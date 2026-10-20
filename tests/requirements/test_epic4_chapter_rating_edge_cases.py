"""Edge cases for rating a chapter or episode (US-10, BR-10, BR-11, US-07, NFR-02).

The chapters are saved in the database directly (see epic4_helpers.py).
"""
import threading
from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.entities import (
    Chapter,
    ChapterKind,
    ChapterProgress,
    MediaItem,
    User,
    UserLibrary,
)
from app.schemas.chapter import ChapterRatingResponse
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
def _progress(game, rating, **overrides):
    """A ChapterProgress for the fixture game. Overrides replace single columns."""
    values = {
        "library_entry_id": game["entry_id"],
        "chapter_id": game["chapter_id"],
        "media_item_id": game["media_id"],
        "rating": rating,
    }
    values.update(overrides)
    return ChapterProgress(**values)


def rating_url(entry_id, chapter_id):
    return f"/library/{entry_id}/chapters/{chapter_id}/rating"


def rate(client, headers, entry_id, chapter_id, body):
    return client.put(rating_url(entry_id, chapter_id), json=body, headers=headers)


def progress_rows(db, entry_id, chapter_id):
    db.expire_all()
    return (
        db.query(ChapterProgress)
        .filter(ChapterProgress.library_entry_id == entry_id, ChapterProgress.chapter_id == chapter_id)
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
@pytest.mark.parametrize("value", [1, 2, 3, 4, 5])
def test_every_rating_from_1_to_5_is_accepted(client, auth_headers, game, value):
    """US-10 and BR-10: the whole range is valid, including both ends."""
    response = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": value})

    assert response.status_code == 200
    assert response.json()["rating"] == value


def test_the_answer_has_the_documented_fields_only(client, auth_headers, game):
    """US-10: the answer shows the rating and where it belongs, and no internal columns."""
    body = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4}).json()

    assert set(body) == {"library_entry_id", "chapter_id", "rating", "updated_at"}
    assert body["library_entry_id"] == game["entry_id"]
    assert body["chapter_id"] == game["chapter_id"]
    assert body["rating"] == 4
    assert body["updated_at"] is not None


def test_the_rating_is_saved_in_the_database(client, auth_headers, game, db):
    """US-10: the rating is stored once, in one progress row."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})

    rows = progress_rows(db, game["entry_id"], game["chapter_id"])
    assert [(row.rating, row.playtime_minutes) for row in rows] == [(4, 0)]


def test_a_new_rating_replaces_the_old_one(client, auth_headers, game, db):
    """US-10: rating again changes the rating. It never adds a second row."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 2})
    response = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 5})

    assert response.json()["rating"] == 5
    rows = progress_rows(db, game["entry_id"], game["chapter_id"])
    assert [row.rating for row in rows] == [5]


def test_the_same_rating_can_be_sent_again(client, auth_headers, game):
    """US-10: PUT can be repeated with the same body and gives the same answer."""
    first = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})
    second = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})

    assert (first.status_code, second.status_code) == (200, 200)
    assert second.json()["rating"] == 3


def test_chapters_of_one_title_are_rated_separately(client, auth_headers, game):
    """US-10: each chapter keeps its own rating, which is the point of comparing the parts."""
    first = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 5})
    second = rate(client, auth_headers, game["entry_id"], game["second_chapter_id"], {"rating": 2})

    assert (first.json()["rating"], second.json()["rating"]) == (5, 2)


def test_an_episode_of_a_series_can_be_rated(client, auth_headers, db):
    """US-10: the story speaks of a chapter or an episode, so an episode works too."""
    series = create_media(client, auth_headers, media_type="SERIES")
    entry = add_to_library(client, auth_headers, series["id"], status="IN_PROGRESS")
    episode_id = add_episode(db, series["id"])

    response = rate(client, auth_headers, entry["id"], episode_id, {"rating": 3})

    assert response.status_code == 200
    assert response.json()["rating"] == 3


def test_the_library_rating_of_the_title_is_not_touched(client, auth_headers, db):
    """US-10: the chapter rating (1 to 5) and the title rating (1 to 10) are separate."""
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], rating=9)
    chapter_id = add_chapter(db, media["id"])

    rate(client, auth_headers, entry["id"], chapter_id, {"rating": 2})

    library = client.get("/library", headers=auth_headers).json()
    assert [item["rating"] for item in library if item["id"] == entry["id"]] == [9]


