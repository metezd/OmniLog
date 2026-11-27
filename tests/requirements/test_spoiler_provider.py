"""SPOILER_PROVIDER keeps review text inside the system while OpenAI stays on for embeddings (#397, US-14)."""
import os
import subprocess  # noqa: S404 - runs this interpreter to import the settings in a fresh process
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core import config
from app.integrations import openai_client
from app.services import review_service

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
SPOILER_TEXT = "In the final chapter the main character dies."


@pytest.fixture
def openai_must_not_be_called(monkeypatch):
    """A key is set, but any call to OpenAI fails the test."""
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        raise AssertionError("the review text was sent to OpenAI")

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        openai_client,
        "_client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    return calls


@pytest.mark.parametrize(
    ("key", "provider", "expected"),
    [
        ("test-key", "openai", True),
        ("test-key", "local", False),
        ("", "openai", False),
        ("", "local", False),
    ],
)
def test_uses_openai_needs_a_key_and_the_openai_provider(monkeypatch, key, provider, expected):
    monkeypatch.setattr(config, "OPENAI_API_KEY", key)
    monkeypatch.setattr(config, "SPOILER_PROVIDER", provider)

    assert review_service.uses_openai() is expected


def test_local_provider_keeps_the_review_out_of_openai(
    client, auth_headers, library_entry, monkeypatch, openai_must_not_be_called
):
    """With a key and SPOILER_PROVIDER=local, the local patterns check the review at once."""
    from app.core import background

    monkeypatch.setattr(config, "SPOILER_PROVIDER", "local")

    response = client.post(
        f"/library/{library_entry['id']}/review", json={"text": SPOILER_TEXT}, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["contains_spoiler"] is True
    assert body["spoiler_model_version"] == review_service.SPOILER_MODEL_VERSION
    assert background.wait_idle(timeout=10)
    assert openai_must_not_be_called == []


def test_detect_spoilers_with_local_provider_does_not_call_openai(
    monkeypatch, openai_must_not_be_called
):
    monkeypatch.setattr(config, "SPOILER_PROVIDER", "local")

    contains_spoiler, score, version = review_service.detect_spoilers(SPOILER_TEXT)

    assert contains_spoiler is True
    assert score is not None and score >= config.SPOILER_THRESHOLD
    assert version == review_service.SPOILER_MODEL_VERSION
    assert openai_must_not_be_called == []


def _import_config(provider: str | None) -> subprocess.CompletedProcess:
    """Import the settings in a fresh process, because they are read once at import time."""
    env = {
        **os.environ,
        "DATABASE_URL": "postgresql+psycopg2://u:p@localhost/x",
        "SECRET_KEY": "test-secret-key-at-least-32-characters-long",  # gitleaks:allow (dummy test value)
    }
    env.pop("SPOILER_PROVIDER", None)
    if provider is not None:
        env["SPOILER_PROVIDER"] = provider
    return subprocess.run(  # noqa: S603 - fixed command, this interpreter
        [sys.executable, "-c", "from app.core import config; print(config.SPOILER_PROVIDER)"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize(
    ("value", "expected"), [(None, "openai"), ("", "openai"), ("local", "local"), (" OpenAI ", "openai")]
)
def test_spoiler_provider_setting_is_read(value, expected):
    result = _import_config(value)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize("value", ["transformer", "off", "none"])
def test_backend_does_not_start_with_an_unknown_spoiler_provider(value):
    result = _import_config(value)

    assert result.returncode != 0
    assert "SPOILER_PROVIDER" in result.stderr
