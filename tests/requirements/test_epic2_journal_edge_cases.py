"""Edge cases for custom lists and the activity diary (US-06, US-07).

Covers the rules in docs/analysis/behavior/dfd-epic2-journal.md: unique list names, one title per
list, ownership, and an append-only diary that records only real changes.
"""
from helpers import HiddenPreCheck, add_to_library, new_credentials, register_and_login


def _create_list(client, headers, name="My list"):
    response = client.post("/lists", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _diary_actions(client, headers):
    return [event["action"] for event in client.get("/diary", headers=headers).json()]


# ---------------------------------------------------------------- lists: validation and uniqueness
def test_list_creation_requires_authentication(client):
    """US-06: POST /lists without a token returns 401."""
    assert client.post("/lists", json={"name": "x"}).status_code == 401


def test_duplicate_list_name_returns_409(client, auth_headers):
    """US-06: a second list with the same name for the same user returns 409."""
    _create_list(client, auth_headers, "Favourites")

    response = client.post("/lists", json={"name": "Favourites"}, headers=auth_headers)

    assert response.status_code == 409


def test_same_list_name_is_allowed_for_different_users(client, auth_headers):
    """US-06: the uniqueness rule applies per user, not globally."""
    _create_list(client, auth_headers, "Favourites")
    other_headers = register_and_login(client, new_credentials())

    response = client.post("/lists", json={"name": "Favourites"}, headers=other_headers)

    assert response.status_code == 201


def test_list_name_is_trimmed(client, auth_headers):
    """US-06: surrounding spaces are removed from the name."""
    response = client.post("/lists", json={"name": "  Favourites  "}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == "Favourites"


def test_blank_list_name_rejected(client, auth_headers):
    """US-06: a name with only spaces returns 422."""
    response = client.post("/lists", json={"name": "   "}, headers=auth_headers)

    assert response.status_code == 422


def test_list_name_longer_than_200_characters_rejected(client, auth_headers):
    """US-06: the name is limited to 200 characters, so the database never has to reject it."""
    response = client.post("/lists", json={"name": "a" * 201}, headers=auth_headers)

    assert response.status_code == 422


# ---------------------------------------------------------------- lists: reading and ownership
def test_get_lists_requires_authentication(client):
    """NFR-02: GET /lists without a token returns 401."""
    assert client.get("/lists").status_code == 401


def test_get_lists_returns_only_my_lists(client, auth_headers):
    """US-06: GET /lists shows the user's own lists and no one else's."""
    mine = _create_list(client, auth_headers, "Mine")
    other_headers = register_and_login(client, new_credentials())
    theirs = _create_list(client, other_headers, "Theirs")

    ids = [item["id"] for item in client.get("/lists", headers=auth_headers).json()]

    assert mine["id"] in ids
    assert theirs["id"] not in ids


def test_other_users_list_returns_404(client, auth_headers):
    """US-06: another user's list is not found, so its existence is not revealed."""
    lst = _create_list(client, auth_headers, "Private")
    other_headers = register_and_login(client, new_credentials())

    response = client.get(f"/lists/{lst['id']}", headers=other_headers)

    assert response.status_code == 404


def test_add_title_to_other_users_list_returns_404(client, auth_headers, media_item):
    """US-06: a user cannot add titles to another user's list."""
    lst = _create_list(client, auth_headers, "Private")
    other_headers = register_and_login(client, new_credentials())

    response = client.post(
        f"/lists/{lst['id']}/items",
        json={"media_item_id": media_item["id"]},
        headers=other_headers,
    )

    assert response.status_code == 404


def test_add_unknown_title_to_list_returns_404(client, auth_headers):
    """US-06: a media item that does not exist returns 404."""
    lst = _create_list(client, auth_headers)

    response = client.post(
        f"/lists/{lst['id']}/items",
        json={"media_item_id": 99999999},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_same_title_is_not_added_twice(client, auth_headers, media_item):
    """US-06: adding a title that is already in the list returns 200 and keeps one item."""
    lst = _create_list(client, auth_headers)
    url = f"/lists/{lst['id']}/items"
    body = {"media_item_id": media_item["id"]}

    first = client.post(url, json=body, headers=auth_headers)
    second = client.post(url, json=body, headers=auth_headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    detail = client.get(f"/lists/{lst['id']}", headers=auth_headers).json()
    assert len(detail["items"]) == 1


# ---------------------------------------------------------------- diary: events
def test_creating_a_list_writes_list_created_event(client, auth_headers):
    """US-07: creating a list writes a LIST_CREATED event."""
    _create_list(client, auth_headers)

    assert "LIST_CREATED" in _diary_actions(client, auth_headers)


def test_list_created_event_has_no_title(client, auth_headers):
    """US-07: LIST_CREATED is not about one title, so media_item_id is empty."""
    _create_list(client, auth_headers)

    events = client.get("/diary", headers=auth_headers).json()
    list_event = next(e for e in events if e["action"] == "LIST_CREATED")

    assert list_event["media_item_id"] is None


def test_adding_a_title_to_a_list_writes_event(client, auth_headers, media_item):
    """US-07: adding a title to a list writes a LIST_ITEM_ADDED event."""
    lst = _create_list(client, auth_headers)
    client.post(f"/lists/{lst['id']}/items", json={"media_item_id": media_item["id"]}, headers=auth_headers)

    assert "LIST_ITEM_ADDED" in _diary_actions(client, auth_headers)


def test_duplicate_list_item_writes_no_extra_event(client, auth_headers, media_item):
    """US-07: a title that is already in the list does not create another event."""
    lst = _create_list(client, auth_headers)
    url = f"/lists/{lst['id']}/items"
    body = {"media_item_id": media_item["id"]}
    client.post(url, json=body, headers=auth_headers)
    before = _diary_actions(client, auth_headers).count("LIST_ITEM_ADDED")

    client.post(url, json=body, headers=auth_headers)

    assert _diary_actions(client, auth_headers).count("LIST_ITEM_ADDED") == before


def test_adding_to_library_writes_library_added_event(client, auth_headers, media_item):
    """US-07: the event type is LIBRARY_ADDED, as in the domain model."""
    add_to_library(client, auth_headers, media_item["id"])

    assert "LIBRARY_ADDED" in _diary_actions(client, auth_headers)


def test_status_change_writes_status_changed_event(client, auth_headers, library_entry):
    """US-07: a status change writes a STATUS_CHANGED event."""
    client.patch(
        f"/library/{library_entry['id']}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )

    assert "STATUS_CHANGED" in _diary_actions(client, auth_headers)


def test_empty_patch_writes_no_event(client, auth_headers, library_entry):
    """US-07: a PATCH that changes nothing writes no event."""
    before = len(_diary_actions(client, auth_headers))

    client.patch(f"/library/{library_entry['id']}", json={}, headers=auth_headers)

    assert len(_diary_actions(client, auth_headers)) == before


def test_same_rating_writes_no_event(client, auth_headers, library_entry):
    """US-07: setting the rating to the value it already has writes no event."""
    client.patch(f"/library/{library_entry['id']}", json={"rating": 6}, headers=auth_headers)
    before = _diary_actions(client, auth_headers).count("RATED")

    client.patch(f"/library/{library_entry['id']}", json={"rating": 6}, headers=auth_headers)

    assert _diary_actions(client, auth_headers).count("RATED") == before


def test_same_status_writes_no_event(client, auth_headers, library_entry):
    """US-07: setting the status to the value it already has writes no event."""
    before = _diary_actions(client, auth_headers).count("STATUS_CHANGED")

    client.patch(
        f"/library/{library_entry['id']}",
        json={"status": library_entry["status"]},
        headers=auth_headers,
    )

    assert _diary_actions(client, auth_headers).count("STATUS_CHANGED") == before


def test_adding_with_rating_writes_rated_event(client, auth_headers, media_item):
    """US-07: a rating given when the title is added is recorded as RATED."""
    add_to_library(client, auth_headers, media_item["id"], rating=8)

    assert "RATED" in _diary_actions(client, auth_headers)


# ---------------------------------------------------------------- diary: reading
def test_diary_is_newest_first(client, auth_headers, media_item):
    """US-07: events come back with the newest first."""
    add_to_library(client, auth_headers, media_item["id"])
    _create_list(client, auth_headers)

    stamps = [e["created_at"] for e in client.get("/diary", headers=auth_headers).json()]

    assert stamps == sorted(stamps, reverse=True)


def test_diary_shows_only_my_events(client, auth_headers, media_item):
    """US-07: a user only sees the events they caused."""
    add_to_library(client, auth_headers, media_item["id"])
    other_headers = register_and_login(client, new_credentials())

    assert _diary_actions(client, other_headers) == []


def test_diary_requires_authentication(client):
    """NFR-02: GET /diary without a token returns 401."""
    assert client.get("/diary").status_code == 401


# ---------------------------------------------------------------- concurrency: unique constraints
# Two requests can both pass the "already exists?" check before either one writes.
# The database unique constraint is then the last line of defence. These tests hide the
# pre-check from the service, so the INSERT really hits the constraint, as in a race.
def _db_user(db, client, headers, media_id):
    """Return the ORM user behind the given auth headers."""
    from app.models.entities import User

    user_id = add_to_library(client, headers, media_id)["user_id"]
    return db.get(User, user_id)


def test_duplicate_list_name_race_is_caught_by_the_constraint(client, auth_headers, media_item):
    """US-06 / BR-06: when the pre-check misses a duplicate, the unique constraint still returns 409."""
    import pytest
    from app.core.database import SessionLocal
    from app.services import journal_service

    _create_list(client, auth_headers, "Race")
    db = SessionLocal()
    try:
        user = _db_user(db, client, auth_headers, media_item["id"])
        with pytest.raises(journal_service.DuplicateListNameError):
            journal_service.create_list(HiddenPreCheck(db, hide_call=1), user, "Race")
    finally:
        db.close()

    names = [lst["name"] for lst in client.get("/lists", headers=auth_headers).json()]
    assert names.count("Race") == 1


def test_duplicate_list_item_race_returns_existing_item(client, auth_headers, media_item):
    """US-06 / BR-06: when the pre-check misses a duplicate item, the existing item is returned."""
    from app.core.database import SessionLocal
    from app.services import journal_service

    lst = _create_list(client, auth_headers, "Race items")
    first = client.post(
        f"/lists/{lst['id']}/items", json={"media_item_id": media_item["id"]}, headers=auth_headers
    ).json()
    events_before = _diary_actions(client, auth_headers).count("LIST_ITEM_ADDED")

    db = SessionLocal()
    try:
        user = _db_user(db, client, auth_headers, media_item["id"])
        # call 1 = load the list, call 2 = "is the title already in the list?" (hidden)
        item, created = journal_service.add_item(
            HiddenPreCheck(db, hide_call=2), user, lst["id"], media_item["id"]
        )
    finally:
        db.close()

    assert created is False
    assert item.id == first["id"]
    assert _diary_actions(client, auth_headers).count("LIST_ITEM_ADDED") == events_before
