"""Paging of the long lists: GET /diary, GET /library and GET /lists (issue perf/diary-index).

The three endpoints take `limit` and `offset`. The answer stays a plain list, and the order of each
endpoint does not change. Rows are inserted directly in the database, because the defaults (100 and
200) are too high to reach through the public API in a fast test.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import inspect

from helpers import new_credentials, register_and_login, unique

_BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


def _user_id(db, credentials) -> int:
    from app.models.entities import User

    return db.query(User).filter(User.username == credentials["username"]).one().id


def _seed_diary(db, user_id: int, count: int) -> None:
    """Event n happened n minutes after the first one, so the newest event has details `event {count - 1}`."""
    from app.models.entities import DiaryEntry

    db.add_all(
        DiaryEntry(
            user_id=user_id,
            action="LIST_CREATED",
            details=f"event {n}",
            created_at=_BASE_TIME + timedelta(minutes=n),
        )
        for n in range(count)
    )
    db.commit()


def _seed_library(db, user_id: int, count: int) -> list[int]:
    from app.models.entities import MediaItem, MediaType, UserLibrary

    items = [MediaItem(title=unique("paged"), media_type=MediaType.GAME) for _ in range(count)]
    db.add_all(items)
    db.flush()
    entries = [UserLibrary(user_id=user_id, media_item_id=item.id) for item in items]
    db.add_all(entries)
    db.commit()
    return [entry.id for entry in entries]


def _seed_lists(db, user_id: int, count: int) -> list[int]:
    from app.models.entities import CustomList

    lists = [CustomList(user_id=user_id, name=f"list {n:03d}") for n in range(count)]
    db.add_all(lists)
    db.commit()
    return [custom_list.id for custom_list in lists]


# ---------------------------------------------------------------- GET /diary
def test_diary_default_limit_is_100(client, db, credentials, auth_headers):
    """The diary answers with at most 100 events when no limit is given."""
    _seed_diary(db, _user_id(db, credentials), 120)

    response = client.get("/diary", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 100


def test_diary_order_is_newest_first(client, db, credentials, auth_headers):
    """The newest event comes first, and the page ends with the 100th newest event."""
    _seed_diary(db, _user_id(db, credentials), 120)

    events = client.get("/diary", headers=auth_headers).json()

    assert events[0]["details"] == "event 119"
    assert events[-1]["details"] == "event 20"
    times = [event["created_at"] for event in events]
    assert times == sorted(times, reverse=True)


def test_diary_offset_skips_the_newest_events(client, db, credentials, auth_headers):
    """offset=100 returns the events after the first page, still newest first."""
    _seed_diary(db, _user_id(db, credentials), 120)

    events = client.get("/diary", params={"offset": 100}, headers=auth_headers).json()

    assert [event["details"] for event in events] == [f"event {n}" for n in range(19, -1, -1)]


def test_diary_pages_do_not_overlap_or_skip(client, db, credentials, auth_headers):
    """Reading page after page gives every event once, in the same order as one big read."""
    _seed_diary(db, _user_id(db, credentials), 25)

    everything = client.get("/diary", headers=auth_headers).json()
    paged = []
    for offset in range(0, 25, 10):
        paged += client.get("/diary", params={"limit": 10, "offset": offset}, headers=auth_headers).json()

    assert [event["id"] for event in paged] == [event["id"] for event in everything]
    assert len({event["id"] for event in paged}) == 25


def test_diary_same_time_events_keep_a_stable_order(client, db, credentials, auth_headers):
    """Events with the same time are ordered by id, newest id first, so paging cannot repeat a row."""
    from app.models.entities import DiaryEntry

    user_id = _user_id(db, credentials)
    db.add_all(
        DiaryEntry(user_id=user_id, action="LIST_CREATED", details=f"same {n}", created_at=_BASE_TIME)
        for n in range(6)
    )
    db.commit()

    first = client.get("/diary", params={"limit": 3}, headers=auth_headers).json()
    second = client.get("/diary", params={"limit": 3, "offset": 3}, headers=auth_headers).json()

    ids = [event["id"] for event in first + second]
    assert ids == sorted(ids, reverse=True)
    assert len(set(ids)) == 6


def test_diary_limit_is_respected(client, db, credentials, auth_headers):
    """limit=5 returns the 5 newest events."""
    _seed_diary(db, _user_id(db, credentials), 12)

    events = client.get("/diary", params={"limit": 5}, headers=auth_headers).json()

    assert [event["details"] for event in events] == [f"event {n}" for n in range(11, 6, -1)]


def test_diary_limit_500_is_allowed(client, auth_headers):
    """500 is the highest allowed limit."""
    assert client.get("/diary", params={"limit": 500}, headers=auth_headers).status_code == 200


def test_diary_limit_above_the_maximum_returns_422(client, auth_headers):
    """A limit above 500 is rejected, not cut down."""
    assert client.get("/diary", params={"limit": 501}, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": -1}, {"offset": -1}, {"limit": "many"}])
def test_diary_invalid_paging_returns_422(client, auth_headers, params):
    """A limit below 1, a negative offset and values that are not numbers return 422."""
    assert client.get("/diary", params=params, headers=auth_headers).status_code == 422


def test_diary_offset_past_the_end_returns_an_empty_list(client, db, credentials, auth_headers):
    """An offset after the last event is not an error."""
    _seed_diary(db, _user_id(db, credentials), 3)

    response = client.get("/diary", params={"offset": 50}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_diary_paging_only_shows_own_events(client, db, credentials, auth_headers):
    """Paging never returns the events of another user."""
    _seed_diary(db, _user_id(db, credentials), 5)
    other = new_credentials()
    other_headers = register_and_login(client, other)
    _seed_diary(db, _user_id(db, other), 7)

    mine = client.get("/diary", params={"limit": 500}, headers=auth_headers).json()
    theirs = client.get("/diary", params={"limit": 500}, headers=other_headers).json()

    assert len(mine) == 5
    assert len(theirs) == 7
    assert not {event["id"] for event in mine} & {event["id"] for event in theirs}


def test_diary_paging_requires_authentication(client):
    """GET /diary with a limit and no token still returns 401."""
    assert client.get("/diary", params={"limit": 5}).status_code == 401


# ---------------------------------------------------------------- GET /library
def test_library_default_limit_is_200(client, db, credentials, auth_headers):
    """The library answers with at most 200 entries when no limit is given."""
    _seed_library(db, _user_id(db, credentials), 210)

    response = client.get("/library", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 200


def test_library_offset_and_order(client, db, credentials, auth_headers):
    """The library stays oldest first, and offset skips entries in that order."""
    entry_ids = _seed_library(db, _user_id(db, credentials), 12)

    page = client.get("/library", params={"limit": 5, "offset": 4}, headers=auth_headers).json()

    assert [entry["id"] for entry in page] == entry_ids[4:9]


def test_library_limit_above_the_maximum_returns_422(client, auth_headers):
    assert client.get("/library", params={"limit": 501}, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("params", [{"limit": 0}, {"offset": -1}])
def test_library_invalid_paging_returns_422(client, auth_headers, params):
    assert client.get("/library", params=params, headers=auth_headers).status_code == 422


# ---------------------------------------------------------------- GET /lists
def test_lists_default_limit_is_200(client, db, credentials, auth_headers):
    """The lists answer with at most 200 lists when no limit is given."""
    _seed_lists(db, _user_id(db, credentials), 210)

    response = client.get("/lists", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 200


def test_lists_offset_and_order(client, db, credentials, auth_headers):
    """The lists stay oldest first, and offset skips lists in that order."""
    list_ids = _seed_lists(db, _user_id(db, credentials), 12)

    page = client.get("/lists", params={"limit": 5, "offset": 4}, headers=auth_headers).json()

    assert [custom_list["id"] for custom_list in page] == list_ids[4:9]


def test_lists_limit_above_the_maximum_returns_422(client, auth_headers):
    assert client.get("/lists", params={"limit": 501}, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("params", [{"limit": 0}, {"offset": -1}])
def test_lists_invalid_paging_returns_422(client, auth_headers, params):
    assert client.get("/lists", params=params, headers=auth_headers).status_code == 422


# ---------------------------------------------------------------- the indexes
def test_diary_entries_have_the_two_indexes(db):
    """The diary list and the delete cascade of a title have an index each (migration 0013)."""
    indexes = {index["name"]: index for index in inspect(db.get_bind()).get_indexes("diary_entries")}

    assert indexes["ix_diary_entries_user_id_created_at"]["column_names"][:2] == ["user_id", "created_at"]
    assert indexes["ix_diary_entries_media_item_id"]["column_names"] == ["media_item_id"]


# ---------------------------------------------------------------- an offset that is too large (#420)
@pytest.mark.parametrize("path", ["/diary", "/library", "/lists"])
@pytest.mark.parametrize("offset", [2**31, 2**63])
def test_an_offset_above_the_maximum_returns_422(client, auth_headers, path, offset):
    """PostgreSQL keeps OFFSET as a 64 bit number, and 2**63 gave 500 before."""
    response = client.get(path, params={"offset": offset}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "offset"]


@pytest.mark.parametrize("path", ["/diary", "/library", "/lists"])
def test_the_largest_offset_is_allowed(client, auth_headers, path):
    response = client.get(path, params={"offset": 2**31 - 1}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
