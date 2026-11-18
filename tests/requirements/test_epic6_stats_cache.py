"""Statistics cache invalidation (US-15).

The cache key is `omni:stats:{user_id}`. It is populated on the first GET /stats after a
write and is deleted whenever the user changes their library, ratings, playtime or decisions.
The three removal endpoints (DELETE /library/{id}, DELETE /lists/{id}/items/{media_item_id}
and DELETE /lists/{id}) also trigger invalidation.

These tests use the in-process fallback cache (Redis is not required), so they run without
any external infrastructure.
"""
import pytest

from app.core import cache
from app.services.stats_service import _STATS_KEY_PREFIX
from epic4_helpers import add_chapter
from helpers import add_to_library, create_media, new_credentials, register_and_login


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def get_stats(client, headers):
    response = client.get("/stats", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def stats_cache_key(client, headers):
    """Return the cache key for the user behind *headers*."""
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    user_id = me.json()["id"]
    return f"{_STATS_KEY_PREFIX}{user_id}"


def cache_is_populated(client, headers) -> bool:
    return cache.get_json(stats_cache_key(client, headers)) is not None


@pytest.fixture
def other_headers(client):
    """A second, independent user."""
    return register_and_login(client, new_credentials())


# ---------------------------------------------------------------------------
# cache population
# ---------------------------------------------------------------------------

def test_first_get_populates_the_cache(client, auth_headers):
    assert not cache_is_populated(client, auth_headers)

    get_stats(client, auth_headers)

    assert cache_is_populated(client, auth_headers)


def test_cache_hit_returns_the_same_data(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    add_to_library(client, auth_headers, media["id"], rating=7)

    first = get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)
    second = get_stats(client, auth_headers)  # served from cache

    assert first == second


# ---------------------------------------------------------------------------
# invalidation: library changes
# ---------------------------------------------------------------------------

def test_adding_a_title_invalidates_the_cache(client, auth_headers):
    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    media = create_media(client, auth_headers, media_type="GAME")
    client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)

    assert not cache_is_populated(client, auth_headers)


def test_updating_an_entry_invalidates_the_cache(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    resp = client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)
    entry_id = resp.json()["id"]

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.patch(f"/library/{entry_id}", json={"rating": 8}, headers=auth_headers)

    assert not cache_is_populated(client, auth_headers)


def test_removing_a_library_entry_invalidates_the_cache(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    resp = client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)
    entry_id = resp.json()["id"]

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.delete(f"/library/{entry_id}", headers=auth_headers)

    assert not cache_is_populated(client, auth_headers)


# ---------------------------------------------------------------------------
# invalidation: ratings, playtime and decisions (chapter endpoints)
# ---------------------------------------------------------------------------

def test_logging_playtime_invalidates_the_cache(client, auth_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    resp = client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)
    entry = resp.json()

    chapter_id = add_chapter(db, entry["media_item_id"], number=1)

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.post(
        f"/library/{entry['id']}/chapters/{chapter_id}/playtime",
        json={"minutes": 60},
        headers=auth_headers,
    )

    assert not cache_is_populated(client, auth_headers)


def test_rating_a_chapter_invalidates_the_cache(client, auth_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    resp = client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)
    entry = resp.json()

    chapter_id = add_chapter(db, entry["media_item_id"], number=1)

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.put(
        f"/library/{entry['id']}/chapters/{chapter_id}/rating",
        json={"rating": 4},
        headers=auth_headers,
    )

    assert not cache_is_populated(client, auth_headers)


# ---------------------------------------------------------------------------
# invalidation: list removal endpoints
# ---------------------------------------------------------------------------

def test_removing_an_item_from_a_list_invalidates_the_cache(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    list_resp = client.post("/lists", json={"name": "My list"}, headers=auth_headers)
    list_id = list_resp.json()["id"]
    client.post(f"/lists/{list_id}/items", json={"media_item_id": media["id"]}, headers=auth_headers)

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.delete(f"/lists/{list_id}/items/{media['id']}", headers=auth_headers)

    assert not cache_is_populated(client, auth_headers)


def test_deleting_a_list_invalidates_the_cache(client, auth_headers):
    list_resp = client.post("/lists", json={"name": "To delete"}, headers=auth_headers)
    list_id = list_resp.json()["id"]

    get_stats(client, auth_headers)
    assert cache_is_populated(client, auth_headers)

    client.delete(f"/lists/{list_id}", headers=auth_headers)

    assert not cache_is_populated(client, auth_headers)


# ---------------------------------------------------------------------------
# cache is per-user: one user's invalidation must not affect another's
# ---------------------------------------------------------------------------

def test_a_write_by_one_user_does_not_invalidate_another_users_cache(
    client, auth_headers, other_headers
):
    # Warm up both caches
    get_stats(client, auth_headers)
    get_stats(client, other_headers)
    assert cache_is_populated(client, auth_headers)
    assert cache_is_populated(client, other_headers)

    # Only the first user changes their library
    media = create_media(client, auth_headers, media_type="GAME")
    client.post("/library", json={"media_item_id": media["id"]}, headers=auth_headers)

    # First user's cache is gone; second user's is intact
    assert not cache_is_populated(client, auth_headers)
    assert cache_is_populated(client, other_headers)


# ---------------------------------------------------------------------------
# freshness: the cache always reflects the latest state
# ---------------------------------------------------------------------------

def test_stats_are_fresh_after_cache_repopulation(client, auth_headers):
    """Add a title, warm the cache, add another → cache busted → next read is fresh."""
    media1 = create_media(client, auth_headers, media_type="GAME")
    add_to_library(client, auth_headers, media1["id"], rating=5)

    stats_before = get_stats(client, auth_headers)  # warms cache
    assert stats_before["total_items"] == 1

    media2 = create_media(client, auth_headers, media_type="SERIES")
    add_to_library(client, auth_headers, media2["id"])  # busts cache

    stats_after = get_stats(client, auth_headers)  # repopulates cache
    assert stats_after["total_items"] == 2
    assert cache_is_populated(client, auth_headers)
