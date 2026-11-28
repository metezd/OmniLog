"""Fixtures for every backend test (tests/ and tests/requirements/)."""
import pytest


@pytest.fixture(autouse=True)
def rate_limits_off(monkeypatch):
    """Turn the rate limits off (#217).

    Almost every test registers and logs in a new user from the same test address, so the limits
    would stop the suite. tests/requirements/test_rate_limits.py turns them on again.
    The app is imported here and not at the top, because tests/requirements/conftest.py must set
    the environment before the app is imported.
    """
    from app.core import config, rate_limit

    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    rate_limit.reset()
    yield
    rate_limit.reset()


@pytest.fixture(autouse=True)
def media_create_on(monkeypatch):
    """Turn POST /media on (#218). It is off by default, but the test helpers use it to create
    titles. tests/requirements/test_media_access.py turns it off again."""
    from app.core import config

    monkeypatch.setattr(config, "ALLOW_MEDIA_CREATE", True)


@pytest.fixture(autouse=True)
def db_cache_off(monkeypatch):
    """Turn the database cache (L2, DB_CACHE_TTL_DAYS) off.

    Many tests clear Redis and open a title again to see a refresh from the outside service. With
    the cache on, a title that was just loaded would be served from PostgreSQL instead.
    tests/requirements/test_multilayer_cache.py turns it on again.
    """
    from app.core import config

    monkeypatch.setattr(config, "DB_CACHE_TTL_DAYS", 0)


@pytest.fixture(autouse=True)
def igdb_limiter_off(monkeypatch):
    """Turn the outgoing IGDB limit off. With it on, the tests that send many IGDB calls would
    wait 1/3 second for each. tests/requirements/test_igdb_efficiency.py turns it on again."""
    from app.core import config

    monkeypatch.setattr(config, "IGDB_MAX_REQUESTS_PER_SECOND", 0)


@pytest.fixture(autouse=True)
def background_jobs_finish():
    """Every background job of a test ends before the next test starts (#382).

    Without this a job could still write to the database or call a fake OpenAI of another test.
    A test that checks the result of a job calls app.core.background.wait_idle() itself.
    """
    from app.integrations import common, openai_client

    openai_client.reset_cooldown()
    common.reset_pauses()
    yield
    from app.core import background

    assert background.wait_idle(timeout=30), "a background job did not finish"
    openai_client.reset_cooldown()
    common.reset_pauses()
