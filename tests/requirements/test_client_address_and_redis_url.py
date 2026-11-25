"""Client address behind a proxy and an empty REDIS_URL (#251).

The login and register limits count the client address. Behind the proxy of Render it is read
from the right end of X-Forwarded-For, never from the left end, which the client writes.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.deps import client_address
from app.core import cache, config, rate_limit
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"


def request_with(forwarded_for=None, peer="10.9.0.1"):
    """A bare request from `peer` with the given X-Forwarded-For header or headers."""
    values = forwarded_for if isinstance(forwarded_for, list) else [forwarded_for]
    headers = [(b"x-forwarded-for", value.encode()) for value in values if value is not None]
    return Request({"type": "http", "headers": headers, "client": (peer, 50000)})


# ------------------------------------------------------------------------- client address
def test_default_uses_the_address_from_uvicorn(monkeypatch):
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", 0)

    assert client_address(request_with("198.51.100.7, 203.0.113.9")) == "10.9.0.1"


@pytest.mark.parametrize(
    ("hops", "header", "expected"),
    [
        (1, "203.0.113.9", "203.0.113.9"),
        (1, "1.2.3.4, 203.0.113.9", "203.0.113.9"),
        # Render: the browser address, then the address of the frontend
        (2, "203.0.113.9, 10.20.0.5", "203.0.113.9"),
        # The client wrote a fake address at the left end: it is not used
        (2, "1.2.3.4, 203.0.113.9, 10.20.0.5", "203.0.113.9"),
        (2, " 1.2.3.4 ,203.0.113.9 ,  10.20.0.5 ", "203.0.113.9"),
        (2, "2001:db8::1, 10.20.0.5", "2001:db8::1"),
    ],
)
def test_address_is_read_from_the_right_end(monkeypatch, hops, header, expected):
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", hops)

    assert client_address(request_with(header)) == expected


def test_several_headers_count_as_one_list(monkeypatch):
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", 2)

    assert client_address(request_with(["1.2.3.4", "203.0.113.9, 10.20.0.5"])) == "203.0.113.9"


@pytest.mark.parametrize("header", [None, "", " , ", "10.20.0.5", "not-an-address, 10.20.0.5", "203.0.113.9:443, 10.20.0.5"])
def test_short_or_bad_header_falls_back_to_uvicorn(monkeypatch, header):
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", 2)

    assert client_address(request_with(header)) == "10.9.0.1"


def test_no_client_and_no_header_is_unknown(monkeypatch):
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", 2)

    assert client_address(Request({"type": "http", "headers": [], "client": None})) == "unknown"


@pytest.fixture
def login_limit_on(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(config, "REDIS_URL", "")  # count in the process, not in a shared Redis
    monkeypatch.setattr(config, "FORWARDED_TRUSTED_HOPS", 2)
    cache.reset_connection()
    rate_limit.reset()
    yield TestClient(app, client=("10.9.0.2", 50000))
    rate_limit.reset()
    cache.reset_connection()


def login(client, forwarded_for):
    return client.post(
        "/auth/login",
        json={"username": "nobody", "password": "WrongPass123!"},
        headers={"X-Forwarded-For": forwarded_for},
    )


def test_a_fake_left_address_does_not_escape_the_login_limit(login_limit_on):
    """The bypass of penetration finding F1: a new fake first address on every call."""
    statuses = [login(login_limit_on, f"198.51.100.{n}, 203.0.113.20, 10.20.0.5").status_code for n in range(12)]

    assert statuses[:10] == [401] * 10
    assert statuses[10:] == [429, 429]


def test_users_behind_the_same_frontend_do_not_share_a_limit(login_limit_on):
    """The bug of #251: every user came from the address of the frontend."""
    for _ in range(10):
        login(login_limit_on, "203.0.113.30, 10.20.0.5")
    assert login(login_limit_on, "203.0.113.30, 10.20.0.5").status_code == 429

    assert login(login_limit_on, "203.0.113.31, 10.20.0.5").status_code == 401


def _hops_setting(value):
    env = dict(os.environ)
    env.pop("FORWARDED_TRUSTED_HOPS", None)
    if value is not None:
        env["FORWARDED_TRUSTED_HOPS"] = value
    return subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", "from app.core import config; print(config.FORWARDED_TRUSTED_HOPS)"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.parametrize(("value", "expected"), [(None, "0"), ("2", "2")])
def test_hops_setting_is_read(value, expected):
    result = _hops_setting(value)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_negative_hops_stop_the_start():
    result = _hops_setting("-1")

    assert result.returncode != 0
    assert "FORWARDED_TRUSTED_HOPS" in result.stderr


def test_render_sets_two_hops_and_keeps_the_proxy_headers():
    render = (BACKEND_DIR.parent / "render.yaml").read_text()

    assert '--proxy-headers --forwarded-allow-ips="*"' in render
    assert "- key: FORWARDED_TRUSTED_HOPS\n        value: \"2\"" in render


# ------------------------------------------------------------------------------- REDIS_URL
@pytest.fixture
def redis_url(monkeypatch):
    def use(value):
        monkeypatch.setattr(config, "REDIS_URL", value)
        cache.reset_connection()

    yield use
    cache.reset_connection()


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_redis_url_uses_the_in_process_cache(redis_url, value):
    redis_url(value)

    assert cache.redis_client() is None
    assert cache.is_available() is False
    cache.set_json("omni:test:251", {"ok": True}, ttl_seconds=60)
    assert cache.get_json("omni:test:251") == {"ok": True}


def test_a_value_that_is_not_a_redis_address_uses_the_in_process_cache(redis_url):
    redis_url("not-a-redis-url")

    assert cache.redis_client() is None
    cache.set_json("omni:test:251b", [1, 2], ttl_seconds=60)
    assert cache.get_json("omni:test:251b") == [1, 2]


def test_empty_redis_url_still_counts_the_login_limit(login_limit_on):
    for _ in range(10):
        assert login(login_limit_on, "203.0.113.40, 10.20.0.5").status_code == 401
    assert login(login_limit_on, "203.0.113.40, 10.20.0.5").status_code == 429


def test_empty_redis_url_is_kept_empty_by_the_config():
    env = dict(os.environ, REDIS_URL="  ")
    result = subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", "from app.core import config; print(repr(config.REDIS_URL))"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )

    assert result.stdout.strip() == "''"


def test_health_ready_answers_with_an_empty_redis_url(client, redis_url):
    redis_url("")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["cache"] == "down"
