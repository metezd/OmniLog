"""Helper functions shared by the requirement-level tests.

These helpers call the public API only. They assert on every setup step, so a
test fails with a clear message when a prerequisite endpoint is missing.
"""
import uuid

import pytest


def not_built(story: str):
    """Mark a requirement test of a story that is not built yet as an expected failure.

    The test stays in the suite and still runs, so the suite is green while the story is open.
    The mark is strict. When the story is built the test passes, and pytest reports that as a
    failure (XPASS strict). That is the sign to remove the mark.

    Only an AssertionError counts as the expected failure, which is what a missing endpoint gives
    (404 instead of 200). Any other error, such as a broken fixture or an import error, is still
    reported as a real failure.
    """
    return pytest.mark.xfail(
        strict=True, raises=AssertionError, reason=f"{story} is not implemented yet"
    )


def unique(prefix: str = "user") -> str:
    """Return a unique name so repeated test runs never collide (409)."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def new_credentials() -> dict:
    name = unique()
    return {
        "username": name,
        "email": f"{name}@example.com",
        "password": "StrongPass123!",
    }


def register_and_login(client, credentials: dict) -> dict:
    """Register a user, log in, and return the Authorization header."""
    reg = client.post("/auth/register", json=credentials)
    assert reg.status_code == 201, f"register failed: {reg.status_code} {reg.text}"

    login = client.post(
        "/auth/login",
        json={
            "username": credentials["username"],
            "password": credentials["password"],
        },
    )
    assert login.status_code == 200, f"login failed: {login.status_code} {login.text}"
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_media(client, headers: dict, media_type: str = "GAME", title: str = None) -> dict:
    """Create a media item in the catalog and return its JSON."""
    payload = {
        "title": title or unique("title"),
        "media_type": media_type,
        "release_date": "2020-01-01",
    }
    resp = client.post("/media", json=payload, headers=headers)
    assert resp.status_code == 201, f"create media failed: {resp.status_code} {resp.text}"
    return resp.json()


def add_to_library(client, headers: dict, media_item_id: int,
                   status: str = "PLAN_TO_WATCH", rating=None) -> dict:
    """Add a media item to the current user's library and return the entry."""
    payload = {"media_item_id": media_item_id, "status": status}
    if rating is not None:
        payload["rating"] = rating
    resp = client.post("/library", json=payload, headers=headers)
    assert resp.status_code == 201, f"add to library failed: {resp.status_code} {resp.text}"
    return resp.json()


class HiddenPreCheck:
    """Wraps a session so the n-th call to query(...).first() returns None.

    Two requests can both pass an "already exists?" check before either one writes.
    Hiding that check lets a test reach the unique-constraint fallback, as in a real race.
    """

    def __init__(self, session, hide_call: int):
        self._session = session
        self._hide_call = hide_call
        self._calls = 0

    def query(self, *args, **kwargs):
        self._calls += 1
        query = self._session.query(*args, **kwargs)
        if self._calls != self._hide_call:
            return query

        class _NoMatch:
            def filter(self, *a, **k):
                return self

            def first(self):
                return None

        return _NoMatch()

    def __getattr__(self, name):
        return getattr(self._session, name)
