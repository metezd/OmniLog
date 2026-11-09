"""Edge cases for recording branching decisions (US-12, BR-11, BR-13, US-07, NFR-02).

The chapters and decision points are saved in the database directly (see epic4_helpers.py).
"""
import threading
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.entities import (
    Chapter,
    ChapterProgress,
    DecisionOption,
    DecisionPoint,
    MediaItem,
    User,
    UserDecision,
    UserLibrary,
)
from app.services import chapter_service
from epic4_helpers import add_chapter, add_decision_point, diary_actions
from helpers import add_to_library, create_media, new_credentials, register_and_login


# ---------------------------------------------------------------- helpers
def base_url(entry_id, chapter_id):
    return f"/library/{entry_id}/chapters/{chapter_id}"


def decide(client, headers, entry_id, chapter_id, body):
    return client.put(f"{base_url(entry_id, chapter_id)}/decision", json=body, headers=headers)


def progress(client, headers, entry_id, chapter_id):
    return client.get(base_url(entry_id, chapter_id), headers=headers).json()


def decision_rows(db, entry_id, point_id=None):
    db.expire_all()
    query = db.query(UserDecision).filter(UserDecision.library_entry_id == entry_id)
    if point_id is not None:
        query = query.filter(UserDecision.decision_point_id == point_id)
    return query.order_by(UserDecision.id).all()


def option_ids(db, point_id):
    return {o.label: o.id for o in db.query(DecisionOption).filter(DecisionOption.decision_point_id == point_id)}


@pytest.fixture
def game(client, auth_headers, db):
    """A game in the library with a chapter that has one decision point (options A and B),
    and a second chapter without a decision point."""
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")
    chapter_id = add_chapter(db, media["id"], 1)
    return {
        "media_id": media["id"],
        "entry_id": entry["id"],
        "chapter_id": chapter_id,
        "point_id": add_decision_point(db, chapter_id, media["id"]),
        "plain_chapter_id": add_chapter(db, media["id"], 2),
    }


def new_row(game, **overrides):
    """A UserDecision for the fixture game with option A. Overrides replace single columns."""
    return UserDecision(
        **{
            "library_entry_id": game["entry_id"],
            "media_item_id": game["media_id"],
            "decision_point_id": game["point_id"],
            "option_id": None,
            **overrides,
        }
    )


# ---------------------------------------------------------------- happy path
def test_recording_a_choice_returns_it_with_its_place(client, auth_headers, game):
    response = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"library_entry_id", "chapter_id", "decision_point_id", "choice", "decided_at"}
    assert (body["library_entry_id"], body["chapter_id"]) == (game["entry_id"], game["chapter_id"])
    assert (body["decision_point_id"], body["choice"]) == (game["point_id"], "A")


def test_the_choice_is_returned_on_the_chapter(client, auth_headers, game):
    """US-12: my choice is stored and returned on the chapter."""
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    body = progress(client, auth_headers, game["entry_id"], game["chapter_id"])

    assert body["choice"] == "A"
    assert [(d["decision_point_id"], d["choice"]) for d in body["decisions"]] == [(game["point_id"], "A")]


def test_the_chapter_shows_when_the_choice_was_made(client, auth_headers, game):
    saved = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"}).json()

    body = progress(client, auth_headers, game["entry_id"], game["chapter_id"])

    assert set(body) == {
        "library_entry_id",
        "chapter_id",
        "rating",
        "playtime_minutes",
        "updated_at",
        "choice",
        "decided_at",
        "decisions",
    }
    assert body["decided_at"] is not None
    assert body["decided_at"] == saved["decided_at"] == body["decisions"][0]["decided_at"]


def test_the_time_on_the_chapter_follows_a_new_choice_and_not_the_same_choice(client, auth_headers, game):
    first = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"}).json()
    again = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"}).json()
    assert again["decided_at"] == first["decided_at"]  # the same choice changes nothing

    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B"})
    body = progress(client, auth_headers, game["entry_id"], game["chapter_id"])

    assert datetime.fromisoformat(body["decided_at"]) > datetime.fromisoformat(first["decided_at"])


