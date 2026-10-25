"""Edge cases for logging playtime per chapter (US-11, BR-11, BR-12, US-07, NFR-02).

The chapters are saved in the database directly (see epic4_helpers.py).
"""
import threading
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.entities import (
    Chapter,
    ChapterKind,
    ChapterProgress,
    PlaytimeLog,
    User,
    UserLibrary,
)
from app.schemas.chapter import MAX_PLAYTIME_MINUTES
from app.services import chapter_service
from epic4_helpers import add_chapter, add_episode, diary_actions
from helpers import (
    HiddenPreCheck,
    add_to_library,
    create_media,
    new_credentials,
    register_and_login,
)


# ---------------------------------------------------------------- helpers
def base_url(entry_id, chapter_id):
    return f"/library/{entry_id}/chapters/{chapter_id}"


def log(client, headers, entry_id, chapter_id, body):
    return client.post(f"{base_url(entry_id, chapter_id)}/playtime", json=body, headers=headers)


def total(client, headers, entry_id, chapter_id):
    return client.get(base_url(entry_id, chapter_id), headers=headers).json()["playtime_minutes"]


def progress_rows(db, entry_id, chapter_id):
    db.expire_all()
    return (
        db.query(ChapterProgress)
        .filter(ChapterProgress.library_entry_id == entry_id, ChapterProgress.chapter_id == chapter_id)
        .all()
    )


def log_rows(db, entry_id, chapter_id):
    db.expire_all()
    return (
        db.query(PlaytimeLog)
        .join(ChapterProgress, PlaytimeLog.chapter_progress_id == ChapterProgress.id)
        .filter(ChapterProgress.library_entry_id == entry_id, ChapterProgress.chapter_id == chapter_id)
        .order_by(PlaytimeLog.id)
        .all()
    )


@pytest.fixture
def game(client, auth_headers, db):
    """A game in the library of the logged-in user, with two chapters."""
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")
    return {
        "media_id": media["id"],
        "entry_id": entry["id"],
        "chapter_id": add_chapter(db, media["id"], 1),
        "second_chapter_id": add_chapter(db, media["id"], 2),
    }


# ---------------------------------------------------------------- happy path
def test_one_entry_returns_201_and_the_new_total(client, auth_headers, game):
    response = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 45})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "chapter_id", "minutes", "logged_at", "playtime_minutes"}
    assert (body["chapter_id"], body["minutes"], body["playtime_minutes"]) == (game["chapter_id"], 45, 45)
    assert body["logged_at"] is not None


def test_entries_add_up_and_every_answer_shows_the_running_total(client, auth_headers, game):
    """US-11: 90 and later 30 minutes make 120."""
    first = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 90}).json()
    second = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 30}).json()

    assert (first["playtime_minutes"], second["playtime_minutes"]) == (90, 120)
    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 120


def test_the_total_is_the_sum_of_the_saved_entries(client, auth_headers, game, db):
    """BR-12: the total and the single entries always agree."""
    for minutes in (10, 25, 5):
        log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": minutes})

    entries = [row.minutes for row in log_rows(db, game["entry_id"], game["chapter_id"])]
    assert entries == [10, 25, 5]
    assert progress_rows(db, game["entry_id"], game["chapter_id"])[0].playtime_minutes == sum(entries)


def test_chapters_keep_their_own_totals(client, auth_headers, game):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 60})
    log(client, auth_headers, game["entry_id"], game["second_chapter_id"], {"minutes": 15})

    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 60
    assert total(client, auth_headers, game["entry_id"], game["second_chapter_id"]) == 15


def test_an_episode_of_a_series_can_get_playtime(client, auth_headers, db):
    series = create_media(client, auth_headers, media_type="SERIES")
    entry = add_to_library(client, auth_headers, series["id"], status="IN_PROGRESS")
    episode_id = add_episode(db, series["id"])

    response = log(client, auth_headers, entry["id"], episode_id, {"minutes": 50})

    assert response.status_code == 201
    assert total(client, auth_headers, entry["id"], episode_id) == 50


def test_two_users_log_the_same_chapter_independently(client, auth_headers, game):
    other = register_and_login(client, new_credentials())
    other_entry = add_to_library(client, other, game["media_id"])

    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 100})
    log(client, other, other_entry["id"], game["chapter_id"], {"minutes": 7})

    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 100
    assert total(client, other, other_entry["id"], game["chapter_id"]) == 7


