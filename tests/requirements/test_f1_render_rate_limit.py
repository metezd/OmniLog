"""F1 of the penetration test: the login limit on the Render setup (#301, US-03, NFR-02).

The app runs here behind uvicorn's ProxyHeadersMiddleware with `trusted_hosts="*"`, the same as
`--proxy-headers --forwarded-allow-ips="*"` in render.yaml, and with the FORWARDED_TRUSTED_HOPS
value of render.yaml. The proxy of Render adds the address of the caller at the right end of
X-Forwarded-For. Everything to the left of it is written by the caller.

Calls through the frontend carry the browser address in X-Client-IP, which the backend uses only
together with the right X-Frontend-Key.
"""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core import cache, config, rate_limit
from app.main import app

RENDER_YAML = Path(__file__).resolve().parents[2] / "render.yaml"
SECRET = "frontend-proxy-secret-for-tests-0123456789"  # noqa: S105  # gitleaks:allow (test value, not a real key)
ATTACKER = "203.0.113.50"  # the address that the proxy of Render sees
FRONTEND = "10.20.0.5"  # the address of the frontend service


class FrozenClock:
    """All calls in one window of the limit, see test_client_address_and_redis_url.py."""

    @staticmethod
    def time() -> float:
        return 1_800_000_000.0


def render_hops() -> int:
    match = re.search(r'- key: FORWARDED_TRUSTED_HOPS\n\s+value: "(\d+)"', RENDER_YAML.read_text(encoding="utf-8"))
    assert match, "render.yaml does not set FORWARDED_TRUSTED_HOPS"
    return int(match.group(1))


@pytest.fixture
def render_api(monkeypatch):
    """The API with the settings of render.yaml and the login limit on."""
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(config, "REDIS_URL", "")
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", render_hops())
    monkeypatch.setattr(config, "FRONTEND_PROXY_SECRET", SECRET, raising=False)
    monkeypatch.setattr(rate_limit, "time", FrozenClock)
    cache.reset_connection()
    rate_limit.reset()
    # The proxy of Render connects from an address of its own network
    yield TestClient(ProxyHeadersMiddleware(app, trusted_hosts="*"), client=("10.0.0.1", 50000))
    rate_limit.reset()
    cache.reset_connection()


def login(client, headers):
    return client.post("/auth/login", json={"username": "nobody", "password": "WrongPass123!"}, headers=headers)


def test_f1_us03_thirty_fake_forwarded_addresses_are_limited(render_api):
    """The proof of F1: a new fake first address on every call. It must not reset the limit."""
    statuses = [
        login(render_api, {"X-Forwarded-For": f"198.51.100.{n}, {ATTACKER}"}).status_code for n in range(30)
    ]

    assert statuses[:10] == [401] * 10
    assert set(statuses[10:]) == {429}


def test_f1_us03_a_forged_client_ip_without_the_key_is_ignored(render_api):
    statuses = [
        login(render_api, {"X-Forwarded-For": ATTACKER, "X-Client-IP": f"198.51.100.{n}"}).status_code
        for n in range(12)
    ]

    assert 429 in statuses


def test_f1_us03_a_forged_client_ip_with_a_wrong_key_is_ignored(render_api):
    headers = {"X-Forwarded-For": ATTACKER, "X-Frontend-Key": "guessed-key"}
    statuses = [login(render_api, headers | {"X-Client-IP": f"198.51.100.{n}"}).status_code for n in range(12)]

    assert 429 in statuses


def test_f1_us03_users_behind_the_frontend_have_their_own_limit(render_api):
    """The bug of #251: with the key, the frontend tells the backend the browser address."""
    via_frontend = {"X-Forwarded-For": f"198.51.100.1, {FRONTEND}", "X-Frontend-Key": SECRET}
    for _ in range(10):
        login(render_api, via_frontend | {"X-Client-IP": "192.0.2.10"})
    assert login(render_api, via_frontend | {"X-Client-IP": "192.0.2.10"}).status_code == 429

    assert login(render_api, via_frontend | {"X-Client-IP": "192.0.2.11"}).status_code == 401


def test_f1_us03_a_broken_client_ip_falls_back_to_the_proxy_address(render_api):
    headers = {"X-Forwarded-For": f"198.51.100.1, {FRONTEND}", "X-Frontend-Key": SECRET, "X-Client-IP": "not-an-ip"}
    for _ in range(10):
        login(render_api, headers)

    assert login(render_api, headers).status_code == 429


def test_f1_short_frontend_proxy_secret_stops_the_start(monkeypatch):
    """A short key could be guessed, so the backend refuses to start with one."""
    import importlib

    monkeypatch.setenv("FRONTEND_PROXY_SECRET", "too-short")
    try:
        with pytest.raises(RuntimeError, match="FRONTEND_PROXY_SECRET"):
            importlib.reload(config)
    finally:
        monkeypatch.undo()
        importlib.reload(config)
