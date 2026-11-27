"""No user request waits for OpenAI (NFR-01, NFR-04, #382).

Before, GET /catalog/{id} made the embedding of a title inside the request, and
POST /library/{id}/review ran the OpenAI spoiler check inside the request. With a slow or broken
OpenAI each of them waited for every try of the client, about 25 seconds with the defaults.

Now both run after the answer in a background job, and after a failure OpenAI is not called again
for OPENAI_COOLDOWN_SECONDS. The fake OpenAI here waits on an event until the answer is back, so
a request that still waited for it would hang until the timeout of the test.
"""
import logging
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APIStatusError

from app.core import background, config
from app.integrations import openai_client
from app.integrations.common import ExternalServiceError
from app.models.entities import Genre, MediaEmbedding, MediaItem, MediaType
from helpers import add_to_library
from tests.requirements.fake_openai import FakeOpenAI

# A request must answer well under the 2 x 8 seconds of one OpenAI try with its retry
FAST_SECONDS = 2.0


class SlowOpenAI:
    """A fake OpenAI that answers only after release(), and counts its calls."""

    def __init__(self):
        self._fake = FakeOpenAI()
        self._released = threading.Event()
        self.calls = []
        self.embeddings = SimpleNamespace(create=self._embeddings)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat))

    def release(self):
        self._released.set()

    def _wait(self, kind):
        self.calls.append(kind)
        assert self._released.wait(timeout=10), "OpenAI was never released"

    def _embeddings(self, **kwargs):
        self._wait("embeddings")
        return self._fake._create_embeddings(**kwargs)

    def _chat(self, **kwargs):
        self._wait("chat")
        return self._fake._create_completion(**kwargs)


@pytest.fixture
def slow_openai(monkeypatch):
    fake = SlowOpenAI()
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_client, "_client", fake)
    yield fake
    fake.release()


def _connection_error(*args, **kwargs):
    raise APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/test"))


@pytest.fixture
def broken_openai(monkeypatch):
    """OpenAI is configured, and every call fails with a connection error. Counts the calls."""
    calls = []

    def broken(*args, **kwargs):
        calls.append(1)
        _connection_error()

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        openai_client,
        "_client",
        SimpleNamespace(
            embeddings=SimpleNamespace(create=broken),
            chat=SimpleNamespace(completions=SimpleNamespace(create=broken)),
        ),
    )
    return calls


@pytest.fixture
def title(db):
    """A title with a description and a genre, so it needs an embedding, and no outside id."""
    genre = db.query(Genre).filter_by(name="Adventure").one_or_none() or Genre(name="Adventure")
    item = MediaItem(title="Slow OpenAI test", media_type=MediaType.GAME, description="A long trip.", genres=[genre])
    db.add(item)
    db.commit()
    return item.id


def _embedding(db, media_id):
    db.expire_all()
    return db.query(MediaEmbedding).filter_by(media_item_id=media_id, model_name=config.EMBEDDING_MODEL).one_or_none()


def _timed(call):
    started = time.monotonic()
    response = call()
    return response, time.monotonic() - started


# ---------------------------------------------------------------- title details
def test_title_details_do_not_wait_for_a_slow_openai(client, auth_headers, db, title, slow_openai):
    response, seconds = _timed(lambda: client.get(f"/catalog/{title}", headers=auth_headers))

    assert response.status_code == 200
    assert seconds < FAST_SECONDS
    assert _embedding(db, title) is None

    slow_openai.release()
    assert background.wait_idle(timeout=10)
    assert slow_openai.calls == ["embeddings"]
    assert _embedding(db, title) is not None


def test_opening_a_title_again_while_its_embedding_runs_adds_no_second_job(client, auth_headers, title, slow_openai):
    for _ in range(5):
        assert client.get(f"/catalog/{title}", headers=auth_headers).status_code == 200

    slow_openai.release()
    assert background.wait_idle(timeout=10)
    assert slow_openai.calls == ["embeddings"]


def test_a_title_with_its_embedding_schedules_nothing(client, auth_headers, db, title, slow_openai):
    client.get(f"/catalog/{title}", headers=auth_headers)
    slow_openai.release()
    background.wait_idle(timeout=10)

    client.get(f"/catalog/{title}", headers=auth_headers)

    assert background.pending() == 0
    assert slow_openai.calls == ["embeddings"]


