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