def test_playtime_and_rating_share_one_progress_row(client, auth_headers, game, db):
    """The rating and the playtime of a chapter live in the same row, in any order."""
    url = base_url(game["entry_id"], game["chapter_id"])
    client.put(f"{url}/rating", json={"rating": 4}, headers=auth_headers)
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 30})
    log(client, auth_headers, game["entry_id"], game["second_chapter_id"], {"minutes": 20})
    client.put(f"{base_url(game['entry_id'], game['second_chapter_id'])}/rating", json={"rating": 2}, headers=auth_headers)

    first = client.get(url, headers=auth_headers).json()
    second = client.get(base_url(game["entry_id"], game["second_chapter_id"]), headers=auth_headers).json()
    assert (first["rating"], first["playtime_minutes"]) == (4, 30)
    assert (second["rating"], second["playtime_minutes"]) == (2, 20)
    assert len(progress_rows(db, game["entry_id"], game["chapter_id"])) == 1


def test_a_new_rating_does_not_change_the_playtime(client, auth_headers, game):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 40})

    client.put(f"{base_url(game['entry_id'], game['chapter_id'])}/rating", json={"rating": 5}, headers=auth_headers)

    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 40


# ---------------------------------------------------------------- invalid minutes (BR-12)
@pytest.mark.parametrize("value", [1, 60, MAX_PLAYTIME_MINUTES])
def test_minutes_inside_the_range_are_accepted(client, auth_headers, game, value):
    response = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": value})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "body",
    [
        {"minutes": 0},
        {"minutes": -5},
        {"minutes": MAX_PLAYTIME_MINUTES + 1},
        {"minutes": 2**31},
        {"minutes": 1.5},
        {"minutes": 30.0},
        {"minutes": "30"},
        {"minutes": True},
        {"minutes": None},
        {"minutes": [30]},
        {},
    ],
)
def test_invalid_minutes_return_422(client, auth_headers, game, db, body):
    """US-11 and BR-12: only a whole number from 1 up to the limit is a playtime."""
    response = log(client, auth_headers, game["entry_id"], game["chapter_id"], body)

    assert response.status_code == 422
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
    assert log_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_a_rejected_entry_changes_nothing(client, auth_headers, game, db):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 30})
    before = diary_actions(client, auth_headers).count("PLAYTIME_LOGGED")

    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": -5})

    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 30
    assert len(log_rows(db, game["entry_id"], game["chapter_id"])) == 1
    assert diary_actions(client, auth_headers).count("PLAYTIME_LOGGED") == before


def test_a_nan_value_returns_422_not_500(client, auth_headers, game):
    response = client.post(
        f"{base_url(game['entry_id'], game['chapter_id'])}/playtime",
        content='{"minutes": NaN}',
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_a_body_that_is_not_json_returns_422(client, auth_headers, game):
    response = client.post(
        f"{base_url(game['entry_id'], game['chapter_id'])}/playtime",
        content="not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_the_total_of_a_chapter_has_a_limit(client, auth_headers, game, db, monkeypatch):
    """The total can never grow until the INTEGER column overflows. A 422 is returned instead."""
    monkeypatch.setattr(chapter_service, "MAX_TOTAL_PLAYTIME_MINUTES", 100)
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 90})

    response = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 11})
    exact = log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})

    assert response.status_code == 422
    assert exact.status_code == 201
    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 100
    assert len(log_rows(db, game["entry_id"], game["chapter_id"])) == 2


# ---------------------------------------------------------------- access (BR-11, NFR-02)
def test_logging_needs_a_token(client, game):
    response = client.post(f"{base_url(game['entry_id'], game['chapter_id'])}/playtime", json={"minutes": 5})

    assert response.status_code == 401


def test_reading_needs_a_token(client, game):
    assert client.get(base_url(game["entry_id"], game["chapter_id"])).status_code == 401


def test_the_library_entry_of_another_user_returns_404(client, game, db):
    """BR-11: a user cannot log time or read progress through the entry of someone else."""
    other = register_and_login(client, new_credentials())

    posted = log(client, other, game["entry_id"], game["chapter_id"], {"minutes": 5})
    read = client.get(base_url(game["entry_id"], game["chapter_id"]), headers=other)

    assert (posted.status_code, read.status_code) == (404, 404)
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_a_chapter_that_does_not_exist_returns_404(client, auth_headers, game):
    assert log(client, auth_headers, game["entry_id"], 99999999, {"minutes": 5}).status_code == 404
    assert client.get(base_url(game["entry_id"], 99999999), headers=auth_headers).status_code == 404


