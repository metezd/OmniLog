"""The connection pool replaces dropped connections and has settings (#392).

Before, the engine used the defaults of SQLAlchemy: a connection that the database had closed (a
restart, maintenance, the idle timeout of a managed database) stayed in the pool, and the next
request that got it failed with OperationalError and 500.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.core import config, database
from app.core.database import get_db, make_engine
from app.main import app


def _terminate(engine_with_one_connection):
    """Let the database drop the connection that is now idle in the pool of the engine."""
    with engine_with_one_connection.connect() as connection:
        pid = connection.execute(text("SELECT pg_backend_pid()")).scalar_one()
    with make_engine(statement_timeout_ms=0).begin() as killer:
        assert killer.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid}).scalar_one()


# ---------------------------------------------------------------- dropped connections
def test_a_dropped_connection_is_replaced_without_an_error():
    engine = make_engine()
    _terminate(engine)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    engine.dispose()


def test_the_engine_of_the_api_checks_connections_before_use():
    _terminate(database.engine)

    with database.engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_a_request_after_a_dropped_connection_answers(client, auth_headers):
    _terminate(database.engine)

    assert client.get("/library", headers=auth_headers).status_code == 200


# ---------------------------------------------------------------- the settings
def test_the_pool_uses_the_settings():
    pool = database.engine.pool

    assert database.engine.pool._pre_ping is True
    assert pool.size() == config.DB_POOL_SIZE
    assert pool._max_overflow == config.DB_MAX_OVERFLOW
    assert pool._timeout == config.DB_POOL_TIMEOUT
    assert pool._recycle == config.DB_POOL_RECYCLE


def test_the_defaults():
    assert (config.DB_POOL_SIZE, config.DB_MAX_OVERFLOW, config.DB_POOL_TIMEOUT) == (5, 10, 10)
    assert config.DB_POOL_RECYCLE == 1800
    assert config.DB_STATEMENT_TIMEOUT_MS == 15000


@pytest.mark.parametrize(("name", "text_value"), [("DB_POOL_SIZE", "0"), ("DB_POOL_TIMEOUT", "ten"), ("DB_MAX_OVERFLOW", "-1")])
def test_a_wrong_pool_setting_stops_the_start(monkeypatch, name, text_value):
    monkeypatch.setenv(name, text_value)
    minimum = 0 if name == "DB_MAX_OVERFLOW" else 1

    with pytest.raises(RuntimeError, match=name):
        config._whole_number(name, 5, minimum)


# ---------------------------------------------------------------- statement timeout
def test_the_api_has_a_statement_timeout():
    with database.engine.connect() as connection:
        # pg_settings gives the value in milliseconds, SHOW would round it to "15s"
        setting = connection.execute(text("SELECT setting FROM pg_settings WHERE name = 'statement_timeout'")).scalar_one()
    assert int(setting) == config.DB_STATEMENT_TIMEOUT_MS


def test_a_statement_over_the_timeout_is_stopped():
    engine = make_engine(statement_timeout_ms=100)
    with pytest.raises(OperationalError, match="statement timeout"):
        with engine.connect() as connection:
            connection.execute(text("SELECT pg_sleep(2)"))
    engine.dispose()


def test_the_migrations_have_no_statement_timeout():
    engine = make_engine(statement_timeout_ms=0)
    with engine.connect() as connection:
        assert connection.execute(text("SHOW statement_timeout")).scalar_one() == "0"
    engine.dispose()


def test_the_migrations_use_an_engine_without_the_timeout():
    source = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "env.py"

    assert "make_engine(statement_timeout_ms=0)" in source.read_text(encoding="utf-8")


# ---------------------------------------------------------------- 503 instead of 500
@pytest.mark.parametrize(
    "error",
    [
        PoolTimeoutError("QueuePool limit of size 5 overflow 10 reached"),
        OperationalError("SELECT 1", {}, Exception("could not connect to server at db.internal:5432")),
    ],
)
def test_a_busy_or_unreachable_database_answers_503(auth_headers, error):
    def broken_db():
        raise error
        yield  # pragma: no cover - makes this a generator like get_db

    app.dependency_overrides[get_db] = broken_db
    try:
        response = TestClient(app, raise_server_exceptions=False).get("/stats", headers=auth_headers)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json() == {"detail": "The database is busy or unavailable. Please try again."}
    assert "db.internal" not in response.text
    assert response.headers["X-Content-Type-Options"] == "nosniff"
