"""Shared pytest fixtures for the OmniLog requirement-level tests.

Run from the repository root:

    pytest tests/requirements -v

At the requirements stage these tests are EXPECTED TO FAIL: they describe
behaviour (user stories) that is not implemented yet.
"""
import os
import sys
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from fake_external_apis import FakeExternalApis
from helpers import (
    add_to_library,
    create_media,
    new_credentials,
    register_and_login,
)

# Make `import app...` work when pytest is started from the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend/.env first so TEST_DATABASE_URL set there is respected.
# Variables that are already set in the shell keep priority.
load_dotenv(BACKEND_DIR / ".env")

# Tests always run against the separate test database, never the development one.
# This must be set before any `app` module is imported, because the engine is
# created at import time.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://omnilog:omnilog@localhost:5432/omnilog_test",
)
# A fixed key for tests so they do not depend on a local .env file.
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-for-production-use")
# Fake credentials for IGDB and TMDB. The tests never reach the real services (see the
# fake_external_apis fixture below). A real value in backend/.env is kept for the live tests.
os.environ.setdefault("IGDB_CLIENT_ID", "test-igdb-client-id")
os.environ.setdefault("IGDB_CLIENT_SECRET", "test-igdb-client-secret")
os.environ.setdefault("TMDB_API_KEY", "test-tmdb-api-key")
os.environ.setdefault("EXTERNAL_API_BACKOFF_SECONDS", "0")  # retries must not slow the tests


def _ensure_test_database_exists(url: str) -> None:
    """Create the test database if it is missing.

    The init script in docker-compose.yml only runs on the first start of an
    empty volume, so an older volume would not have the test database.
    """
    target = make_url(url)
    admin = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target.database},
            ).scalar()
            if not exists:
                # Database names cannot be bound as parameters, so quote it safely
                conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    finally:
        admin.dispose()


_ensure_test_database_exists(os.environ["DATABASE_URL"])


@pytest.fixture(scope="session", autouse=True)
def fast_password_hashing():
    """Use the lowest bcrypt cost in tests.

    Almost every test registers and logs in a new user. At the production cost (12) that is
    about 0.65 s of hashing per test. Cost 4 is the minimum bcrypt allows and takes a few
    milliseconds. The hash format and the verify logic stay the same.
    """
    from app.core.security import pwd_context

    pwd_context.update(bcrypt__rounds=4)
    yield


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    """Recreate all tables once per test session so every run starts clean."""
    from app.core.database import Base, engine
    import app.models.entities  # noqa: F401  (registers the tables on Base)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    """A database session for a test that needs to read or prepare rows directly.

    Use this fixture instead of opening SessionLocal() in a test or in another fixture. The
    session is closed after the test, so an open transaction never leaks into the next test.
    """
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture
def credentials():
    return new_credentials()


@pytest.fixture
def auth_headers(client, credentials):
    """Authorization header of a freshly registered and logged-in user."""
    return register_and_login(client, credentials)


@pytest.fixture
def media_item(client, auth_headers):
    return create_media(client, auth_headers, media_type="GAME")


@pytest.fixture
def library_entry(client, auth_headers, media_item):
    return add_to_library(client, auth_headers, media_item["id"])


# ---------------------------------------------------------------- outside services
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: calls the real IGDB and TMDB. Needs real keys and RUN_LIVE_API_TESTS=1",
    )


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_LIVE_API_TESTS") == "1":
        return
    skip_live = pytest.mark.skip(reason="live API test: set RUN_LIVE_API_TESTS=1 and real keys")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def fake_external_apis(request, monkeypatch):
    """Put a fake under the IGDB and TMDB calls, and start every test with empty catalog caches.

    The real client code still runs. Tests marked `live` skip the fake and use the real services.
    """
    from app.core import cache
    from app.integrations import igdb

    cache.reset_connection()
    # Redis keeps its data between test runs, but the database is created again for each run
    cache.clear_prefix("omni:search:")
    cache.clear_prefix("omni:catalog:")
    igdb.reset_access_token()

    if request.node.get_closest_marker("live"):
        yield None
        return

    fake = FakeExternalApis()
    monkeypatch.setattr(requests.sessions.Session, "request", fake.request)
    yield fake
