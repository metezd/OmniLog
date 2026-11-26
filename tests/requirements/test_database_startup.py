"""The API uses PostgreSQL only, and says so when the database cannot be reached (#371).

Before, a local PostgreSQL that was not running made the API switch to an empty SQLite file without
a word. /health/ready then said "ready" and the first real request failed with 500. Now there is
no SQLite fallback, and the API refuses to start when the local PostgreSQL is not running.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core import database
from app.core.database import DatabaseUnreachableError, check_database
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
SECRET = "test-secret-key-at-least-32-characters-long"

# Nothing listens on port 1, so a connection is refused at once
LOCAL_DOWN = "postgresql+psycopg2://u:p@127.0.0.1:1/omnilog"


def import_database(tmp_path, url):
    """Import app.core.database in a new Python with this DATABASE_URL, in an empty folder."""
    env = {key: value for key, value in os.environ.items() if key != "DATABASE_URL"}
    env.update({"PYTHONPATH": str(BACKEND_DIR), "SECRET_KEY": SECRET})
    if url is not None:
        env["DATABASE_URL"] = url
    return subprocess.run(
        [sys.executable, "-c", "from app.core import database; print(database.engine.url.drivername)"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
    )


def test_a_local_postgresql_that_is_down_is_not_replaced_by_sqlite(tmp_path):
    result = import_database(tmp_path, "postgresql+psycopg2://u:p@localhost:5999/x")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "postgresql+psycopg2"
    assert not (tmp_path / "omnilog_local.db").exists()


def test_a_missing_database_url_stops_the_import(tmp_path):
    result = import_database(tmp_path, None)

    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr
    assert not (tmp_path / "omnilog_local.db").exists()


def test_the_database_code_has_no_sqlite_left():
    for path in (BACKEND_DIR / "app" / "core" / "database.py", BACKEND_DIR / "app" / "models" / "entities.py"):
        assert "sqlite" not in path.read_text(encoding="utf-8").lower(), path


def test_a_reachable_database_passes_the_check():
    check_database(database.engine)


def test_a_local_database_that_is_down_stops_with_a_clear_message():
    engine = create_engine(LOCAL_DOWN)

    with pytest.raises(DatabaseUnreachableError) as caught:
        check_database(engine)

    message = str(caught.value)
    assert "127.0.0.1:1" in message
    assert "docker compose up -d" in message
    assert "p@" not in message  # the password is never shown


def test_a_remote_database_that_is_down_only_logs(caplog):
    # On Render or in Docker the database can start later; /health/ready shows 503 until then
    engine = create_engine("postgresql+psycopg2://u:p@db.invalid:5432/omnilog", connect_args={"connect_timeout": 2})

    with caplog.at_level(logging.WARNING):
        check_database(engine)

    assert "db.invalid" in caplog.text
    assert "p@" not in caplog.text


def test_the_api_does_not_start_when_the_local_database_is_down(monkeypatch):
    monkeypatch.setattr(database, "engine", create_engine(LOCAL_DOWN))

    with pytest.raises(DatabaseUnreachableError):
        with TestClient(app):
            pass


def test_the_api_starts_when_the_database_answers():
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 200
