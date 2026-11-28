"""Hardening (#220): security headers, the ENABLE_DOCS switch and 401 for tokens without exp or sub."""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import SECRET_KEY  # noqa: E402
from app.core.security import JWT_ALGORITHM  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


# Security headers

def test_security_headers_on_every_answer():
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_security_headers_on_errors_too():
    response = client.get("/this-path-does-not-exist")

    assert response.status_code == 404
    assert response.headers["X-Content-Type-Options"] == "nosniff"



# ---------------------------------------------------------------- F7 and the missing headers (#304)
API_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}
ROOT = BACKEND_DIR.parent


@pytest.fixture
def tolerant():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _answer(tolerant, kind, monkeypatch):
    """One answer of each status that the issue names."""
    if kind == 200:
        return tolerant.get("/health")
    if kind == 404:
        return tolerant.get("/no-such-path")
    if kind == 422:
        return tolerant.post("/auth/login", json={})
    if kind == 429:
        from fastapi import HTTPException

        from app.core import rate_limit

        def always_limited(name, identity):
            raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "1"})

        monkeypatch.setattr(rate_limit, "check", always_limited)
        return tolerant.post("/auth/login", json={"username": "x", "password": "y"})
    if kind == 500:
        from app.core import database

        def broken_session():
            raise RuntimeError("database is gone")
            yield  # pragma: no cover

        app.dependency_overrides[database.get_db] = broken_session
        try:
            return tolerant.post("/auth/login", json={"username": "x", "password": "y"})
        finally:
            app.dependency_overrides.pop(database.get_db, None)
    raise AssertionError(kind)


@pytest.mark.parametrize("kind", [200, 404, 422, 429, 500])
def test_f7_the_api_headers_are_on_every_status(tolerant, monkeypatch, kind):
    response = _answer(tolerant, kind, monkeypatch)

    assert response.status_code == kind
    for name, value in API_HEADERS.items():
        assert response.headers.get(name) == value, f"{name} on {kind}"


def test_f7_a_500_does_not_show_the_error():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = _answer(test_client, 500, None)

    assert response.json() == {"detail": "Internal Server Error"}
    assert "database is gone" not in response.text


@pytest.mark.parametrize("path", ["backend/Dockerfile", "render.yaml"])
def test_f7_uvicorn_does_not_name_itself(path):
    text = (ROOT / path).read_text(encoding="utf-8")

    assert "--no-server-header" in text


def test_f7_caddy_removes_the_server_header_and_adds_the_browser_headers():
    caddyfile = (ROOT / "docker/Caddyfile").read_text(encoding="utf-8")

    for rule in ("-Server", "Strict-Transport-Security", "X-Content-Type-Options", "Referrer-Policy",
                 "Permissions-Policy", "X-Frame-Options"):
        assert rule in caddyfile, rule
    assert re.search(r"Strict-Transport-Security\s+\"max-age=\d+", caddyfile)


def test_caddy_sends_one_hsts_header_of_one_year_for_both_sites():
    """#425: the same value as the API and the frontend, and the HSTS of the frontend and of the
    API is dropped behind Caddy, so the browser never gets two."""
    caddyfile = (ROOT / "docker/Caddyfile").read_text(encoding="utf-8")

    assert 'Strict-Transport-Security "max-age=31536000"' in caddyfile
    assert caddyfile.count("header_down -Strict-Transport-Security") == 2

def test_auth_answers_are_not_cached():
    # Wrong body, so it stops at validation and never needs the database
    response = client.post("/auth/login", json={})

    assert response.headers["Cache-Control"] == "no-store"


def test_other_answers_are_not_cached_either():
    # #394: no-store is the default, an endpoint can set its own (the catalog, see
    # tests/requirements/test_http_defaults.py)
    response = client.get("/health")

    assert response.headers["Cache-Control"] == "no-store"


# 401 for tokens that miss a claim

def _token(payload):
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest.mark.parametrize(
    "payload",
    [
        {"sub": "1"},
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
    ],
    ids=["no-exp", "no-sub"],
)
def test_token_without_required_claim_gives_401(payload):
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {_token(payload)}"})

    assert response.status_code == 401


# ENABLE_DOCS

def _docs_status(enable_docs):
    """Start a fresh interpreter, because ENABLE_DOCS is read when the app is imported."""
    env = dict(os.environ)
    if enable_docs is None:
        env.pop("ENABLE_DOCS", None)
    else:
        env["ENABLE_DOCS"] = enable_docs
    code = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "c = TestClient(app)\n"
        "print(c.get('/docs').status_code, c.get('/redoc').status_code,"
        " c.get('/openapi.json').status_code)\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return result.stdout.split()


def test_docs_are_off_by_default():
    # #394: a start without the setting (uvicorn on a server) must not show every endpoint
    assert _docs_status(None) == ["404", "404", "404"]


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "False", ""])
def test_docs_can_be_turned_off(value):
    assert _docs_status(value) == ["404", "404", "404"]


@pytest.mark.parametrize("value", ["true", "1", "yes", "on", "True"])
def test_docs_can_be_turned_on_for_development(value):
    assert _docs_status(value) == ["200", "200", "200"]


def test_env_example_turns_the_docs_on_for_development():
    example = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")

    assert re.search(r"^ENABLE_DOCS=true$", example, re.MULTILINE)


@pytest.mark.parametrize("config_file", ["render.yaml", "docker-compose.prod.yml"])
def test_docs_are_off_in_every_production_config(config_file):
    config = (BACKEND_DIR.parent / config_file).read_text(encoding="utf-8")

    assert re.search(r'ENABLE_DOCS(:\s*\$\{ENABLE_DOCS:-false\}|\s+value:\s*"false")', config)
