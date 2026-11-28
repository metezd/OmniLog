"""Health endpoints (US-01): /health says the process is alive, /health/ready checks the database and Redis."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

# Make `import app...` work when pytest is started from the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core import cache  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _client_with_db(execute_error=None):
    """A test client whose database session works, or fails when execute_error is given."""
    db = MagicMock()
    if execute_error is not None:
        db.execute.side_effect = execute_error

    def fake_get_db():
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    return TestClient(app), db


@pytest.fixture(autouse=True)
def clean_overrides():
    yield
    app.dependency_overrides.pop(get_db, None)


def test_health_answers_even_when_the_database_is_down():
    client, _ = _client_with_db(OperationalError("SELECT 1", {}, Exception("db is down")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_when_database_and_redis_work(monkeypatch):
    monkeypatch.setattr(cache, "is_available", lambda: True)
    client, db = _client_with_db()

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok", "cache": "ok"}
    db.execute.assert_called_once()


def test_not_ready_when_the_database_is_down(monkeypatch):
    monkeypatch.setattr(cache, "is_available", lambda: True)
    client, _ = _client_with_db(OperationalError("SELECT 1", {}, Exception("password=hunter2 refused")))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down", "cache": "ok"}
    assert "hunter2" not in response.text  # no error details in the answer


def test_redis_down_is_not_fatal(monkeypatch):
    monkeypatch.setattr(cache, "status", lambda: "down")
    client, _ = _client_with_db()

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok", "cache": "down"}


class _FakeRedis:
    def __init__(self, error=None):
        self.error = error

    def ping(self):
        if self.error:
            raise self.error
        return True


def test_cache_is_available_when_redis_answers(monkeypatch):
    monkeypatch.setattr(cache, "_redis", lambda: _FakeRedis())

    assert cache.is_available() is True


def test_cache_is_not_available_when_redis_is_in_its_wait_time(monkeypatch):
    monkeypatch.setattr(cache, "_redis", lambda: None)

    assert cache.is_available() is False


def test_cache_is_not_available_and_waits_when_ping_fails(monkeypatch):
    monkeypatch.setattr(cache, "_redis", lambda: _FakeRedis(redis.ConnectionError("down")))
    marked = []
    monkeypatch.setattr(cache, "_mark_redis_down", marked.append)

    assert cache.is_available() is False
    assert len(marked) == 1


# ---------------------------------------------------------------- the state of Redis (#422)
@pytest.mark.parametrize(
    ("url", "answers", "expected"),
    [
        ("", True, "not_configured"),
        ("   ", True, "not_configured"),
        ("redis://cache.internal:6379/0", True, "ok"),
        ("redis://cache.internal:6379/0", False, "down"),
    ],
)
def test_cache_status_tells_a_missing_setting_from_a_redis_that_does_not_answer(monkeypatch, url, answers, expected):
    from app.core import config

    monkeypatch.setattr(config, "REDIS_URL", url)
    monkeypatch.setattr(cache, "is_available", lambda: answers)

    assert cache.status() == expected


@pytest.mark.parametrize(
    ("url", "target"),
    [
        ("redis://default:s3cret@red-abc:6379/0", "red-abc:6379"),
        ("rediss://user:pw@host.upstash.io:6380", "host.upstash.io:6380"),
        ("redis://localhost", "localhost:6379"),
        ("", ""),
    ],
)
def test_the_log_target_never_holds_the_password(monkeypatch, url, target):
    from app.core import config

    monkeypatch.setattr(config, "REDIS_URL", url)

    assert cache.redis_target() == target
    assert "s3cret" not in cache.redis_target()


@pytest.mark.parametrize(
    ("state", "message"),
    [("not_configured", "REDIS_URL is empty"), ("down", "does not answer"), ("ok", None)],
)
def test_the_start_says_why_the_cache_is_not_redis(monkeypatch, caplog, state, message):
    import logging

    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(cache, "status", lambda: state)
    monkeypatch.setattr(cache, "redis_target", lambda: "red-abc:6379")
    with caplog.at_level(logging.WARNING, logger="app.main"), TestClient(app):
        pass

    if message is None:
        assert "Redis" not in caplog.text and "REDIS_URL" not in caplog.text
    else:
        assert message in caplog.text

