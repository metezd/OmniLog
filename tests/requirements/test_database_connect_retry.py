"""The migrations wait for a database that cannot be reached yet (Render start, #402).

On Render `alembic upgrade head` runs right when a new instance starts. The private name of the
database could not be resolved for a few seconds, the first try failed with "could not translate
host name", and Render marked the deploy as failed although a second try worked.
"""
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core import database
from app.core.database import connect_with_retry

ENV_PY = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "env.py"


class FlakyEngine:
    """Fails with OperationalError for the first `failures` tries, then gives a real connection."""

    def __init__(self, failures, error=None):
        self.failures = failures
        self.calls = 0
        self.error = error or OperationalError(
            "connect", {}, Exception('could not translate host name "dpg-test-a" to address')
        )

    def connect(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return database.engine.connect()


def test_a_database_that_answers_later_is_waited_for():
    engine, waits = FlakyEngine(failures=2), []

    with connect_with_retry(engine, attempts=5, delay_seconds=3, sleep=waits.append) as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    assert engine.calls == 3
    assert waits == [3, 3]


def test_it_gives_up_after_the_last_try():
    engine, waits = FlakyEngine(failures=99), []

    with pytest.raises(OperationalError, match="could not translate host name"):
        connect_with_retry(engine, attempts=4, delay_seconds=1, sleep=waits.append)

    assert engine.calls == 4
    assert waits == [1, 1, 1]


def test_another_error_is_not_tried_again():
    engine = FlakyEngine(failures=1, error=ProgrammingError("SELECT", {}, Exception("permission denied")))

    with pytest.raises(ProgrammingError):
        connect_with_retry(engine, attempts=5, sleep=lambda _: None)

    assert engine.calls == 1


def test_the_try_is_logged_without_the_password(caplog):
    engine = FlakyEngine(failures=1)

    with connect_with_retry(engine, attempts=2, sleep=lambda _: None):
        pass

    assert "try 1 of 2" in caplog.text
    assert "dpg-test-a" not in caplog.text


def test_the_migrations_use_it():
    assert "with connect_with_retry(engine) as connection:" in ENV_PY.read_text(encoding="utf-8")