def test_a_new_choice_replaces_the_old_one(client, auth_headers, game, db):
    """US-12 and BR-13: only the latest choice is kept, in one row."""
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    response = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B"})

    assert response.json()["choice"] == "B"
    assert progress(client, auth_headers, game["entry_id"], game["chapter_id"])["choice"] == "B"
    assert len(decision_rows(db, game["entry_id"], game["point_id"])) == 1


def test_the_same_choice_can_be_sent_again(client, auth_headers, game, db):
    first = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    second = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    assert (first.status_code, second.status_code) == (200, 200)
    assert second.json()["decided_at"] == first.json()["decided_at"]
    assert len(decision_rows(db, game["entry_id"], game["point_id"])) == 1


def test_decided_at_changes_with_a_new_choice(client, auth_headers, game):
    first = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"}).json()
    second = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B"}).json()

    assert datetime.fromisoformat(second["decided_at"]) > datetime.fromisoformat(first["decided_at"])


def test_a_choice_creates_no_progress_row(client, auth_headers, game, db):
    """A decision does not need a rating or playtime, and it does not create them."""
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    body = progress(client, auth_headers, game["entry_id"], game["chapter_id"])

    assert (body["rating"], body["playtime_minutes"], body["choice"]) == (None, 0, "A")
    db.expire_all()
    assert db.query(ChapterProgress).filter(ChapterProgress.library_entry_id == game["entry_id"]).count() == 0


def test_a_chapter_without_a_choice_returns_none(client, auth_headers, game):
    body = progress(client, auth_headers, game["entry_id"], game["chapter_id"])

    assert (body["choice"], body["decided_at"], body["decisions"]) == (None, None, [])


def test_two_users_choose_independently(client, auth_headers, game):
    other = register_and_login(client, new_credentials())
    other_entry = add_to_library(client, other, game["media_id"])

    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    decide(client, other, other_entry["id"], game["chapter_id"], {"choice": "B"})

    assert progress(client, auth_headers, game["entry_id"], game["chapter_id"])["choice"] == "A"
    assert progress(client, other, other_entry["id"], game["chapter_id"])["choice"] == "B"


# ---------------------------------------------------------------- choices that are not allowed
def test_a_choice_that_is_not_an_option_returns_422_and_names_the_options(client, auth_headers, game, db):
    response = decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "Z"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Choice must be one of: A, B"
    assert decision_rows(db, game["entry_id"]) == []


@pytest.mark.parametrize(
    "body",
    [
        {"choice": "a"},  # labels are exact
        {"choice": " A"},
        {"choice": "A "},
        {"choice": ""},
        {"choice": "A" * 11},
        {"choice": None},
        {"choice": 1},
        {"choice": True},
        {"choice": ["A"]},
        {"choice": {"label": "A"}},
        {},
    ],
)
def test_invalid_choices_return_422(client, auth_headers, game, db, body):
    response = decide(client, auth_headers, game["entry_id"], game["chapter_id"], body)

    assert response.status_code == 422
    assert decision_rows(db, game["entry_id"]) == []


def test_a_rejected_choice_keeps_the_old_one(client, auth_headers, game):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "Z"})

    assert progress(client, auth_headers, game["entry_id"], game["chapter_id"])["choice"] == "A"