def test_a_chapter_of_another_title_returns_404(client, auth_headers, game, db):
    """BR-11: the chapter must belong to the title of the library entry."""
    other_media = create_media(client, auth_headers, media_type="GAME")
    foreign_chapter = add_chapter(db, other_media["id"])

    posted = log(client, auth_headers, game["entry_id"], foreign_chapter, {"minutes": 5})
    read = client.get(base_url(game["entry_id"], foreign_chapter), headers=auth_headers)

    assert (posted.status_code, read.status_code) == (404, 404)
    assert progress_rows(db, game["entry_id"], foreign_chapter) == []
    assert "PLAYTIME_LOGGED" not in diary_actions(client, auth_headers)


@pytest.mark.parametrize("bad_id", ["0", "-5", str(2**31), "99999999999999999999"])
def test_ids_that_cannot_exist_return_404(client, auth_headers, game, bad_id):
    for url in (
        f"/library/{bad_id}/chapters/{game['chapter_id']}",
        f"/library/{game['entry_id']}/chapters/{bad_id}",
    ):
        assert client.get(url, headers=auth_headers).status_code == 404
        assert client.post(f"{url}/playtime", json={"minutes": 5}, headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- reading the progress (4.5)
def test_a_chapter_without_data_returns_no_rating_and_zero_minutes(client, auth_headers, game, db):
    response = client.get(base_url(game["entry_id"], game["chapter_id"]), headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "library_entry_id": game["entry_id"],
        "chapter_id": game["chapter_id"],
        "rating": None,
        "playtime_minutes": 0,
        "updated_at": None,
        "choice": None,
        "decided_at": None,
        "decisions": [],
    }
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []  # reading creates nothing


def test_the_progress_shows_rating_and_total_together(client, auth_headers, game):
    url = base_url(game["entry_id"], game["chapter_id"])
    client.put(f"{url}/rating", json={"rating": 3}, headers=auth_headers)
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 25})

    body = client.get(url, headers=auth_headers).json()

    assert (body["rating"], body["playtime_minutes"]) == (3, 25)
    assert body["updated_at"] is not None


# ---------------------------------------------------------------- diary (US-07)
def test_every_entry_is_recorded_in_the_diary(client, auth_headers, game):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 90})
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 30})

    events = [e for e in client.get("/diary", headers=auth_headers).json() if e["action"] == "PLAYTIME_LOGGED"]

    assert sorted(e["details"] for e in events) == ["Logged 30 min on chapter 1", "Logged 90 min on chapter 1"]
    assert {e["media_item_id"] for e in events} == {game["media_id"]}


def test_an_episode_entry_says_episode_in_the_diary(client, auth_headers, db):
    series = create_media(client, auth_headers, media_type="SERIES")
    entry = add_to_library(client, auth_headers, series["id"])
    episode_id = add_episode(db, series["id"], number=4)

    log(client, auth_headers, entry["id"], episode_id, {"minutes": 45})

    events = [e for e in client.get("/diary", headers=auth_headers).json() if e["action"] == "PLAYTIME_LOGGED"]
    assert [e["details"] for e in events] == ["Logged 45 min on episode 4"]


# ---------------------------------------------------------------- updated_at
def test_updated_at_changes_when_playtime_is_logged(client, auth_headers, game):
    url = base_url(game["entry_id"], game["chapter_id"])
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})
    first = datetime.fromisoformat(client.get(url, headers=auth_headers).json()["updated_at"])

    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})
    second = datetime.fromisoformat(client.get(url, headers=auth_headers).json()["updated_at"])

    assert second > first


# ---------------------------------------------------------------- concurrency and errors
def test_many_entries_at_the_same_time_are_all_counted(client, auth_headers, game, db):
    """Real concurrency, starting with no progress row. Every request succeeds, no minute is
    lost (the database adds the minutes) and there is one progress row."""
    workers = 8
    barrier = threading.Barrier(workers)
    codes = []

    def worker():
        barrier.wait()
        codes.append(log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10}).status_code)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert codes == [201] * workers
    assert len(progress_rows(db, game["entry_id"], game["chapter_id"])) == 1
    assert len(log_rows(db, game["entry_id"], game["chapter_id"])) == workers
    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == workers * 10
    assert diary_actions(client, auth_headers).count("PLAYTIME_LOGGED") == workers


def _service_user(db, game):
    return db.get(User, db.get(UserLibrary, game["entry_id"]).user_id)