def test_without_an_openai_key_no_embedding_job_is_added(client, auth_headers, title, monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    added = []
    monkeypatch.setattr(background, "submit_once", lambda *args: added.append(args) or True)

    assert client.get(f"/catalog/{title}", headers=auth_headers).status_code == 200
    assert added == []


def test_title_details_with_openai_down_call_it_once_and_stay_fast(client, auth_headers, title, broken_openai):
    """The case of the issue: a title without an embedding is opened again and again."""
    for _ in range(3):
        response, seconds = _timed(lambda: client.get(f"/catalog/{title}", headers=auth_headers))
        assert response.status_code == 200
        assert seconds < FAST_SECONDS
        assert background.wait_idle(timeout=10)

    # The first job failed and paused OpenAI, so the next jobs did not call it
    assert len(broken_openai) == 1


# ---------------------------------------------------------------- reviews
def test_a_review_does_not_wait_for_a_slow_openai(client, auth_headers, media_item, slow_openai):
    entry = add_to_library(client, auth_headers, media_item["id"])

    response, seconds = _timed(
        lambda: client.post(
            f"/library/{entry['id']}/review", json={"text": "Turns out the friend is the killer."}, headers=auth_headers
        )
    )

    assert response.status_code == 201
    assert seconds < FAST_SECONDS
    assert response.json()["contains_spoiler"] is None  # "not checked yet"

    slow_openai.release()
    assert background.wait_idle(timeout=10)
    review = client.get(f"/library/{entry['id']}/review", headers=auth_headers).json()
    assert review["contains_spoiler"] is True
    assert review["spoiler_model_version"] == config.SPOILER_MODEL


def test_a_review_edited_during_its_check_keeps_only_the_result_of_the_new_text(
    client, auth_headers, media_item, slow_openai
):
    entry = add_to_library(client, auth_headers, media_item["id"])
    url = f"/library/{entry['id']}/review"

    client.post(url, json={"text": "Turns out the friend is the killer."}, headers=auth_headers)
    second = client.post(url, json={"text": "A calm and pretty game."}, headers=auth_headers)
    slow_openai.release()
    assert background.wait_idle(timeout=10)

    assert second.status_code == 200
    assert slow_openai.calls == ["chat", "chat"]
    review = client.get(url, headers=auth_headers).json()
    assert review["text"] == "A calm and pretty game."
    assert review["contains_spoiler"] is False


def test_a_review_with_openai_down_is_fast_and_stays_unchecked(client, auth_headers, media_item, broken_openai):
    entry = add_to_library(client, auth_headers, media_item["id"])

    response, seconds = _timed(
        lambda: client.post(f"/library/{entry['id']}/review", json={"text": "It dies."}, headers=auth_headers)
    )
    assert background.wait_idle(timeout=10)

    assert response.status_code == 201
    assert seconds < FAST_SECONDS
    review = client.get(f"/library/{entry['id']}/review", headers=auth_headers).json()
    assert review["contains_spoiler"] is None
    assert review["spoiler_model_version"] is None


def test_without_an_openai_key_the_local_check_answers_at_once(
    client, auth_headers, media_item, monkeypatch
):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    entry = add_to_library(client, auth_headers, media_item["id"])

    response = client.post(
        f"/library/{entry['id']}/review", json={"text": "In the final chapter the hero dies."}, headers=auth_headers
    )

    assert response.json()["contains_spoiler"] is True
    assert background.pending() == 0


# ---------------------------------------------------------------- the pause after a failure
def test_after_a_failure_openai_is_not_called_until_the_pause_ends(broken_openai, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(openai_client.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(config, "OPENAI_COOLDOWN_SECONDS", 60.0)

    with pytest.raises(ExternalServiceError):
        openai_client.classify_spoiler("first")
    with pytest.raises(ExternalServiceError, match="not called for now"):
        openai_client.embed_texts(["second"])
    assert len(broken_openai) == 1

    clock[0] += 61
    with pytest.raises(ExternalServiceError):
        openai_client.embed_texts(["third"])
    assert len(broken_openai) == 2


def test_a_pause_of_0_seconds_turns_the_pause_off(broken_openai, monkeypatch):
    monkeypatch.setattr(config, "OPENAI_COOLDOWN_SECONDS", 0.0)

    for _ in range(2):
        with pytest.raises(ExternalServiceError):
            openai_client.classify_spoiler("text")

    assert len(broken_openai) == 2


@pytest.mark.parametrize(("status", "pauses"), [(400, False), (401, False), (429, True), (503, True)])
def test_only_failures_that_would_repeat_pause_openai(monkeypatch, status, pauses):
    calls = []

    def failing(*args, **kwargs):
        calls.append(1)
        request = httpx.Request("POST", "https://api.openai.com/v1/test")
        raise APIStatusError("failed", response=httpx.Response(status, request=request), body=None)

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_client, "_client", SimpleNamespace(embeddings=SimpleNamespace(create=failing)))

    for _ in range(2):
        with pytest.raises(ExternalServiceError):
            openai_client.embed_texts(["text"])

    assert len(calls) == (1 if pauses else 2)


# ---------------------------------------------------------------- the job pool
def test_a_failed_job_is_logged_and_the_pool_keeps_working(caplog):
    def boom():
        raise RuntimeError("simulated failure")

    done = []
    with caplog.at_level(logging.ERROR, logger="app.core.background"):
        assert background.submit_once("test:boom", boom)
        assert background.wait_idle(timeout=10)
        assert background.submit_once("test:after", lambda: done.append(1))
        assert background.wait_idle(timeout=10)

    assert done == [1]
    assert "Background job test:boom failed" in caplog.text


def test_a_job_with_the_same_key_is_added_once_while_it_is_pending():
    release = threading.Event()
    runs = []

    def job():
        runs.append(1)
        release.wait(timeout=10)

    assert background.submit_once("test:same", job) is True
    assert background.submit_once("test:same", job) is False
    release.set()
    assert background.wait_idle(timeout=10)
    assert background.submit_once("test:same", lambda: runs.append(2)) is True
    assert background.wait_idle(timeout=10)

    assert runs == [1, 2]