def test_a_body_that_is_not_json_returns_422(client, auth_headers, game):
    response = client.put(
        f"{base_url(game['entry_id'], game['chapter_id'])}/decision",
        content="not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_a_chapter_without_a_decision_point_returns_422(client, auth_headers, game, db):
    response = decide(client, auth_headers, game["entry_id"], game["plain_chapter_id"], {"choice": "A"})

    assert response.status_code == 422
    assert response.json()["detail"] == "This chapter has no decision point"
    assert decision_rows(db, game["entry_id"]) == []


def test_a_decision_point_without_options_returns_422(client, auth_headers, game, db):
    empty_chapter = add_chapter(db, game["media_id"], 3)
    add_decision_point(db, empty_chapter, game["media_id"], labels=())

    response = decide(client, auth_headers, game["entry_id"], empty_chapter, {"choice": "A"})

    assert response.status_code == 422
    assert response.json()["detail"] == "This decision point has no options"


# ---------------------------------------------------------------- several decision points
@pytest.fixture
def two_points(game, db):
    """The first chapter gets a second decision point with the options X and Y."""
    game["second_point_id"] = add_decision_point(
        db, game["chapter_id"], game["media_id"], labels=("X", "Y"), position=2, prompt="Then what?"
    )
    return game


def test_several_decision_points_need_an_id(client, auth_headers, two_points):
    response = decide(client, auth_headers, two_points["entry_id"], two_points["chapter_id"], {"choice": "A"})

    assert response.status_code == 422
    assert "decision_point_id" in response.json()["detail"]


def test_each_decision_point_keeps_its_own_choice(client, auth_headers, two_points, db):
    entry, chapter = two_points["entry_id"], two_points["chapter_id"]
    decide(client, auth_headers, entry, chapter, {"choice": "Y", "decision_point_id": two_points["second_point_id"]})
    decide(client, auth_headers, entry, chapter, {"choice": "B", "decision_point_id": two_points["point_id"]})
    decide(client, auth_headers, entry, chapter, {"choice": "X", "decision_point_id": two_points["second_point_id"]})

    body = progress(client, auth_headers, entry, chapter)

    # ordered by the position of the decision point, and `choice` is the first answered one
    assert [(d["decision_point_id"], d["choice"]) for d in body["decisions"]] == [
        (two_points["point_id"], "B"),
        (two_points["second_point_id"], "X"),
    ]
    assert body["choice"] == "B"
    assert body["decided_at"] == body["decisions"][0]["decided_at"]  # the time of `choice`
    assert len(decision_rows(db, entry)) == 2


def test_a_label_of_another_decision_point_returns_422(client, auth_headers, two_points):
    """BR-13: the option must belong to the decision point that is answered."""
    response = decide(
        client,
        auth_headers,
        two_points["entry_id"],
        two_points["chapter_id"],
        {"choice": "A", "decision_point_id": two_points["second_point_id"]},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Choice must be one of: X, Y"


def test_a_decision_point_of_another_chapter_returns_404(client, auth_headers, game, db):
    other_chapter = add_chapter(db, game["media_id"], 3)
    other_point = add_decision_point(db, other_chapter, game["media_id"])

    response = decide(
        client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A", "decision_point_id": other_point}
    )

    assert response.status_code == 404
    assert decision_rows(db, game["entry_id"]) == []


def test_a_decision_point_that_does_not_exist_returns_404(client, auth_headers, game):
    response = decide(
        client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A", "decision_point_id": 99999999}
    )

    assert response.status_code == 404


@pytest.mark.parametrize("bad", [0, -1, "x", 1.5, True, 2**31])
def test_an_invalid_decision_point_id_returns_422(client, auth_headers, game, bad):
    response = decide(
        client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A", "decision_point_id": bad}
    )

    assert response.status_code == 422


def test_the_right_decision_point_id_works_for_a_single_point(client, auth_headers, game):
    response = decide(
        client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B", "decision_point_id": game["point_id"]}
    )

    assert response.status_code == 200
    assert response.json()["choice"] == "B"


# ---------------------------------------------------------------- access (BR-11, NFR-02)
def test_recording_needs_a_token(client, game):
    response = client.put(f"{base_url(game['entry_id'], game['chapter_id'])}/decision", json={"choice": "A"})

    assert response.status_code == 401


def test_the_library_entry_of_another_user_returns_404(client, game, db):
    other = register_and_login(client, new_credentials())

    response = decide(client, other, game["entry_id"], game["chapter_id"], {"choice": "A"})

    assert response.status_code == 404
    assert decision_rows(db, game["entry_id"]) == []


def test_a_chapter_that_does_not_exist_returns_404(client, auth_headers, game):
    assert decide(client, auth_headers, game["entry_id"], 99999999, {"choice": "A"}).status_code == 404


def test_a_chapter_of_another_title_returns_404(client, auth_headers, game, db):
    """BR-11: the chapter must belong to the title of the library entry."""
    other_media = create_media(client, auth_headers, media_type="GAME")
    foreign_chapter = add_chapter(db, other_media["id"])
    add_decision_point(db, foreign_chapter, other_media["id"])

    response = decide(client, auth_headers, game["entry_id"], foreign_chapter, {"choice": "A"})

    assert response.status_code == 404
    assert decision_rows(db, game["entry_id"]) == []
    assert "DECISION_RECORDED" not in diary_actions(client, auth_headers)


@pytest.mark.parametrize("bad_id", ["0", "-5", str(2**31), "99999999999999999999"])
def test_ids_that_cannot_exist_return_404(client, auth_headers, game, bad_id):
    for url in (
        f"/library/{bad_id}/chapters/{game['chapter_id']}/decision",
        f"/library/{game['entry_id']}/chapters/{bad_id}/decision",
    ):
        assert client.put(url, json={"choice": "A"}, headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- diary (US-07)
def test_a_choice_is_recorded_in_the_diary(client, auth_headers, game):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    events = [e for e in client.get("/diary", headers=auth_headers).json() if e["action"] == "DECISION_RECORDED"]

    assert [e["details"] for e in events] == ["Chose A in chapter 1"]
    assert events[0]["media_item_id"] == game["media_id"]


def test_the_same_choice_adds_no_event_and_a_new_one_adds_one(client, auth_headers, game):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    before = diary_actions(client, auth_headers).count("DECISION_RECORDED")

    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    assert diary_actions(client, auth_headers).count("DECISION_RECORDED") == before

    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B"})
    assert diary_actions(client, auth_headers).count("DECISION_RECORDED") == before + 1


def test_a_rejected_choice_adds_no_event(client, auth_headers, game):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "Z"})
    decide(client, auth_headers, game["entry_id"], game["plain_chapter_id"], {"choice": "A"})

    assert "DECISION_RECORDED" not in diary_actions(client, auth_headers)


# ---------------------------------------------------------------- concurrency and errors
def _service_user(db, game):
    return db.get(User, db.get(UserLibrary, game["entry_id"]).user_id)


def test_many_first_choices_at_the_same_time_leave_one_row(client, auth_headers, game, db):
    """Real concurrency. Every request succeeds and there is one decision at the end."""
    workers = 6
    barrier = threading.Barrier(workers)
    codes = []

    def worker(label):
        barrier.wait()
        codes.append(decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": label}).status_code)

    threads = [threading.Thread(target=worker, args=("AB"[index % 2],)) for index in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert codes == [200] * workers
    rows = decision_rows(db, game["entry_id"], game["point_id"])
    assert len(rows) == 1
    assert rows[0].option_id in option_ids(db, game["point_id"]).values()


def test_a_second_first_choice_replaces_the_one_that_won_the_race(client, auth_headers, game, db, monkeypatch):
    """The service sees no decision, but another request saved one a moment before. ON CONFLICT
    replaces it, so there is no error and one row."""
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    user = _service_user(db, game)
    real_find = chapter_service._find_decision
    calls = []

    def blind_once(*args):
        calls.append(1)
        return None if len(calls) == 1 else real_find(*args)

    monkeypatch.setattr(chapter_service, "_find_decision", blind_once)

    point, option, decision = chapter_service.record_decision(db, user, game["entry_id"], game["chapter_id"], "B")

    assert option.label == "B"
    assert decision.option_id == option_ids(db, game["point_id"])["B"]
    assert len(decision_rows(db, game["entry_id"], game["point_id"])) == 1


def test_a_database_error_is_raised_again_and_saves_nothing(client, auth_headers, game, db, monkeypatch):
    """A foreign key error is not hidden, and the session works after it."""
    user = _service_user(db, game)
    vanished = SimpleNamespace(id=99999999, options=[SimpleNamespace(id=1, label="A")])
    monkeypatch.setattr(chapter_service, "_resolve_decision_point", lambda *args: vanished)

    with pytest.raises(IntegrityError):
        chapter_service.record_decision(db, user, game["entry_id"], game["chapter_id"], "A")

    assert "DECISION_RECORDED" not in diary_actions(client, auth_headers)
    assert decision_rows(db, game["entry_id"]) == []


# ---------------------------------------------------------------- database rules (BR-11, BR-13)
def test_the_database_rejects_an_option_of_another_decision_point(client, auth_headers, game, db):
    """BR-13: the option must belong to the decision point."""
    other_point = add_decision_point(db, game["chapter_id"], game["media_id"], position=2)

    db.add(new_row(game, option_id=option_ids(db, other_point)["A"]))
    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "fk_decision_option_point" in str(error.value)


def test_the_database_rejects_a_library_entry_of_another_title(client, auth_headers, game, db):
    """BR-11: the library entry and the decision point must belong to the same title."""
    other_media = create_media(client, auth_headers, media_type="GAME")
    other_entry = add_to_library(client, auth_headers, other_media["id"])
    option = option_ids(db, game["point_id"])["A"]

    # the title of the decision point is given, but the library entry belongs to another title
    db.add(new_row(game, library_entry_id=other_entry["id"], option_id=option))
    with pytest.raises(IntegrityError) as entry_error:
        db.commit()
    db.rollback()
    assert "fk_decision_entry_title" in str(entry_error.value)

    # the title of the library entry is given, but the decision point belongs to another title
    db.add(new_row(game, library_entry_id=other_entry["id"], media_item_id=other_media["id"], option_id=option))
    with pytest.raises(IntegrityError) as point_error:
        db.commit()
    db.rollback()
    assert "fk_decision_point_title" in str(point_error.value)


def test_the_database_rejects_a_decision_point_with_the_title_of_another_chapter(client, auth_headers, game, db):
    other_media = create_media(client, auth_headers, media_type="GAME")

    db.add(DecisionPoint(chapter_id=game["chapter_id"], media_item_id=other_media["id"], prompt="Bad"))
    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "fk_decision_point_chapter_title" in str(error.value)


def test_the_database_allows_one_decision_per_entry_and_point(client, auth_headers, game, db):
    option = option_ids(db, game["point_id"])["A"]
    db.add(new_row(game, option_id=option))
    db.commit()

    db.add(new_row(game, option_id=option))
    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "uq_user_decision_entry_point" in str(error.value)


def test_the_database_rejects_a_label_twice_in_one_decision_point(client, auth_headers, game, db):
    db.add(DecisionOption(decision_point_id=game["point_id"], label="A", text="again"))

    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "uq_option_point_label" in str(error.value)


def test_the_database_rejects_a_position_below_one(client, auth_headers, game, db):
    db.add(DecisionPoint(chapter_id=game["chapter_id"], media_item_id=game["media_id"], prompt="x", position=0))

    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "chk_decision_point_position" in str(error.value)


def test_the_orm_relationships_connect_chapter_points_and_options(client, auth_headers, game, db):
    db.expire_all()
    chapter = db.get(Chapter, game["chapter_id"])

    assert [point.id for point in chapter.decision_points] == [game["point_id"]]
    assert chapter.decision_points[0].chapter.id == chapter.id
    assert [option.label for option in chapter.decision_points[0].options] == ["A", "B"]
    assert chapter.decision_points[0].options[0].decision_point.id == game["point_id"]


def _remaining(db, game):
    """How many of the points, options and decisions of the fixture game are left."""
    db.expire_all()
    return (
        db.query(DecisionPoint).filter(DecisionPoint.id == game["point_id"]).count(),
        db.query(DecisionOption).filter(DecisionOption.decision_point_id == game["point_id"]).count(),
        db.query(UserDecision).filter(UserDecision.decision_point_id == game["point_id"]).count(),
    )


def test_deleting_a_chapter_deletes_its_points_options_and_decisions(client, auth_headers, game, db):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})
    assert _remaining(db, game) == (1, 2, 1)

    db.query(Chapter).filter(Chapter.id == game["chapter_id"]).delete()
    db.commit()

    assert _remaining(db, game) == (0, 0, 0)


def test_deleting_a_library_entry_deletes_its_decisions_only(client, auth_headers, game, db):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "A"})

    db.delete(db.get(UserLibrary, game["entry_id"]))
    db.commit()

    assert _remaining(db, game) == (1, 2, 0)  # the decision point and its options stay


def test_deleting_a_title_deletes_everything_of_the_decisions(client, auth_headers, game, db):
    decide(client, auth_headers, game["entry_id"], game["chapter_id"], {"choice": "B"})

    db.query(MediaItem).filter(MediaItem.id == game["media_id"]).delete(synchronize_session=False)
    db.commit()

    assert _remaining(db, game) == (0, 0, 0)