# ---------------------------------------------------------------- invalid ratings (BR-10)
@pytest.mark.parametrize(
    "body",
    [
        {"rating": 0},
        {"rating": 6},
        {"rating": -1},
        {"rating": 10},
        {"rating": 4.5},
        {"rating": 4.0},
        {"rating": "4"},
        {"rating": True},
        {"rating": None},
        {"rating": [4]},
        {},
    ],
)
def test_invalid_ratings_return_422(client, auth_headers, game, db, body):
    """US-10 and BR-10: only a whole JSON number from 1 to 5 is a rating."""
    response = rate(client, auth_headers, game["entry_id"], game["chapter_id"], body)

    assert response.status_code == 422
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_an_invalid_rating_keeps_the_old_one(client, auth_headers, game, db):
    """US-10: a rejected request changes nothing."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 6})

    assert [row.rating for row in progress_rows(db, game["entry_id"], game["chapter_id"])] == [4]


def test_a_nan_rating_returns_422_not_500(client, auth_headers, game):
    """US-10: NaN is not valid JSON. It must be a validation error, never a server error."""
    response = client.put(
        rating_url(game["entry_id"], game["chapter_id"]),
        content='{"rating": NaN}',
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_a_body_that_is_not_json_returns_422(client, auth_headers, game):
    response = client.put(
        rating_url(game["entry_id"], game["chapter_id"]),
        content="not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- access (BR-11, NFR-02)
def test_rating_needs_a_token(client, game):
    """NFR-02: a request without a token returns 401."""
    response = client.put(rating_url(game["entry_id"], game["chapter_id"]), json={"rating": 4})

    assert response.status_code == 401


def test_a_bad_token_returns_401(client, game):
    response = client.put(
        rating_url(game["entry_id"], game["chapter_id"]),
        json={"rating": 4},
        headers={"Authorization": "Bearer not-a-token"},
    )

    assert response.status_code == 401


def test_the_library_entry_of_another_user_returns_404(client, game, db):
    """BR-11: a user cannot rate chapters through the entry of someone else."""
    other = register_and_login(client, new_credentials())

    response = rate(client, other, game["entry_id"], game["chapter_id"], {"rating": 4})

    assert response.status_code == 404
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_the_answer_is_the_same_for_an_entry_that_does_not_exist(client, auth_headers, game):
    """BR-11: the 404 of another user's entry and of a missing entry look the same."""
    other = register_and_login(client, new_credentials())

    theirs = rate(client, other, game["entry_id"], game["chapter_id"], {"rating": 4})
    missing = rate(client, other, 99999999, game["chapter_id"], {"rating": 4})

    assert (theirs.status_code, theirs.json()) == (missing.status_code, missing.json())


def test_a_chapter_that_does_not_exist_returns_404(client, auth_headers, game):
    response = rate(client, auth_headers, game["entry_id"], 99999999, {"rating": 4})

    assert response.status_code == 404


def test_a_chapter_of_another_title_returns_404(client, auth_headers, game, db):
    """BR-11: the chapter must belong to the title of the library entry."""
    other_media = create_media(client, auth_headers, media_type="GAME")
    foreign_chapter = add_chapter(db, other_media["id"])

    response = rate(client, auth_headers, game["entry_id"], foreign_chapter, {"rating": 4})

    assert response.status_code == 404
    assert progress_rows(db, game["entry_id"], foreign_chapter) == []
    assert "CHAPTER_RATED" not in diary_actions(client, auth_headers)


@pytest.mark.parametrize("bad_id", ["0", "-5", str(2**31), "99999999999999999999"])
def test_ids_that_cannot_exist_return_404(client, auth_headers, game, bad_id):
    """US-10: an id that cannot exist (zero, negative, too large) is unknown, never a 500."""
    for url in (
        f"/library/{bad_id}/chapters/{game['chapter_id']}/rating",
        f"/library/{game['entry_id']}/chapters/{bad_id}/rating",
    ):
        assert client.put(url, json={"rating": 4}, headers=auth_headers).status_code == 404


def test_a_text_id_returns_422(client, auth_headers, game):
    response = client.put(f"/library/abc/chapters/{game['chapter_id']}/rating", json={"rating": 4}, headers=auth_headers)

    assert response.status_code == 422


