"""IGDB and TMDB calls hold no database connection, and a failing host is paused (#428, NFR-04).

Before, the title details and the search called IGDB or TMDB while the request held a pool
connection (get_current_user had already read the user), and a title that was never loaded called
the failing service again on every open. With the real client that is up to about 35 seconds each.
"""
import pytest
import requests
from fastapi.testclient import TestClient

from app.core import config
from app.core.database import SessionLocal, engine
from app.integrations import common
from app.integrations.common import ExternalServiceError
from app.main import app
from app.models.entities import MediaItem, MediaType


def _movie(external_id=80001):
    """A movie that was never loaded: it has an outside id and no saved details. The fake TMDB knows
    only this id, and (media type, id) is unique, so an earlier test may have saved it already."""
    db = SessionLocal()
    try:
        item = (
            db.query(MediaItem)
            .filter_by(media_type=MediaType.MOVIE, external_api_id=external_id)
            .one_or_none()
        )
        if item is None:
            item = MediaItem(title="Blade Runner", media_type=MediaType.MOVIE, external_api_id=external_id)
            db.add(item)
        item.description = None
        item.last_synced = None
        db.commit()
        return item.id
    finally:
        db.close()


@pytest.fixture
def tmdb_on(monkeypatch):
    monkeypatch.setattr(config, "TMDB_API_KEY", "test-tmdb-key")


@pytest.fixture
def checked_out_during_calls(monkeypatch, fake_external_apis):
    """Record how many pool connections are checked out while each outside call runs."""
    seen = []
    original = fake_external_apis.request

    def request(_session, method, url, **kwargs):
        seen.append(engine.pool.checkedout())
        return original(method, url, **kwargs)

    monkeypatch.setattr(requests.sessions.Session, "request", request)
    return seen


# ---------------------------------------------------------------- no connection during the call
def test_title_details_hold_no_connection_during_the_tmdb_call(
    client, auth_headers, tmdb_on, checked_out_during_calls
):
    response = client.get(f"/catalog/{_movie()}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["description"] == "A blade runner hunts replicants."
    assert checked_out_during_calls == [0]


def test_search_holds_no_connection_during_the_tmdb_call(
    client, auth_headers, tmdb_on, checked_out_during_calls
):
    response = client.get("/catalog/search", params={"q": "blade", "type": "MOVIE"}, headers=auth_headers)

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Blade Runner"]
    assert checked_out_during_calls == [0]


# ---------------------------------------------------------------- a failing host is paused
def test_a_failing_tmdb_is_called_once_for_three_opens(client, auth_headers, tmdb_on, fake_external_apis):
    """The case of the issue: three opens of a title that was never loaded while TMDB is down."""
    fake_external_apis.fail("tmdb", exception=requests.exceptions.ConnectTimeout("no answer"), times=None)
    media_id = _movie()

    for _ in range(3):
        assert client.get(f"/catalog/{media_id}", headers=auth_headers).status_code == 200

    tries = config.EXTERNAL_API_MAX_RETRIES + 1
    assert fake_external_apis.count("tmdb") == tries  # the tries of the first open only


def test_the_pause_ends_after_the_cooldown(tmdb_on, fake_external_apis, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(common.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(config, "EXTERNAL_API_COOLDOWN_SECONDS", 60.0)
    fake_external_apis.fail("tmdb", exception=requests.exceptions.ConnectTimeout("no answer"), times=None)
    session = requests.Session()

    with pytest.raises(ExternalServiceError):
        common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/1", source="TMDB")
    calls = fake_external_apis.count("tmdb")
    with pytest.raises(ExternalServiceError, match="not called for now"):
        common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/2", source="TMDB")
    assert fake_external_apis.count("tmdb") == calls

    clock[0] += 61
    with pytest.raises(ExternalServiceError):
        common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/3", source="TMDB")
    assert fake_external_apis.count("tmdb") > calls


def test_a_pause_of_one_host_does_not_stop_another(tmdb_on, fake_external_apis):
    fake_external_apis.fail("tmdb", exception=requests.exceptions.ConnectTimeout("no answer"), times=None)
    session = requests.Session()
    with pytest.raises(ExternalServiceError):
        common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/1", source="TMDB")

    response = common.request_with_retry(
        session, "POST", "https://id.twitch.tv/oauth2/token", source="IGDB",
        data={"client_id": "x", "client_secret": "y", "grant_type": "client_credentials"},
    )

    assert response is not None


@pytest.mark.parametrize("status", [404, 429, 503])
def test_an_answer_does_not_pause_the_host(tmdb_on, fake_external_apis, status):
    """A 404, a 429 or a 503 comes back at once, so the next call still goes out (#250 retries)."""
    tries = config.EXTERNAL_API_MAX_RETRIES + 1
    fake_external_apis.fail("tmdb", status=status, times=tries)
    session = requests.Session()
    try:
        common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/1", source="TMDB")
    except ExternalServiceError:
        pass
    calls = fake_external_apis.count("tmdb")

    common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/80001", source="TMDB")

    assert fake_external_apis.count("tmdb") == calls + 1


def test_a_cooldown_of_0_turns_the_pause_off(tmdb_on, fake_external_apis, monkeypatch):
    monkeypatch.setattr(config, "EXTERNAL_API_COOLDOWN_SECONDS", 0.0)
    fake_external_apis.fail("tmdb", exception=requests.exceptions.ConnectTimeout("no answer"), times=None)
    session = requests.Session()

    for _ in range(2):
        with pytest.raises(ExternalServiceError):
            common.request_with_retry(session, "GET", "https://api.themoviedb.org/3/movie/1", source="TMDB")

    assert fake_external_apis.count("tmdb") == 2 * (config.EXTERNAL_API_MAX_RETRIES + 1)


def test_the_default_cooldown_is_60_seconds():
    assert config.EXTERNAL_API_COOLDOWN_SECONDS == 60.0


def test_a_lenient_client_never_sees_a_500_while_tmdb_is_down(auth_headers, tmdb_on, fake_external_apis):
    fake_external_apis.fail("tmdb", exception=requests.exceptions.ConnectTimeout("no answer"), times=None)
    lenient = TestClient(app, raise_server_exceptions=False)

    assert lenient.get(f"/catalog/{_movie()}", headers=auth_headers).status_code == 200
    assert lenient.get("/catalog/search", params={"q": "nothing saved", "type": "MOVIE"}, headers=auth_headers).status_code == 503
