"""The Render Blueprint (render.yaml) matches the deployment pipeline of docs/deployment.md (#292).

Section 5 says that Render deploys main only after the GitHub checks pass, and section 7 says which
health path each web service uses. These tests fail when the file and the document drift apart.
"""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
WEB_SERVICES = {s["name"]: s for s in BLUEPRINT["services"] if s["type"] == "web"}

HEALTH_PATHS = {
    "omnilog-api": "/health",
    "omnilog-web": "/api/health",
}


def test_both_web_services_are_in_the_blueprint():
    assert set(WEB_SERVICES) == set(HEALTH_PATHS)


@pytest.mark.parametrize("name", sorted(HEALTH_PATHS))
def test_deploy_starts_only_after_the_checks_pass(name):
    assert WEB_SERVICES[name].get("autoDeployTrigger") == "checksPass"


@pytest.mark.parametrize(("name", "path"), sorted(HEALTH_PATHS.items()))
def test_health_check_path(name, path):
    assert WEB_SERVICES[name].get("healthCheckPath") == path


def test_health_check_is_not_the_readiness_path():
    # /health/ready answers 503 when the database is down, and a restart does not fix the database
    for service in WEB_SERVICES.values():
        assert service.get("healthCheckPath") != "/health/ready"


def test_migrations_run_before_the_api_starts():
    start = WEB_SERVICES["omnilog-api"]["startCommand"]

    assert start.startswith("alembic upgrade head && ")
    assert "uvicorn app.main:app" in start
