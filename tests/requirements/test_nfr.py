"""Non-functional requirement tests (NFR-01 to NFR-04).

The coverage requirement is checked in tests/test_coverage_gate.py, and the number is measured in
CI (docs/tests/coverage.md).
"""
import time
from types import SimpleNamespace

import pytest

from helpers import add_to_library, create_media, new_credentials


# ---------------------------------------------------------------- NFR-01
def _p95_of_repeated_gets(client, path, headers, params=None, runs=100):
    """Call GET `path` `runs` times and return the 95th percentile duration in seconds."""
    durations = []
    for _ in range(runs):
        start = time.perf_counter()
        response = client.get(path, params=params, headers=headers)
        durations.append(time.perf_counter() - start)
        assert response.status_code == 200

    durations.sort()
    p95 = durations[int(runs * 0.95) - 1]
    # Shown with `pytest -s`. Copy this line into the Testing Report.
    print(f"\n[NFR-01] GET {path}: p95={p95 * 1000:.1f} ms over {runs} requests")
    return p95


def test_nfr01_cached_search_p95_under_500ms(client, auth_headers):
    """NFR-01: 95th percentile of repeated catalog searches is under 500 ms."""
    params = {"q": "Life is Strange", "type": "GAME"}
    warmup = client.get("/catalog/search", params=params, headers=auth_headers)
    assert warmup.status_code == 200  # fills the cache

    p95 = _p95_of_repeated_gets(client, "/catalog/search", auth_headers, params)

    assert p95 < 0.5, f"p95 was {p95:.3f}s"


def test_nfr01_cached_stats_p95_under_500ms(client, auth_headers):
    """NFR-01: 95th percentile of repeated /stats requests is under 500 ms."""
    game = create_media(client, auth_headers, media_type="GAME")
    add_to_library(client, auth_headers, game["id"], status="COMPLETED", rating=8)
    warmup = client.get("/stats", headers=auth_headers)
    assert warmup.status_code == 200  # fills the cache, if the endpoint has one

    p95 = _p95_of_repeated_gets(client, "/stats", auth_headers)

    assert p95 < 0.5, f"p95 was {p95:.3f}s"


# ---------------------------------------------------------------- NFR-02
@pytest.mark.parametrize(
    ("method", "path"),
    [
        # Library (US-04, US-05, removal)
        ("POST", "/library"),
        ("GET", "/library"),
        ("PATCH", "/library/1"),
        ("DELETE", "/library/1"),
        # Reviews (US-14)
        ("POST", "/library/1/review"),
        ("GET", "/library/1/review"),
        # Episodic logging (US-10, US-11, US-12)
        ("PUT", "/library/1/chapters/1/rating"),
        ("POST", "/library/1/chapters/1/playtime"),
        ("PUT", "/library/1/chapters/1/decision"),
        ("GET", "/library/1/chapters/1"),
        # Custom lists and diary (US-06, US-07)
        ("POST", "/lists"),
        ("GET", "/lists"),
        ("GET", "/lists/1"),
        ("POST", "/lists/1/items"),
        ("DELETE", "/lists/1/items/1"),
        ("DELETE", "/lists/1"),
        ("GET", "/diary"),
        # Catalog (US-08, US-09)
        ("GET", "/catalog/search"),
        ("GET", "/catalog/1"),
        # Recommendations (US-13)
        ("GET", "/recommendations"),
        # Statistics (US-15)
        ("GET", "/stats"),
        # Media (internal)
        ("POST", "/media"),
        ("GET", "/media/1"),
    ],
)
def test_nfr02_protected_endpoints_require_token(client, method, path):
    """NFR-02: protected endpoints return 401 without a valid token."""
    # Provide minimal valid-shaped bodies so the auth check is reached before
    # validation rejects the request with 422.
    body_by_path = {
        "/library": {"media_item_id": 1},
        "/library/1/review": {"text": "Great game."},
        "/library/1/chapters/1/rating": {"rating": 3},
        "/library/1/chapters/1/playtime": {"minutes": 30},
        "/library/1/chapters/1/decision": {"choice": "A"},
        "/lists": {"name": "My list"},
        "/lists/1/items": {"media_item_id": 1},
        "/media": {"title": "Test", "media_type": "GAME"},
    }
    kwargs = {"json": body_by_path[path]} if path in body_by_path else {}

    response = client.request(method, path, **kwargs)

    assert response.status_code == 401


# ---------------------------------------------------------------- NFR-03
def test_nfr03_password_is_hashed_and_never_returned(client):
    """NFR-03: stored password differs from plain text and is never returned."""
    credentials = new_credentials()
    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 201
    assert credentials["password"] not in response.text
    assert "hashed_password" not in response.text

    # Check what is actually stored in the database.
    from app.core.database import SessionLocal
    from app.models.entities import User

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == credentials["username"]).one()
        assert user.hashed_password != credentials["password"]
        assert len(user.hashed_password) > len(credentials["password"])


# ---------------------------------------------------------------- NFR-04
@pytest.fixture
def lenient_client():
    """A client that returns a real 500 response instead of raising the server error."""
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def openai_down(monkeypatch):
    """OpenAI is configured, but every call to it fails with a connection error."""
    import httpx
    from openai import APIConnectionError
    from app.core import config
    from app.integrations import openai_client

    def broken(*args, **kwargs):
        raise APIConnectionError(
            request=httpx.Request("POST", "https://api.openai.com/v1/test")
        )

    broken_client = SimpleNamespace(
        embeddings=SimpleNamespace(create=broken),
        chat=SimpleNamespace(completions=SimpleNamespace(create=broken)),
    )
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_client, "_client", broken_client)


def test_nfr04_survives_external_api_failure(auth_headers, monkeypatch):
    """NFR-04: when IGDB/TMDB is down the API returns cached data or 503, not 500."""
    import requests
    from fastapi.testclient import TestClient
    from app.main import app

    def broken_request(*args, **kwargs):
        raise requests.exceptions.ConnectionError("external API unavailable")

    monkeypatch.setattr(requests.sessions.Session, "request", broken_request)
    lenient = TestClient(app, raise_server_exceptions=False)

    response = lenient.get(
        "/catalog/search",
        params={"q": "uncached-query-for-failure-test", "type": "GAME"},
        headers=auth_headers,
    )

    assert response.status_code in (200, 503)


def test_nfr04_recommendations_survive_openai_down(
    openai_down, lenient_client, auth_headers
):
    """NFR-04: /recommendations answers 200 or 503 when OpenAI is down, never 500."""
    response = lenient_client.get(
        "/recommendations", params={"target": "SERIES"}, headers=auth_headers
    )

    assert response.status_code in (200, 503)


def test_nfr04_review_survives_openai_down_and_is_saved(
    openai_down, lenient_client, auth_headers, library_entry
):
    """NFR-04: a review gets 201 when OpenAI is down (never 503 or 500) and is still saved.

    The spoiler fields stay NULL: the review was not checked (US-14, #152, #155).
    """
    text = "In the final chapter the main character dies."

    response = lenient_client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": text},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["contains_spoiler"] is None
    assert response.json()["spoiler_score"] is None
    assert response.json()["spoiler_model_version"] is None
    saved = lenient_client.get(
        f"/library/{library_entry['id']}/review", headers=auth_headers
    )
    assert saved.status_code == 200
    assert saved.json() is not None, "the review was not saved"
    assert saved.json()["text"] == text