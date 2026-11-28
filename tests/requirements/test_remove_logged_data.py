"""A user can take back what they logged: a review, a chapter rating, the newest playtime entry
and a choice (US-10, US-11, US-12, US-14, #427).

Before, the only way out was to remove the whole title from the library, which deleted every
rating, playtime entry, choice and the review of it.
"""
import pytest

from app.models.entities import DiaryEntry
from epic4_helpers import add_chapter, add_decision_point
from helpers import add_to_library, create_media, new_credentials, register_and_login


@pytest.fixture
def game(client, auth_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    chapter = add_chapter(db, media["id"], 1)
    first = add_decision_point(db, chapter, media["id"], labels=("A", "B"), position=1)
    entry = add_to_library(client, auth_headers, media["id"])
    return {"media": media, "entry": entry, "chapter": chapter, "point": first, "db": db}


def _chapter(game):
    return f"/library/{game['entry']['id']}/chapters/{game['chapter']}"


def _last_action(db, media_id):
    db.expire_all()
    return (
        db.query(DiaryEntry.action)
        .filter(DiaryEntry.media_item_id == media_id)
        .order_by(DiaryEntry.id.desc())
        .first()[0]
    )


# ---------------------------------------------------------------- review
def test_a_review_can_be_removed(client, auth_headers, game):
    url = f"/library/{game['entry']['id']}/review"
    client.post(url, json={"text": "It has a twist."}, headers=auth_headers)

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404
    assert _last_action(game["db"], game["media"]["id"]) == "REVIEW_REMOVED"


def test_removing_a_review_that_does_not_exist_is_404(client, auth_headers, game):
    assert client.delete(f"/library/{game['entry']['id']}/review", headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- chapter rating
def test_a_chapter_rating_can_be_removed_and_the_playtime_stays(client, auth_headers, game):
    client.put(f"{_chapter(game)}/rating", json={"rating": 4}, headers=auth_headers)
    client.post(f"{_chapter(game)}/playtime", json={"minutes": 30}, headers=auth_headers)

    response = client.delete(f"{_chapter(game)}/rating", headers=auth_headers)

    progress = client.get(_chapter(game), headers=auth_headers).json()
    assert response.status_code == 204
    assert progress["rating"] is None
    assert progress["playtime_minutes"] == 30
    assert _last_action(game["db"], game["media"]["id"]) == "CHAPTER_RATING_REMOVED"


def test_removing_a_rating_that_does_not_exist_is_404(client, auth_headers, game):
    assert client.delete(f"{_chapter(game)}/rating", headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- chapter playtime
def test_the_newest_playtime_entry_of_a_chapter_can_be_removed(client, auth_headers, game):
    """The case of the issue: 600 minutes typed instead of 60."""
    client.post(f"{_chapter(game)}/playtime", json={"minutes": 45}, headers=auth_headers)
    client.post(f"{_chapter(game)}/playtime", json={"minutes": 600}, headers=auth_headers)

    response = client.delete(f"{_chapter(game)}/playtime/last", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["playtime_minutes"] == 45
    assert client.get("/stats", headers=auth_headers).json()["playtime"]["total_minutes"] == 45
    assert _last_action(game["db"], game["media"]["id"]) == "PLAYTIME_REMOVED"


def test_removing_playtime_twice_removes_the_two_newest_entries(client, auth_headers, game):
    for minutes in (10, 20, 30):
        client.post(f"{_chapter(game)}/playtime", json={"minutes": minutes}, headers=auth_headers)

    client.delete(f"{_chapter(game)}/playtime/last", headers=auth_headers)
    response = client.delete(f"{_chapter(game)}/playtime/last", headers=auth_headers)

    assert response.json()["playtime_minutes"] == 10


def test_removing_playtime_of_a_chapter_without_entries_is_404(client, auth_headers, game):
    client.put(f"{_chapter(game)}/rating", json={"rating": 2}, headers=auth_headers)

    assert client.delete(f"{_chapter(game)}/playtime/last", headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- title playtime
def test_the_newest_playtime_entry_of_a_whole_game_can_be_removed(client, auth_headers, game):
    url = f"/library/{game['entry']['id']}/playtime"
    client.post(url, json={"minutes": 60}, headers=auth_headers)
    client.post(url, json={"minutes": 600}, headers=auth_headers)

    response = client.delete(f"{url}/last", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["playtime_minutes"] == 60


def test_removing_title_playtime_keeps_the_chapter_entries(client, auth_headers, game):
    client.post(f"{_chapter(game)}/playtime", json={"minutes": 15}, headers=auth_headers)

    response = client.delete(f"/library/{game['entry']['id']}/playtime/last", headers=auth_headers)

    assert response.status_code == 404  # the only entry belongs to a chapter
    assert client.get(_chapter(game), headers=auth_headers).json()["playtime_minutes"] == 15


# ---------------------------------------------------------------- decision
def test_a_choice_can_be_removed(client, auth_headers, game):
    client.put(f"{_chapter(game)}/decision", json={"choice": "B"}, headers=auth_headers)

    response = client.delete(f"{_chapter(game)}/decision", headers=auth_headers)

    progress = client.get(_chapter(game), headers=auth_headers).json()
    assert response.status_code == 204
    assert progress["choice"] is None and progress["decisions"] == []
    assert _last_action(game["db"], game["media"]["id"]) == "DECISION_REMOVED"


def test_a_chapter_with_several_decision_points_needs_the_point(client, auth_headers, game):
    second = add_decision_point(game["db"], game["chapter"], game["media"]["id"], labels=("X", "Y"), position=2)
    client.put(f"{_chapter(game)}/decision", json={"choice": "Y", "decision_point_id": second}, headers=auth_headers)

    assert client.delete(f"{_chapter(game)}/decision", headers=auth_headers).status_code == 422
    response = client.delete(f"{_chapter(game)}/decision", params={"decision_point_id": second}, headers=auth_headers)

    assert response.status_code == 204


def test_removing_a_choice_that_was_not_made_is_404(client, auth_headers, game):
    assert client.delete(f"{_chapter(game)}/decision", headers=auth_headers).status_code == 404


# ---------------------------------------------------------------- access
@pytest.mark.parametrize(
    "suffix",
    ["/review", "/playtime/last", "/chapters/{chapter}/rating", "/chapters/{chapter}/playtime/last", "/chapters/{chapter}/decision"],
)
def test_another_user_cannot_remove_anything(client, auth_headers, game, suffix):
    client.post(f"/library/{game['entry']['id']}/review", json={"text": "Mine."}, headers=auth_headers)
    other = register_and_login(client, new_credentials())
    path = f"/library/{game['entry']['id']}" + suffix.format(chapter=game["chapter"])

    assert client.delete(path, headers=other).status_code == 404
    assert client.get(f"/library/{game['entry']['id']}/review", headers=auth_headers).status_code == 200


@pytest.mark.parametrize(
    "suffix",
    ["/review", "/playtime/last", "/chapters/{chapter}/rating", "/chapters/{chapter}/playtime/last", "/chapters/{chapter}/decision"],
)
def test_removing_needs_a_login(client, game, suffix):
    path = f"/library/{game['entry']['id']}" + suffix.format(chapter=game["chapter"])

    assert client.delete(path).status_code == 401


@pytest.mark.parametrize("entry_id", [0, 2**31])
def test_an_id_out_of_range_is_404(client, auth_headers, entry_id):
    assert client.delete(f"/library/{entry_id}/review", headers=auth_headers).status_code == 404
    assert client.delete(f"/library/{entry_id}/playtime/last", headers=auth_headers).status_code == 404
