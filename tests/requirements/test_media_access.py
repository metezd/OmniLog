"""Access to the shared catalog through /media (#218).

POST /media is off unless ALLOW_MEDIA_CREATE is on, GET /media/{id} needs a login, and a title
that a user adds may only use a poster from the TMDB or IGDB image host.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core import config

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
NEW_TITLE = {"title": "Access check title", "media_type": "GAME"}


def _allow_media_create(value):
    """Read ALLOW_MEDIA_CREATE in a fresh interpreter, because config reads it on import."""
    env = dict(os.environ)
    if value is None:
        env.pop("ALLOW_MEDIA_CREATE", None)
    else:
        env["ALLOW_MEDIA_CREATE"] = value
    result = subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", "from app.core import config; print(config.ALLOW_MEDIA_CREATE)"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return result.stdout.strip()


def test_media_create_is_off_by_default():
    assert _allow_media_create(None) == "False"


@pytest.mark.parametrize("value", ["true", "1", "yes", "on", "True"])
def test_media_create_can_be_turned_on(value):
    assert _allow_media_create(value) == "True"


@pytest.mark.parametrize("headers", ["none", "user"])
def test_post_media_answers_404_when_off(client, auth_headers, monkeypatch, headers):
    monkeypatch.setattr(config, "ALLOW_MEDIA_CREATE", False)

    response = client.post("/media", json=NEW_TITLE, headers=auth_headers if headers == "user" else {})

    assert response.status_code == 404


def test_post_media_works_when_on(client, auth_headers):
    response = client.post("/media", json=NEW_TITLE | {"title": "Access check on"}, headers=auth_headers)

    assert response.status_code == 201


def test_get_media_needs_a_token(client, media_item):
    assert client.get(f"/media/{media_item['id']}").status_code == 401


@pytest.mark.parametrize(
    "poster_url",
    [
        "https://image.tmdb.org/t/p/w500/a.jpg",
        "https://images.igdb.com/igdb/image/upload/t_cover_big/a.jpg",
    ],
)
def test_poster_from_tmdb_or_igdb_is_accepted(client, auth_headers, poster_url):
    title = f"Poster ok {poster_url[-30:]}"
    response = client.post("/media", json=NEW_TITLE | {"title": title, "poster_url": poster_url}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["poster_url"] == poster_url


@pytest.mark.parametrize(
    "poster_url",
    [
        "javascript:alert(document.domain)",
        "http://image.tmdb.org/t/p/w500/a.jpg",
        "https://attacker.example/pixel.png",
        "https://image.tmdb.org.attacker.example/a.jpg",
        "https://user@image.tmdb.org/a.jpg",
        "https://image.tmdb.org:8443/a.jpg",
        "//image.tmdb.org/a.jpg",
        "data:image/png;base64,AAAA",
        "https://image.tmdb.org/" + "a" * 500,
    ],
)
def test_other_poster_addresses_are_refused(client, auth_headers, poster_url):
    response = client.post("/media", json=NEW_TITLE | {"poster_url": poster_url}, headers=auth_headers)

    assert response.status_code == 422
