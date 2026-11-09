"""Removing things (an extension of US-04 and US-06, outside the stories of the Charter).

- DELETE /library/{entry_id}: remove a title from the library. What the user logged for its
  chapters (ratings, playtime, decisions) goes with it.
- DELETE /lists/{list_id}/items/{media_item_id}: take a title out of a list.
- DELETE /lists/{list_id}: delete a list with its items.

Every removal is a new diary event. Older events are never deleted (US-07).
"""
import pytest

from app.models.entities import (
    ChapterProgress,
    CustomList,
    CustomListItem,
    DiaryEntry,
    PlaytimeLog,
    UserDecision,
    UserLibrary,
)
from app.services.diary_service import DiaryAction
from epic4_helpers import add_chapter, add_decision_point, diary_actions
from helpers import add_to_library, create_media, new_credentials, register_and_login, unique


@pytest.fixture
def other_headers(client):
    """A second user."""
    return register_and_login(client, new_credentials())


def make_list(client, headers, name=None):
    response = client.post("/lists", json={"name": name or unique("list")}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def add_to_list(client, headers, list_id, media_id):
    return client.post(f"/lists/{list_id}/items", json={"media_item_id": media_id}, headers=headers)


def log_progress(client, headers, entry_id, chapter_id):
    """A rating, some playtime and a decision for one chapter."""
    base = f"/library/{entry_id}/chapters/{chapter_id}"
    assert client.put(f"{base}/rating", json={"rating": 4}, headers=headers).status_code == 200
    assert client.post(f"{base}/playtime", json={"minutes": 30}, headers=headers).status_code == 201
    assert client.put(f"{base}/decision", json={"choice": "A"}, headers=headers).status_code == 200


def logged_rows(db, entry_id):
    db.expire_all()
    progress = db.query(ChapterProgress).filter(ChapterProgress.library_entry_id == entry_id)
    progress_ids = [p.id for p in progress]
    return (
        len(progress_ids),
        db.query(PlaytimeLog).filter(PlaytimeLog.chapter_progress_id.in_(progress_ids)).count() if progress_ids else 0,
        db.query(UserDecision).filter(UserDecision.library_entry_id == entry_id).count(),
    )


# ---------------------------------------------------------------- DELETE /library/{id}
def test_removing_an_entry_answers_204_and_it_leaves_the_library(client, auth_headers, library_entry):
    response = client.delete(f"/library/{library_entry['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert library_entry["id"] not in [e["id"] for e in client.get("/library", headers=auth_headers).json()]


def test_the_title_stays_in_the_catalog(client, auth_headers, media_item, library_entry):
    client.delete(f"/library/{library_entry['id']}", headers=auth_headers)

    assert client.get(f"/catalog/{media_item['id']}", headers=auth_headers).status_code == 200


def test_the_title_can_be_added_again_and_starts_fresh(client, auth_headers, media_item):
    first = add_to_library(client, auth_headers, media_item["id"], status="COMPLETED", rating=9)
    client.delete(f"/library/{first['id']}", headers=auth_headers)

    again = client.post("/library", json={"media_item_id": media_item["id"]}, headers=auth_headers)

    assert again.status_code == 201
    assert again.json()["id"] != first["id"]
    assert (again.json()["status"], again.json()["rating"]) == ("PLAN_TO_WATCH", None)


@pytest.mark.parametrize("entry_id", [999_999_999, 0, -1])
def test_an_unknown_entry_answers_404(client, auth_headers, entry_id):
    assert client.delete(f"/library/{entry_id}", headers=auth_headers).status_code == 404


def test_removing_twice_answers_404_the_second_time(client, auth_headers, library_entry):
    assert client.delete(f"/library/{library_entry['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/library/{library_entry['id']}", headers=auth_headers).status_code == 404


def test_the_entry_of_another_user_cannot_be_removed(client, auth_headers, other_headers, library_entry):
    """The answer is the same 404 as for an unknown id, so nobody can tell whether it exists."""
    response = client.delete(f"/library/{library_entry['id']}", headers=other_headers)

    assert response.status_code == 404
    assert response.json() == client.delete("/library/999999999", headers=other_headers).json()
    assert library_entry["id"] in [e["id"] for e in client.get("/library", headers=auth_headers).json()]


def test_removing_needs_a_login(client, library_entry):
    assert client.delete(f"/library/{library_entry['id']}").status_code == 401


def test_a_bad_id_is_refused(client, auth_headers):
    assert client.delete("/library/abc", headers=auth_headers).status_code == 422


def test_the_chapter_ratings_playtime_and_decisions_of_the_entry_go_with_it(client, auth_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")
    chapter_id = add_chapter(db, media["id"], 1)
    add_decision_point(db, chapter_id, media["id"])
    log_progress(client, auth_headers, entry["id"], chapter_id)
    assert logged_rows(db, entry["id"]) == (1, 1, 1)

    assert client.delete(f"/library/{entry['id']}", headers=auth_headers).status_code == 204

    assert logged_rows(db, entry["id"]) == (0, 0, 0)


def test_what_another_user_logged_for_the_same_title_stays(client, auth_headers, other_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    mine = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")
    theirs = add_to_library(client, other_headers, media["id"], status="IN_PROGRESS")
    chapter_id = add_chapter(db, media["id"], 1)
    add_decision_point(db, chapter_id, media["id"])
    log_progress(client, auth_headers, mine["id"], chapter_id)
    log_progress(client, other_headers, theirs["id"], chapter_id)

    client.delete(f"/library/{mine['id']}", headers=auth_headers)

    assert logged_rows(db, theirs["id"]) == (1, 1, 1)
    assert [e["id"] for e in client.get("/library", headers=other_headers).json()] == [theirs["id"]]


def test_the_title_stays_in_the_lists_of_the_user(client, auth_headers, media_item, library_entry):
    """A list is separate from the library, so removing from the library does not touch it."""
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    client.delete(f"/library/{library_entry['id']}", headers=auth_headers)

    items = client.get(f"/lists/{custom['id']}", headers=auth_headers).json()["items"]
    assert [i["media_item_id"] for i in items] == [media_item["id"]]


def test_the_removal_is_a_new_diary_event_and_the_old_ones_stay(client, auth_headers, other_headers, media_item):
    entry = add_to_library(client, auth_headers, media_item["id"], status="IN_PROGRESS", rating=8)
    before = diary_actions(client, auth_headers)

    client.delete(f"/library/{entry['id']}", headers=auth_headers)

    events = client.get("/diary", headers=auth_headers).json()
    assert [e["action"] for e in events][0] == "LIBRARY_REMOVED"
    assert [e["action"] for e in events][1:] == before  # nothing older was touched
    removed = events[0]
    assert (removed["media_item_id"], removed["details"]) == (media_item["id"], "Removed from library")
    assert diary_actions(client, other_headers) == []


def test_no_event_is_written_when_nothing_was_removed(client, auth_headers):
    client.delete("/library/999999999", headers=auth_headers)

    assert "LIBRARY_REMOVED" not in diary_actions(client, auth_headers)


def test_the_event_and_the_delete_are_saved_together(client, auth_headers, library_entry, db, monkeypatch):
    """If the event cannot be written, the entry is not removed either."""
    from app.services import library_service

    def broken(*args, **kwargs):
        raise RuntimeError("diary is broken")

    monkeypatch.setattr(library_service, "record_event", broken)

    with pytest.raises(RuntimeError):
        library_service.remove_entry(db, _user(db, auth_headers, client), library_entry["id"])
    db.rollback()

    assert db.get(UserLibrary, library_entry["id"]) is not None


def _user(db, headers, client):
    from app.models.entities import User

    username = client.get("/auth/me", headers=headers).json()["username"]
    return db.query(User).filter(User.username == username).one()


# ---------------------------------------------------------------- DELETE /lists/{id}/items/{media_id}
def test_taking_a_title_out_of_a_list_answers_204(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)
    other_title = create_media(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])
    add_to_list(client, auth_headers, custom["id"], other_title["id"])

    response = client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)

    assert response.status_code == 204
    items = client.get(f"/lists/{custom['id']}", headers=auth_headers).json()["items"]
    assert [i["media_item_id"] for i in items] == [other_title["id"]]  # only that title went


def test_the_title_is_still_in_the_catalog_and_the_library(client, auth_headers, media_item, library_entry):
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)

    assert client.get(f"/catalog/{media_item['id']}", headers=auth_headers).status_code == 200
    assert library_entry["id"] in [e["id"] for e in client.get("/library", headers=auth_headers).json()]


def test_a_title_can_be_added_to_the_list_again(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])
    client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)

    assert add_to_list(client, auth_headers, custom["id"], media_item["id"]).status_code == 201


