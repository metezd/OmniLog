
"""Tests for the OpenAI integration without real API calls."""

import pytest

from app.core import config
from app.integrations import openai_client
from app.integrations.common import ExternalServiceError
from tests.requirements.fake_openai import FakeOpenAI


@pytest.fixture
def fake_client(monkeypatch):
    fake = FakeOpenAI()
    monkeypatch.setattr(openai_client, "_client", fake)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    return fake


def test_embed_texts_returns_vectors(fake_client):
    vectors = openai_client.embed_texts(["Game review", "Movie review"])

    assert len(vectors) == 2
    assert len(vectors[0]) == config.EMBEDDING_DIMENSIONS
    assert len(vectors[1]) == config.EMBEDDING_DIMENSIONS


def test_embed_texts_empty_input(fake_client):
    assert openai_client.embed_texts([]) == []


def test_classify_spoiler_detects_spoiler(fake_client):
    contains_spoiler, score = openai_client.classify_spoiler(
        "In the final chapter the main character dies and it turns out "
        "the narrator was the killer all along."
    )

    assert contains_spoiler is True
    assert score >= config.SPOILER_THRESHOLD


def test_classify_spoiler_rejects_non_spoiler(fake_client):
    contains_spoiler, score = openai_client.classify_spoiler(
        "Great atmosphere and a wonderful soundtrack. Highly recommended."
    )

    assert contains_spoiler is False
    assert score < config.SPOILER_THRESHOLD


def test_missing_api_key_raises_external_service_error(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(openai_client, "_client", None)

    with pytest.raises(ExternalServiceError):
        openai_client.embed_texts(["A review"])


def test_embedding_timeout_raises_external_service_error(
    fake_client, monkeypatch
):
    from openai import APITimeoutError

    def timeout(*args, **kwargs):
        raise APITimeoutError(request=None)

    monkeypatch.setattr(fake_client.embeddings, "create", timeout)

    with pytest.raises(ExternalServiceError):
        openai_client.embed_texts(["A review"])


def test_invalid_spoiler_response_raises_external_service_error(
    fake_client, monkeypatch
):
    from types import SimpleNamespace

    invalid_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"contains_spoiler": "yes", "score": 0.9}'
                )
            )
        ]
    )

    monkeypatch.setattr(
        fake_client.chat.completions,
        "create",
        lambda **kwargs: invalid_response,
    )

    with pytest.raises(ExternalServiceError):
        openai_client.classify_spoiler("A review")


def test_embedding_connection_error_raises_external_service_error(
    fake_client, monkeypatch
):
    from openai import APIConnectionError

    def connection_error(*args, **kwargs):
        raise APIConnectionError(request=None)

    monkeypatch.setattr(
        fake_client.embeddings, "create", connection_error
    )

    with pytest.raises(ExternalServiceError):
        openai_client.embed_texts(["A review"])