def test_two_users_rate_the_same_chapter_independently(client, auth_headers, game, db):
    """US-10: the progress belongs to the library entry, so users do not overwrite each other."""
    other = register_and_login(client, new_credentials())
    other_entry = add_to_library(client, other, game["media_id"])

    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 5})
    rate(client, other, other_entry["id"], game["chapter_id"], {"rating": 1})

    mine = [r.rating for r in progress_rows(db, game["entry_id"], game["chapter_id"])]
    theirs = [r.rating for r in progress_rows(db, other_entry["id"], game["chapter_id"])]
    assert (mine, theirs) == ([5], [1])


# ---------------------------------------------------------------- diary (US-07)
def test_rating_a_chapter_is_recorded_in_the_diary(client, auth_headers, game):
    """US-07: a chapter rating is a CHAPTER_RATED event for the title."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})

    events = [e for e in client.get("/diary", headers=auth_headers).json() if e["action"] == "CHAPTER_RATED"]
    assert len(events) == 1
    assert events[0]["media_item_id"] == game["media_id"]
    assert events[0]["details"] == "Rated chapter 1 as 4"


def test_an_episode_rating_says_episode_in_the_diary(client, auth_headers, db):
    series = create_media(client, auth_headers, media_type="SERIES")
    entry = add_to_library(client, auth_headers, series["id"])
    episode_id = add_episode(db, series["id"], number=7)

    rate(client, auth_headers, entry["id"], episode_id, {"rating": 2})

    events = [e for e in client.get("/diary", headers=auth_headers).json() if e["action"] == "CHAPTER_RATED"]
    assert [e["details"] for e in events] == ["Rated episode 7 as 2"]


def test_a_chapter_rating_is_not_a_title_rating_event(client, auth_headers, game):
    """US-07: RATED stays for the rating of the title, so the two kinds can be told apart."""
    before = diary_actions(client, auth_headers).count("RATED")

    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})

    assert diary_actions(client, auth_headers).count("RATED") == before


def test_the_same_rating_again_adds_no_event(client, auth_headers, game):
    """US-07: events are written for real changes only."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")

    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})

    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before


def test_a_changed_rating_adds_an_event(client, auth_headers, game):
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 4})
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")

    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 2})

    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before + 1


def test_a_rejected_rating_adds_no_event(client, auth_headers, game):
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")

    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 6})
    rate(client, auth_headers, 99999999, game["chapter_id"], {"rating": 4})

    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before


# ---------------------------------------------------------------- concurrency and database rules
def test_a_race_on_the_first_rating_is_caught_by_the_constraint(client, auth_headers, game, db):
    """US-10: two first ratings can pass the pre-check together. The unique constraint then
    stops the second INSERT. The service recognises that constraint, reads the row that exists
    and updates it."""
    first = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 2})
    user = _service_user(db, game)
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")

    # call 1 = library entry, call 2 = chapter, call 3 = "is there a progress row?" (hidden)
    progress = chapter_service.rate_chapter(
        HiddenPreCheck(db, hide_call=3), user, game["entry_id"], game["chapter_id"], 5
    )

    assert first.status_code == 200
    assert progress.rating == 5
    assert [row.rating for row in progress_rows(db, game["entry_id"], game["chapter_id"])] == [5]
    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before + 1


def test_the_database_rejects_a_rating_out_of_range(client, auth_headers, game, db):
    """BR-10: the check constraint is the last line of defence behind the API."""
    db.add(_progress(game, rating=6))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_the_database_allows_one_progress_row_per_entry_and_chapter(client, auth_headers, game, db):
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})
    db.add(_progress(game, rating=4))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_deleting_a_chapter_deletes_its_progress(client, auth_headers, game, db):
    """The ratings of users never point to a chapter that is gone."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})

    db.query(Chapter).filter(Chapter.id == game["chapter_id"]).delete()
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_deleting_a_title_deletes_the_progress_of_its_chapters(client, auth_headers, game, db):
    """Title, then library entry and chapters, then progress: the cascade reaches all of it."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})

    db.query(MediaItem).filter(MediaItem.id == game["media_id"]).delete(synchronize_session=False)
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


# ---------------------------------------------------------------- response model
def test_the_response_model_needs_a_rating_from_1_to_5():
    """A saved rating is always there, so the response model has no empty rating."""
    ok = {"library_entry_id": 1, "chapter_id": 2, "rating": 3, "updated_at": datetime(2026, 1, 1)}

    assert ChapterRatingResponse(**ok).rating == 3
    for bad in (None, 0, 6):
        with pytest.raises(ValidationError):
            ChapterRatingResponse(**{**ok, "rating": bad})
    with pytest.raises(ValidationError):
        ChapterRatingResponse(**{**ok, "updated_at": None})


