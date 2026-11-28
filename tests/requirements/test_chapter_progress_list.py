"""GET /library/{entry_id}/chapters lists the progress of every chapter in one answer (US-10 to
US-12, NFR-01, #419).

Before, the title page sent one GET per chapter: 300 requests and 1800 SQL queries for a series
with 300 episodes.
"""
import pytest
from sqlalchemy import event

from app.core.database import engine
from app.models.entities import Chapter, ChapterKind, Season
from epic4_helpers import add_chapter, add_decision_point
from helpers import add_to_library, create_media, new_credentials, register_and_login


def _path(entry_id):
    return f"/library/{entry_id}/chapters"


@pytest.fixture
def game(client, auth_headers, db):
    media = create_media(client, auth_headers, media_type="GAME")
    chapters = [add_chapter(db, media["id"], number) for number in (1, 2, 3)]
    points = [
        add_decision_point(db, chapters[1], media["id"], labels=("A", "B"), position=1),
        add_decision_point(db, chapters[1], media["id"], labels=("X", "Y"), position=2),
    ]
    entry = add_to_library(client, auth_headers, media["id"])
    return entry, chapters, points


def test_an_entry_without_data_lists_nothing(client, auth_headers, game):
    entry, _, _ = game

    response = client.get(_path(entry["id"]), headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_the_list_holds_ratings_playtime_and_choices(client, auth_headers, game):
    entry, (first, second, _third), points = game
    base = _path(entry["id"])
    client.put(f"{base}/{first}/rating", json={"rating": 4}, headers=auth_headers)
    client.post(f"{base}/{first}/playtime", json={"minutes": 90}, headers=auth_headers)
    client.post(f"{base}/{first}/playtime", json={"minutes": 30}, headers=auth_headers)
    client.put(f"{base}/{second}/decision", json={"choice": "Y", "decision_point_id": points[1]}, headers=auth_headers)
    client.put(f"{base}/{second}/decision", json={"choice": "A", "decision_point_id": points[0]}, headers=auth_headers)

    rows = {row["chapter_id"]: row for row in client.get(base, headers=auth_headers).json()}

    assert sorted(rows) == [first, second]  # the third chapter has no data
    assert rows[first]["rating"] == 4 and rows[first]["playtime_minutes"] == 120
    assert rows[first]["decisions"] == [] and rows[first]["choice"] is None
    assert rows[second]["rating"] is None and rows[second]["playtime_minutes"] == 0
    assert [d["choice"] for d in rows[second]["decisions"]] == ["A", "Y"]  # by position
    assert rows[second]["choice"] == "A"


def test_each_row_is_the_same_as_the_answer_for_one_chapter(client, auth_headers, game):
    entry, (first, _, _), _ = game
    client.put(f"{_path(entry['id'])}/{first}/rating", json={"rating": 5}, headers=auth_headers)

    listed = client.get(_path(entry["id"]), headers=auth_headers).json()
    single = client.get(f"{_path(entry['id'])}/{first}", headers=auth_headers).json()

    assert listed == [single]


def test_a_long_series_takes_a_fixed_number_of_queries(client, auth_headers, db):
    """300 episodes with data: one request, and the queries do not grow with the episodes."""
    media = create_media(client, auth_headers, media_type="SERIES")
    season = Season(media_item_id=media["id"], season_number=1, title="Season 1")
    db.add(season)
    db.flush()
    episodes = [
        Chapter(media_item_id=media["id"], season_id=season.id, number=number, kind=ChapterKind.EPISODE)
        for number in range(1, 301)
    ]
    db.add_all(episodes)
    db.commit()
    entry = add_to_library(client, auth_headers, media["id"])
    for episode in episodes[:20]:
        client.put(f"{_path(entry['id'])}/{episode.id}/rating", json={"rating": 3}, headers=auth_headers)

    queries = []
    listener = lambda *args: queries.append(1)  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        response = client.get(_path(entry["id"]), headers=auth_headers)
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    assert response.status_code == 200
    assert len(response.json()) == 20
    assert len(queries) <= 6  # user, entry, progress, decisions, and the token check


def test_another_users_entry_is_404(client, auth_headers, game):
    entry, _, _ = game
    other = register_and_login(client, new_credentials())

    assert client.get(_path(entry["id"]), headers=other).status_code == 404


@pytest.mark.parametrize("entry_id", [0, -1, 2**31, 999999999])
def test_an_unknown_entry_is_404(client, auth_headers, entry_id):
    assert client.get(_path(entry_id), headers=auth_headers).status_code == 404


def test_the_list_needs_a_login(client, game):
    entry, _, _ = game

    assert client.get(_path(entry["id"])).status_code == 401