def test_a_title_that_is_not_in_the_list_answers_404(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)

    # The title exists in the catalog, but not in this list
    assert client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers).status_code == 404
    assert client.delete(f"/lists/{custom['id']}/items/999999999", headers=auth_headers).status_code == 404


def test_taking_a_title_out_twice_answers_404_the_second_time(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    assert client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers).status_code == 404


def test_the_list_of_another_user_cannot_be_changed(client, auth_headers, other_headers, media_item):
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    response = client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=other_headers)

    assert response.status_code == 404
    assert len(client.get(f"/lists/{custom['id']}", headers=auth_headers).json()["items"]) == 1


def test_the_same_title_in_the_list_of_another_user_stays(client, auth_headers, other_headers, media_item):
    mine, theirs = make_list(client, auth_headers), make_list(client, other_headers)
    add_to_list(client, auth_headers, mine["id"], media_item["id"])
    add_to_list(client, other_headers, theirs["id"], media_item["id"])

    client.delete(f"/lists/{mine['id']}/items/{media_item['id']}", headers=auth_headers)

    assert len(client.get(f"/lists/{theirs['id']}", headers=other_headers).json()["items"]) == 1


def test_taking_a_title_out_needs_a_login(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)

    assert client.delete(f"/lists/{custom['id']}/items/{media_item['id']}").status_code == 401


