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

# Tests always run against the separate test database, never the development one.
# This must be set before any `app` module is imported, because the engine is
# created at import time.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://omnilog:omnilog@localhost:5432/omnilog_test",
)

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


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    """Recreate all tables once per test session so every run starts clean."""
    from app.core.database import Base, engine
    import app.models.entities  # noqa: F401  (registers the tables on Base)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


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