# ---------------------------------------------------------------- updated_at
def _parse(value):
    return datetime.fromisoformat(value)


def test_updated_at_is_filled_after_the_first_rating(client, auth_headers, game, db):
    body = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3}).json()

    assert body["updated_at"] is not None
    assert progress_rows(db, game["entry_id"], game["chapter_id"])[0].updated_at is not None


def test_updated_at_changes_when_the_rating_changes(client, auth_headers, game):
    first = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3}).json()
    second = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 5}).json()

    assert _parse(second["updated_at"]) > _parse(first["updated_at"])


def test_updated_at_stays_when_the_same_rating_is_sent_again(client, auth_headers, game):
    first = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3}).json()
    second = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3}).json()

    assert second["updated_at"] == first["updated_at"]


def test_the_database_fills_updated_at_for_an_insert_outside_the_orm(client, auth_headers, game, db):
    """The server default covers raw SQL. The column is NOT NULL as well."""
    db.execute(
        text(
            "INSERT INTO chapter_progress (library_entry_id, chapter_id, media_item_id, rating) "
            "VALUES (:entry, :chapter, :media, 4)"
        ),
        {"entry": game["entry_id"], "chapter": game["chapter_id"], "media": game["media_id"]},
    )
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"])[0].updated_at is not None
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO chapter_progress (library_entry_id, chapter_id, media_item_id, updated_at) "
                "VALUES (:entry, :chapter, :media, NULL)"
            ),
            {"entry": game["entry_id"], "chapter": game["second_chapter_id"], "media": game["media_id"]},
        )
    db.rollback()


# ---------------------------------------------------------------- same title in the database (BR-11)
def test_the_database_rejects_a_chapter_of_another_title(client, auth_headers, game, db):
    """The foreign keys check the title. A service bug cannot save a chapter of another title."""
    other = create_media(client, auth_headers, media_type="GAME")
    foreign_chapter = add_chapter(db, other["id"])

    # The title of the entry is given, but the chapter belongs to another title
    db.add(_progress(game, rating=3, chapter_id=foreign_chapter))
    with pytest.raises(IntegrityError) as chapter_error:
        db.commit()
    db.rollback()
    assert "fk_progress_chapter_title" in str(chapter_error.value)

    # The title of the chapter is given, but the library entry belongs to another title
    db.add(_progress(game, rating=3, chapter_id=foreign_chapter, media_item_id=other["id"]))
    with pytest.raises(IntegrityError) as entry_error:
        db.commit()
    db.rollback()
    assert "fk_progress_entry_title" in str(entry_error.value)

    assert progress_rows(db, game["entry_id"], foreign_chapter) == []


def test_a_chapter_of_the_same_title_is_accepted_by_the_database(client, auth_headers, game, db):
    db.add(_progress(game, rating=3))
    db.commit()

    assert [row.rating for row in progress_rows(db, game["entry_id"], game["chapter_id"])] == [3]


# ---------------------------------------------------------------- only the expected race is caught
def _service_user(db, game):
    return db.get(User, db.get(UserLibrary, game["entry_id"]).user_id)


def test_a_foreign_key_error_is_raised_again_and_adds_no_event(
    client, auth_headers, game, db, monkeypatch
):
    """Only the race on the unique constraint is handled. Any other IntegrityError is raised."""
    user = _service_user(db, game)
    entry = db.get(UserLibrary, game["entry_id"])
    vanished = SimpleNamespace(id=99999999, number=1, kind=ChapterKind.CHAPTER)
    # The chapter is gone between the access check and the INSERT
    monkeypatch.setattr(chapter_service, "get_chapter_context", lambda *args: (entry, vanished))

    with pytest.raises(IntegrityError) as error:
        chapter_service.rate_chapter(db, user, game["entry_id"], vanished.id, 4)

    assert "fk_progress_chapter_title" in str(error.value)
    assert "CHAPTER_RATED" not in diary_actions(client, auth_headers)
    assert db.query(User).count() > 0  # the session still works after the rollback


