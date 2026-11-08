"""Non-functional requirement tests (NFR-01 to NFR-04).

NFR-05 (code coverage) is measured in the Testing phase with:
    pytest --cov=backend/app
"""
import time

import pytest

from helpers import new_credentials


def test_nfr01_cached_search_p95_under_500ms(client, auth_headers):
    """NFR-01: 95th percentile of repeated catalog searches is under 500 ms."""
    params = {"q": "Life is Strange", "type": "GAME"}
    warmup = client.get("/catalog/search", params=params, headers=auth_headers)
    assert warmup.status_code == 200  # fills the cache

    durations = []
    for _ in range(100):
        start = time.perf_counter()
        response = client.get("/catalog/search", params=params, headers=auth_headers)
        durations.append(time.perf_counter() - start)
        assert response.status_code == 200

    durations.sort()
    p95 = durations[94]
    assert p95 < 0.5, f"p95 was {p95:.3f}s"


@pytest.mark.parametrize(
    "path",
    [
        "/library",
        "/lists",
        "/diary",
        "/stats",
    ],
)
def test_nfr02_protected_endpoints_require_token(client, path):
    """NFR-02: protected endpoints return 401 without a valid token."""
    response = client.get(path)

    assert response.status_code == 401


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


def test_nfr04_survives_external_api_failure(auth_headers, monkeypatch):
    """NFR-04: when IGDB/TMDB is down the API returns cached data or 503, not 500."""
    import requests
    from fastapi.testclient import TestClient
    from app.main import app

    def broken_request(*args, **kwargs):
        raise requests.exceptions.ConnectionError("external API unavailable")

    monkeypatch.setattr(requests.sessions.Session, "request", broken_request)
    lenient_client = TestClient(app, raise_server_exceptions=False)

    response = lenient_client.get(
        "/catalog/search",
        params={"q": "uncached-query-for-failure-test", "type": "GAME"},
        headers=auth_headers,
    )

    assert response.status_code in (200, 503)