def test_the_race_on_the_first_entry_is_caught_by_the_constraint(client, auth_headers, game, db):
    """Two first requests can pass the pre-check together. The unique constraint stops the second
    INSERT, and the service adds the entry to the row that exists."""
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 20})
    user = _service_user(db, game)

    # call 1 = library entry, call 2 = chapter, call 3 = "is there a progress row?" (hidden)
    entry, progress = chapter_service.log_playtime(
        HiddenPreCheck(db, hide_call=3), user, game["entry_id"], game["chapter_id"], 15
    )

    assert progress.playtime_minutes == 35
    assert len(progress_rows(db, game["entry_id"], game["chapter_id"])) == 1
    assert total(client, auth_headers, game["entry_id"], game["chapter_id"]) == 35


def test_a_database_error_is_raised_again_and_saves_nothing(client, auth_headers, game, db, monkeypatch):
    """Only the race on the unique constraint is handled. A foreign key error is not hidden."""
    user = _service_user(db, game)
    entry = db.get(UserLibrary, game["entry_id"])
    vanished = SimpleNamespace(id=99999999, number=1, kind=ChapterKind.CHAPTER)
    monkeypatch.setattr(chapter_service, "get_chapter_context", lambda *args: (entry, vanished))
    logs_before = db.query(PlaytimeLog).count()

    with pytest.raises(IntegrityError):
        chapter_service.log_playtime(db, user, game["entry_id"], vanished.id, 30)

    assert "PLAYTIME_LOGGED" not in diary_actions(client, auth_headers)
    assert db.query(PlaytimeLog).count() == logs_before
    assert db.query(User).count() > 0  # the session still works after the rollback


def test_a_failed_entry_does_not_keep_the_new_progress_row(client, auth_headers, game, db, monkeypatch):
    """The progress row, the entry, the total and the event are one transaction. If the entry
    cannot be saved, the row that this request created is not left behind."""
    user = _service_user(db, game)
    monkeypatch.setattr(chapter_service, "record_event", lambda *args, **kwargs: 1 / 0)

    with pytest.raises(ZeroDivisionError):
        chapter_service.log_playtime(db, user, game["entry_id"], game["chapter_id"], 30)
    db.rollback()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
    assert log_rows(db, game["entry_id"], game["chapter_id"]) == []


# ---------------------------------------------------------------- database rules (BR-12)
def _progress(game):
    progress = ChapterProgress(
        library_entry_id=game["entry_id"], chapter_id=game["chapter_id"], media_item_id=game["media_id"]
    )
    return progress


def test_the_database_rejects_an_entry_below_one_minute(client, auth_headers, game, db):
    progress = _progress(game)
    db.add(progress)
    db.commit()

    for bad in (0, -5):
        db.add(PlaytimeLog(chapter_progress_id=progress.id, minutes=bad))
        with pytest.raises(IntegrityError) as error:
            db.commit()
        db.rollback()
        assert "chk_playtime_minutes" in str(error.value)


def test_the_database_fills_logged_at_for_an_insert_outside_the_orm(client, auth_headers, game, db):
    progress = _progress(game)
    db.add(progress)
    db.commit()

    db.execute(
        text("INSERT INTO playtime_logs (chapter_progress_id, minutes) VALUES (:id, 5)"),
        {"id": progress.id},
    )
    db.commit()

    assert log_rows(db, game["entry_id"], game["chapter_id"])[0].logged_at is not None


def test_the_orm_relationships_connect_progress_and_entries(client, auth_headers, game, db):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 20})
    db.expire_all()

    progress = progress_rows(db, game["entry_id"], game["chapter_id"])[0]

    assert [entry.minutes for entry in progress.playtime_logs] == [10, 20]
    assert all(entry.progress.id == progress.id for entry in progress.playtime_logs)


def test_deleting_a_chapter_deletes_its_progress_and_entries(client, auth_headers, game, db):
    """The cascade runs chapter, then progress, then playtime entries."""
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})
    log_ids = [row.id for row in log_rows(db, game["entry_id"], game["chapter_id"])]
    assert log_ids

    db.query(Chapter).filter(Chapter.id == game["chapter_id"]).delete()
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
    assert db.query(PlaytimeLog).filter(PlaytimeLog.id.in_(log_ids)).count() == 0


def test_deleting_a_library_entry_through_the_orm_deletes_its_entries(client, auth_headers, game, db):
    log(client, auth_headers, game["entry_id"], game["chapter_id"], {"minutes": 10})
    log_ids = [row.id for row in log_rows(db, game["entry_id"], game["chapter_id"])]
    assert log_ids

    db.delete(db.get(UserLibrary, game["entry_id"]))
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
    assert db.query(PlaytimeLog).filter(PlaytimeLog.id.in_(log_ids)).count() == 0
