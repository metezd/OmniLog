"""Helper functions shared by the requirement-level tests.

These helpers call the public API only. They assert on every setup step, so a
test fails with a clear message when a prerequisite endpoint is missing.
"""
import uuid


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
