"""The login token lasts 90 minutes by default (US-03). The frontend reads the end time from the
token (the exp claim) and gives its session cookie the same lifetime, so the two always agree."""
import os
import subprocess
import sys
import time
from pathlib import Path

from jose import jwt

from app.core import config
from helpers import new_credentials

BACKEND = Path(__file__).resolve().parents[2] / "backend"


def test_the_default_lifetime_is_90_minutes():
    """Checked in a fresh process, because the value is read once when the module loads."""
    environment = {key: value for key, value in os.environ.items() if key != "ACCESS_TOKEN_EXPIRE_MINUTES"}
    environment["PYTHONPATH"] = str(BACKEND)

    result = subprocess.run(
        [sys.executable, "-c", "from app.core import config; print(config.ACCESS_TOKEN_EXPIRE_MINUTES)"],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )

    assert result.stdout.strip() == "90"


def test_the_token_expires_after_the_configured_lifetime(client):
    credentials = new_credentials()
    client.post("/auth/register", json=credentials)

    response = client.post("/auth/login", json={"username": credentials["username"], "password": credentials["password"]})
    claims = jwt.get_unverified_claims(response.json()["access_token"])

    remaining_minutes = (claims["exp"] - time.time()) / 60
    assert config.ACCESS_TOKEN_EXPIRE_MINUTES - 1 < remaining_minutes <= config.ACCESS_TOKEN_EXPIRE_MINUTES


def test_the_token_has_the_two_claims_that_the_frontend_reads():
    """The frontend needs exp (cookie lifetime). The user id is in sub."""
    from app.core.security import create_access_token

    claims = jwt.get_unverified_claims(create_access_token(7))

    assert set(claims) == {"sub", "exp"}
    assert claims["sub"] == "7"
