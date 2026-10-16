"""Epic 1 - Backend Infrastructure and Database Foundation."""


def test_us01_health_returns_ok(client):
    """US-01: GET /health returns 200 and {"status": "healthy"}.

    This feature is already implemented, so this test is expected to pass.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

def test_root_returns_welcome_message(client):
    """US-01: GET / answers, so a quick browser check shows the backend is up."""
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


# ---------------------------------------------------------------- configuration: fail fast
def _reload_config_expecting_error(monkeypatch, message):
    """Reload app.core.config with a broken environment and return the RuntimeError text.

    The module is reloaded once more with the real environment afterwards, so other tests
    keep the normal settings.
    """
    import importlib

    import pytest
    import app.core.config as config

    try:
        with pytest.raises(RuntimeError) as error:
            importlib.reload(config)
        assert message in str(error.value)
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_missing_database_url_stops_startup(monkeypatch):
    """Epic 1: without DATABASE_URL the app refuses to start with a clear message."""
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)

    _reload_config_expecting_error(monkeypatch, "DATABASE_URL")


def test_short_secret_key_stops_startup(monkeypatch):
    """Epic 1: a SECRET_KEY shorter than 32 characters is rejected, so weak keys never sign tokens."""
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)

    _reload_config_expecting_error(monkeypatch, "at least 32 characters")
