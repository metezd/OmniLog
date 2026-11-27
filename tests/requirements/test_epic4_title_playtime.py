"""Playtime of a whole game or movie, without a chapter (US-11, US-07, US-15, issue #413).

POST /library/{entry_id}/playtime adds one entry to the library entry itself. The total is in the
library entry (`playtime_minutes`) and counts in the statistics together with the chapters.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.entities import PlaytimeLog, UserLibrary
from app.schemas.chapter import MAX_PLAYTIME_MINUTES
from app.services import library_service
from epic4_helpers import add_chapter, diary_actions
from helpers import add_to_library, create_media, new_credentials, register_and_login


def log(client, headers, entry_id, body):
    return client.post(f"/library/{entry_id}/playtime", json=body, headers=headers)


def library_entry(client, headers, entry_id):
    return next(item for item in client.get("/library", headers=headers).json() if item["id"] == entry_id)


def title_logs(db, entry_id):
    db.expire_all()
    return (
        db.query(PlaytimeLog)
        .filter(PlaytimeLog.library_entry_id == entry_id)
        .order_by(PlaytimeLog.id)
        .all()
    )


@pytest.fixture
def game_entry(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")
    return {"media_id": media["id"], "entry_id": entry["id"]}


# ---------------------------------------------------------------- happy path
def test_a_game_entry_gets_201_and_the_new_total(client, auth_headers, game_entry):
    """US-11: a game without chapters can be logged as a whole."""
    response = log(client, auth_headers, game_entry["entry_id"], {"minutes": 60})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "library_entry_id", "minutes", "logged_at", "playtime_minutes"}
    assert (body["library_entry_id"], body["minutes"], body["playtime_minutes"]) == (
        game_entry["entry_id"], 60, 60,
    )
    assert body["logged_at"] is not None


def test_entries_add_up_and_the_library_shows_the_total(client, auth_headers, game_entry, db):
    """US-11: the total stays after a reload, because GET /library returns it."""
    assert library_entry(client, auth_headers, game_entry["entry_id"])["playtime_minutes"] == 0

    first = log(client, auth_headers, game_entry["entry_id"], {"minutes": 90}).json()
    second = log(client, auth_headers, game_entry["entry_id"], {"minutes": 30}).json()

    assert (first["playtime_minutes"], second["playtime_minutes"]) == (90, 120)
    assert library_entry(client, auth_headers, game_entry["entry_id"])["playtime_minutes"] == 120
    assert [row.minutes for row in title_logs(db, game_entry["entry_id"])] == [90, 30]


def test_a_movie_can_be_logged_as_a_whole(client, auth_headers):
    movie = create_media(client, auth_headers, media_type="MOVIE")
    entry = add_to_library(client, auth_headers, movie["id"])

    response = log(client, auth_headers, entry["id"], {"minutes": 125})

    assert response.status_code == 201
    assert response.json()["playtime_minutes"] == 125


def test_a_series_is_refused_with_422(client, auth_headers, db):
    """US-11: a series is logged on its episodes, so the whole title cannot get time."""
    series = create_media(client, auth_headers, media_type="SERIES")
    entry = add_to_library(client, auth_headers, series["id"])

    response = log(client, auth_headers, entry["id"], {"minutes": 45})

    assert response.status_code == 422
    assert "episodes" in response.json()["detail"]
    assert title_logs(db, entry["id"]) == []


def test_title_and_chapter_playtime_stay_apart(client, auth_headers, game_entry, db):
    """US-11: time on a chapter does not change the total of the whole title, and the other way."""
    chapter_id = add_chapter(db, game_entry["media_id"], 1)
    url = f"/library/{game_entry['entry_id']}/chapters/{chapter_id}"
    client.post(f"{url}/playtime", json={"minutes": 20}, headers=auth_headers)
    log(client, auth_headers, game_entry["entry_id"], {"minutes": 50})

    assert client.get(url, headers=auth_headers).json()["playtime_minutes"] == 20
    assert library_entry(client, auth_headers, game_entry["entry_id"])["playtime_minutes"] == 50


# ---------------------------------------------------------------- diary and statistics
def test_an_entry_is_written_to_the_diary(client, auth_headers, game_entry):
    """US-07: every entry is a PLAYTIME_LOGGED event."""
    log(client, auth_headers, game_entry["entry_id"], {"minutes": 15})

    events = client.get("/diary", headers=auth_headers).json()
    assert events[0]["action"] == "PLAYTIME_LOGGED"
    assert events[0]["media_item_id"] == game_entry["media_id"]


def test_the_statistics_count_title_and_chapter_playtime(client, auth_headers, game_entry, db):
    """US-15: the playtime of the whole title and of its chapters add up for that title."""
    assert client.get("/stats", headers=auth_headers).json()["playtime"]["total_minutes"] == 0
    chapter_id = add_chapter(db, game_entry["media_id"], 1)
    client.post(
        f"/library/{game_entry['entry_id']}/chapters/{chapter_id}/playtime",
        json={"minutes": 120},
        headers=auth_headers,
    )
    log(client, auth_headers, game_entry["entry_id"], {"minutes": 240})

    playtime = client.get("/stats", headers=auth_headers).json()["playtime"]
    assert playtime["total_minutes"] == 360
    # 6 hours fall into the bucket 5-10h, so the title is counted once and not twice
    assert {"bucket": "5-10h", "count": 1} in playtime["histogram"]


# ---------------------------------------------------------------- invalid input
@pytest.mark.parametrize(
    "body",
    [
        {"minutes": 0},
        {"minutes": -5},
        {"minutes": MAX_PLAYTIME_MINUTES + 1},
        {"minutes": 1.5},
        {"minutes": "30"},
        {"minutes": True},
        {"minutes": None},
        {},
    ],
)
def test_invalid_minutes_return_422_and_change_nothing(client, auth_headers, game_entry, db, body):
    """US-11, BR-12: only a whole number from 1 up to the limit is a playtime."""
    before = diary_actions(client, auth_headers)

    response = log(client, auth_headers, game_entry["entry_id"], body)

    assert response.status_code == 422
    assert title_logs(db, game_entry["entry_id"]) == []
    assert diary_actions(client, auth_headers) == before


def test_the_total_of_a_title_has_a_limit(client, auth_headers, game_entry, db):
    db.query(UserLibrary).filter(UserLibrary.id == game_entry["entry_id"]).update(
        {UserLibrary.playtime_minutes: library_service.MAX_TOTAL_TITLE_PLAYTIME_MINUTES}
    )
    db.commit()

    response = log(client, auth_headers, game_entry["entry_id"], {"minutes": 1})

    assert response.status_code == 422
    assert title_logs(db, game_entry["entry_id"]) == []


# ---------------------------------------------------------------- ownership (BR-11)
def test_another_users_entry_is_404(client, auth_headers, game_entry, db):
    """US-11: one user cannot log time on the library entry of another user."""
    other = register_and_login(client, new_credentials())

    response = log(client, other, game_entry["entry_id"], {"minutes": 10})

    assert response.status_code == 404
    assert title_logs(db, game_entry["entry_id"]) == []


@pytest.mark.parametrize("entry_id", [0, -1, 2**31, 2**63])
def test_ids_that_cannot_exist_are_404(client, auth_headers, entry_id):
    assert log(client, auth_headers, entry_id, {"minutes": 10}).status_code == 404


def test_without_a_token_it_is_401(client, game_entry):
    assert log(client, {}, game_entry["entry_id"], {"minutes": 10}).status_code == 401


def test_removing_the_entry_removes_its_playtime(client, auth_headers, game_entry, db):
    log(client, auth_headers, game_entry["entry_id"], {"minutes": 30})

    assert client.delete(f"/library/{game_entry['entry_id']}", headers=auth_headers).status_code == 204
    assert title_logs(db, game_entry["entry_id"]) == []


# ---------------------------------------------------------------- database rules
def test_an_entry_must_belong_to_exactly_one_target(db, client, auth_headers, game_entry):
    """BR-12: a playtime entry points to a chapter or to a whole title, never to none or both."""
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO playtime_logs (minutes) VALUES (5)"))
        db.commit()
    db.rollback()
