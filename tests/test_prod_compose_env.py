"""docker-compose.prod.yml passes every backend setting to the container (#393).

A setting that is in backend/.env.example but not in x-backend-env is silently ignored in
production: the value in .env.prod never reaches the backend and the default is always used.
These tests fail when a new setting is added to the backend but not to the compose file, or when
the default of the compose file and the default of app/core/config.py drift apart.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8"))
BACKEND_ENV = COMPOSE["x-backend-env"]
CONFIG = (ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")

# Settings of backend/.env.example that are left out of x-backend-env on purpose
ALLOWED_MISSING = {
    # Used by pytest only
    "TEST_DATABASE_URL",
    # The compose setup uses FORWARDED_ALLOW_IPS of uvicorn instead (docs/deployment.md, section 4)
    "FORWARDED_TRUSTED_HOPS",
}

# "${NAME:-default}" with the name of the key itself
COMPOSE_DEFAULT = re.compile(r"^\$\{(?P<name>[A-Z0-9_]+):-(?P<default>[^}]*)\}$")
# os.getenv("NAME", "default") and _rate_limit("NAME", "default") in config.py
CONFIG_DEFAULT = re.compile(r'(?:os\.getenv|_rate_limit)\(\s*"(?P<name>[A-Z0-9_]+)",\s*"(?P<default>[^"]*)"')


def _example_names():
    text = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")
    return {line.split("=", 1)[0] for line in text.splitlines() if re.match(r"^[A-Z0-9_]+=", line)}


def _config_defaults():
    return {m["name"]: m["default"] for m in CONFIG_DEFAULT.finditer(CONFIG)}


def test_every_setting_of_the_example_reaches_the_backend():
    missing = _example_names() - set(BACKEND_ENV) - ALLOWED_MISSING

    assert not missing, f"Add these settings to x-backend-env in docker-compose.prod.yml: {sorted(missing)}"


def test_the_allowed_exceptions_are_still_in_the_example():
    # An exception that is no longer a setting should be removed from the list
    assert ALLOWED_MISSING <= _example_names()


def test_the_allowed_exceptions_are_really_left_out():
    assert not ALLOWED_MISSING & set(BACKEND_ENV)


@pytest.mark.parametrize(
    "name",
    sorted(
        name
        for name, value in BACKEND_ENV.items()
        if COMPOSE_DEFAULT.match(str(value)) and name in _config_defaults()
    ),
)
def test_the_compose_default_is_the_config_default(name):
    match = COMPOSE_DEFAULT.match(str(BACKEND_ENV[name]))

    assert match["name"] == name
    # ENABLE_DOCS is off in production on purpose (test_security_hardening.py)
    if name == "ENABLE_DOCS":
        assert match["default"] == "false"
        return
    assert match["default"] == _config_defaults()[name]


@pytest.mark.parametrize(
    "name",
    [
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "CACHE_TTL_SECONDS",
        "DETAILS_CACHE_TTL_SECONDS",
        "DB_CACHE_TTL_DAYS",
        "NEGATIVE_CACHE_TTL_SECONDS",
        "REDIS_SOCKET_TIMEOUT_SECONDS",
        "EXTERNAL_API_TIMEOUT_SECONDS",
        "EXTERNAL_API_MAX_RETRIES",
        "EXTERNAL_API_BACKOFF_SECONDS",
        "IGDB_MAX_REQUESTS_PER_SECOND",
        "FRONTEND_PROXY_SECRET",
    ],
)
def test_the_settings_of_issue_393_can_be_changed_in_env_prod(name):
    assert COMPOSE_DEFAULT.match(str(BACKEND_ENV[name]))["name"] == name


def test_nothing_requires_the_unused_public_api_address():
    """#430: no code reads NEXT_PUBLIC_API_URL, so neither the frontend image nor the compose file
    may require it (or API_URL) any more."""
    compose_text = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")

    assert "NEXT_PUBLIC_API_URL" not in compose_text + dockerfile + blueprint
    assert "API_URL" not in compose_text.replace("BACKEND_URL", "")
