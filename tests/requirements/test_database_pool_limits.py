"""The connection pool has settings, a statement timeout, and a full pool answers 503 (#432).

Before, the pool used the defaults of SQLAlchemy (5 + 10 connections, a wait of 30 seconds), a
request that found no free connection got 500 after 30 seconds, and a slow query had no limit.
"""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core import config, database
from app.core.database import DATABASE_URL, engine, engine_options, set_statement_timeout
from app.main import app

ENV_PY = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "env.py"


def _setting(connection) -> int:
    # pg_settings gives milliseconds, SHOW would round 15000 to "15s"
    return int(connection.execute(text("SELECT setting FROM pg_settings WHERE name = 'statement_timeout'")).scalar_one())


def test_the_pool_uses_the_settings():
    assert engine.pool.size() == config.DB_POOL_SIZE
    assert engine.pool._max_overflow == config.DB_MAX_OVERFLOW
    assert engine.pool._timeout == config.DB_POOL_TIMEOUT
    assert engine.pool._pre_ping is True


def test_the_defaults():
    assert (config.DB_POOL_SIZE, config.DB_MAX_OVERFLOW, config.DB_POOL_TIMEOUT) == (5, 10, 10)
    assert config.DB_STATEMENT_TIMEOUT_MS == 15000


@pytest.mark.parametrize(("value", "minimum"), [("0", 1), ("ten", 1), ("-1", 0)])
def test_a_wrong_pool_setting_stops_the_start(monkeypatch, value, minimum):
    monkeypatch.setenv("DB_TEST_SETTING", value)

    with pytest.raises(RuntimeError, match="DB_TEST_SETTING"):
        config._whole_number("DB_TEST_SETTING", 5, minimum)


def test_the_api_connections_have_the_statement_timeout():
    with engine.connect() as connection:
        assert _setting(connection) == config.DB_STATEMENT_TIMEOUT_MS


def test_a_statement_over_the_timeout_is_stopped():
    short = create_engine(DATABASE_URL, **engine_options(DATABASE_URL))
    set_statement_timeout(short, 100)
    try:
        with pytest.raises(OperationalError, match="statement timeout"):
            with short.connect() as connection:
                connection.execute(text("SELECT pg_sleep(2)"))
    finally:
        short.dispose()


def test_a_timeout_of_0_sets_nothing():
    plain = create_engine(DATABASE_URL, **engine_options(DATABASE_URL))
    set_statement_timeout(plain, 0)
    try:
        with plain.connect() as connection:
            assert _setting(connection) == 0
    finally:
        plain.dispose()


def test_the_migrations_have_their_own_engine_without_the_timeout():
    source = ENV_PY.read_text(encoding="utf-8")

    assert "create_engine(ENGINE_URL, **engine_options(ENGINE_URL))" in source
    assert "set_statement_timeout" not in source


def test_a_full_pool_answers_503_quickly(auth_headers, monkeypatch):
    """The case of the issue: every connection is busy. Before: 500 after 30 seconds."""
    small = create_engine(
        DATABASE_URL, **(engine_options(DATABASE_URL) | {"pool_size": 1, "max_overflow": 0, "pool_timeout": 1})
    )
    monkeypatch.setattr(database.SessionLocal, "kw", database.SessionLocal.kw | {"bind": small})
    busy = small.connect()
    try:
        started = time.monotonic()
        response = TestClient(app, raise_server_exceptions=False).get("/library", headers=auth_headers)
        seconds = time.monotonic() - started
    finally:
        busy.close()
        small.dispose()

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json() == {"detail": "The server is busy. Please try again in a moment."}
    assert seconds < 5