def test_a_check_constraint_error_is_raised_again_and_adds_no_event(client, auth_headers, game, db):
    """The API never sends 6, but the service must not hide the database error if it does."""
    user = _service_user(db, game)

    with pytest.raises(IntegrityError) as error:
        chapter_service.rate_chapter(db, user, game["entry_id"], game["chapter_id"], 6)

    assert "chk_progress_rating" in str(error.value)
    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
    assert "CHAPTER_RATED" not in diary_actions(client, auth_headers)


@pytest.mark.parametrize(
    ("pgcode", "constraint", "expected"),
    [
        ("23505", "uq_progress_entry_chapter", True),  # the expected race
        ("23505", "uq_user_media_entry", False),  # another unique constraint
        ("23503", "fk_progress_chapter_title", False),  # a foreign key
        ("23514", "chk_progress_rating", False),  # a check constraint
        (None, None, False),  # a driver error without details
    ],
)
def test_only_the_progress_unique_violation_counts_as_the_race(pgcode, constraint, expected):
    original = SimpleNamespace(pgcode=pgcode, diag=SimpleNamespace(constraint_name=constraint))

    assert chapter_service._is_duplicate_progress(IntegrityError("INSERT", {}, original)) is expected


def test_a_real_unique_violation_has_the_details_the_service_reads(client, auth_headers, game, db):
    """The check works only if the driver really reports the code and the constraint name."""
    db.add(_progress(game, rating=3))
    db.commit()
    db.add(_progress(game, rating=4))

    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert chapter_service._is_duplicate_progress(error.value) is True


def test_the_race_adds_exactly_one_event_for_a_new_rating(client, auth_headers, game, db):
    """After the race the service finds the row. The same rating adds no event, a new one adds one."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 2})
    user = _service_user(db, game)
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")

    chapter_service.rate_chapter(HiddenPreCheck(db, hide_call=3), user, game["entry_id"], game["chapter_id"], 2)
    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before

    chapter_service.rate_chapter(HiddenPreCheck(db, hide_call=3), user, game["entry_id"], game["chapter_id"], 4)
    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before + 1


def test_many_first_ratings_at_the_same_time_leave_one_row(client, auth_headers, game, db):
    """Real concurrency: every request succeeds and there is one progress row at the end."""
    workers = 6
    barrier = threading.Barrier(workers)
    codes = []

    def worker(value):
        barrier.wait()
        response = rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": value})
        codes.append(response.status_code)

    threads = [threading.Thread(target=worker, args=(1 + index % 5,)) for index in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = progress_rows(db, game["entry_id"], game["chapter_id"])
    assert codes == [200] * workers
    assert len(rows) == 1
    assert rows[0].rating in range(1, 6)
    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") >= 1


def test_the_original_error_is_raised_if_the_row_of_the_race_cannot_be_found(
    client, auth_headers, game, db, monkeypatch
):
    """After a duplicate the service reads the row. If it is not there, the error is not hidden."""
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 2})
    user = _service_user(db, game)
    before = diary_actions(client, auth_headers).count("CHAPTER_RATED")
    monkeypatch.setattr(chapter_service, "_find_progress", lambda *args: None)

    with pytest.raises(IntegrityError):
        chapter_service.rate_chapter(db, user, game["entry_id"], game["chapter_id"], 4)

    assert diary_actions(client, auth_headers).count("CHAPTER_RATED") == before


# ---------------------------------------------------------------- ORM relationships
def test_the_orm_relationships_connect_progress_entry_and_chapter(client, auth_headers, game, db):
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})
    db.expire_all()

    progress = progress_rows(db, game["entry_id"], game["chapter_id"])[0]

    assert progress.library_entry.id == game["entry_id"]
    assert progress.chapter.id == game["chapter_id"]
    assert [row.rating for row in db.get(UserLibrary, game["entry_id"]).chapter_progress] == [3]
    assert [row.rating for row in db.get(Chapter, game["chapter_id"]).progress_entries] == [3]


def test_deleting_a_library_entry_through_the_orm_deletes_its_progress(client, auth_headers, game, db):
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})

    db.delete(db.get(UserLibrary, game["entry_id"]))
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []


def test_deleting_a_chapter_through_the_orm_deletes_its_progress(client, auth_headers, game, db):
    rate(client, auth_headers, game["entry_id"], game["chapter_id"], {"rating": 3})

    db.delete(db.get(Chapter, game["chapter_id"]))
    db.commit()

    assert progress_rows(db, game["entry_id"], game["chapter_id"]) == []