def test_taking_a_title_out_is_a_diary_event_with_the_list_name(client, auth_headers, media_item):
    custom = make_list(client, auth_headers, name="Best narrative games")
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)

    latest = client.get("/diary", headers=auth_headers).json()[0]
    assert (latest["action"], latest["media_item_id"]) == ("LIST_ITEM_REMOVED", media_item["id"])
    assert latest["details"] == "Removed from list Best narrative games"
    assert "LIST_ITEM_ADDED" in diary_actions(client, auth_headers)  # the older event stays


def test_no_event_is_written_for_a_title_that_was_not_in_the_list(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)

    client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)

    assert "LIST_ITEM_REMOVED" not in diary_actions(client, auth_headers)


# ---------------------------------------------------------------- DELETE /lists/{id}
def test_deleting_a_list_answers_204_and_it_is_gone(client, auth_headers, media_item):
    custom = make_list(client, auth_headers)
    keep = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    response = client.delete(f"/lists/{custom['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(f"/lists/{custom['id']}", headers=auth_headers).status_code == 404
    ids = [item["id"] for item in client.get("/lists", headers=auth_headers).json()]
    assert custom["id"] not in ids and keep["id"] in ids


def test_the_items_of_the_list_are_deleted_and_the_titles_stay(client, auth_headers, media_item, library_entry, db):
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    client.delete(f"/lists/{custom['id']}", headers=auth_headers)

    db.expire_all()
    assert db.query(CustomListItem).filter(CustomListItem.list_id == custom["id"]).count() == 0
    assert client.get(f"/catalog/{media_item['id']}", headers=auth_headers).status_code == 200
    assert library_entry["id"] in [e["id"] for e in client.get("/library", headers=auth_headers).json()]


def test_the_name_of_a_deleted_list_can_be_used_again(client, auth_headers):
    custom = make_list(client, auth_headers, name="Weekend")
    client.delete(f"/lists/{custom['id']}", headers=auth_headers)

    again = client.post("/lists", json={"name": "Weekend"}, headers=auth_headers)

    assert again.status_code == 201
    assert again.json()["items"] == [] and again.json()["id"] != custom["id"]


def test_deleting_twice_or_an_unknown_list_answers_404(client, auth_headers):
    custom = make_list(client, auth_headers)

    assert client.delete(f"/lists/{custom['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/lists/{custom['id']}", headers=auth_headers).status_code == 404
    assert client.delete("/lists/999999999", headers=auth_headers).status_code == 404


def test_the_list_of_another_user_cannot_be_deleted(client, auth_headers, other_headers, db):
    custom = make_list(client, auth_headers)

    assert client.delete(f"/lists/{custom['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/lists/{custom['id']}", headers=auth_headers).status_code == 200


def test_a_list_with_the_same_name_of_another_user_stays(client, auth_headers, other_headers):
    mine, theirs = make_list(client, auth_headers, name="Shared name"), make_list(client, other_headers, name="Shared name")

    client.delete(f"/lists/{mine['id']}", headers=auth_headers)

    assert client.get(f"/lists/{theirs['id']}", headers=other_headers).status_code == 200


def test_deleting_a_list_needs_a_login(client, auth_headers):
    custom = make_list(client, auth_headers)

    assert client.delete(f"/lists/{custom['id']}").status_code == 401
    assert client.delete("/lists/abc", headers=auth_headers).status_code == 422


def test_deleting_a_list_is_a_diary_event_with_its_name_and_no_title(client, auth_headers, media_item):
    custom = make_list(client, auth_headers, name="Old favorites")
    add_to_list(client, auth_headers, custom["id"], media_item["id"])

    client.delete(f"/lists/{custom['id']}", headers=auth_headers)

    events = client.get("/diary", headers=auth_headers).json()
    assert (events[0]["action"], events[0]["media_item_id"], events[0]["details"]) == (
        "LIST_DELETED", None, "Deleted list Old favorites",
    )
    assert {"LIST_CREATED", "LIST_ITEM_ADDED"} <= {e["action"] for e in events}  # the old ones stay


def test_the_event_and_the_delete_of_a_list_are_saved_together(client, auth_headers, db, monkeypatch):
    from app.services import journal_service

    custom = make_list(client, auth_headers)

    def broken(*args, **kwargs):
        raise RuntimeError("diary is broken")

    monkeypatch.setattr(journal_service, "record_event", broken)

    with pytest.raises(RuntimeError):
        journal_service.delete_list(db, _user(db, auth_headers, client), custom["id"])
    db.rollback()

    assert db.get(CustomList, custom["id"]) is not None


# ---------------------------------------------------------------- the diary rule
def test_the_new_events_have_their_own_action_names():
    assert (DiaryAction.LIBRARY_REMOVED, DiaryAction.LIST_ITEM_REMOVED, DiaryAction.LIST_DELETED) == (
        "LIBRARY_REMOVED", "LIST_ITEM_REMOVED", "LIST_DELETED",
    )


def test_no_removal_deletes_a_diary_event(client, auth_headers, media_item, db):
    entry = add_to_library(client, auth_headers, media_item["id"], rating=7)
    custom = make_list(client, auth_headers)
    add_to_list(client, auth_headers, custom["id"], media_item["id"])
    count = db.query(DiaryEntry).count()
    mine = len(client.get("/diary", headers=auth_headers).json())

    client.delete(f"/lists/{custom['id']}/items/{media_item['id']}", headers=auth_headers)
    client.delete(f"/lists/{custom['id']}", headers=auth_headers)
    client.delete(f"/library/{entry['id']}", headers=auth_headers)

    db.expire_all()
    assert db.query(DiaryEntry).count() == count + 3
    assert len(client.get("/diary", headers=auth_headers).json()) == mine + 3
