"""Hardening (#220): security headers, the ENABLE_DOCS switch and 401 for tokens without exp or sub."""
import os
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


def test_auth_answers_are_not_cached():
    # Wrong body, so it stops at validation and never needs the database
    response = client.post("/auth/login", json={})

    assert response.headers["Cache-Control"] == "no-store"


def test_other_answers_keep_their_cache_header():
    response = client.get("/health")

    assert response.headers.get("Cache-Control") != "no-store"


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


def test_docs_are_on_by_default():
    assert _docs_status(None) == ["200", "200", "200"]


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "False"])
def test_docs_can_be_turned_off(value):
    assert _docs_status(value) == ["404", "404", "404"]
