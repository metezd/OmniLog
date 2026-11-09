"""Decision points and options in title details (US-09, US-12).

The data comes from the seed (app/seed), so these tests load a small seed first and then read it
back through GET /catalog/{id}.
"""
from sqlalchemy import event

from app.core.database import engine
from epic4_helpers import add_decision_point, add_episode
from epic4_seed_helpers import game_of, load, seed_data
from helpers import add_to_library, create_media


DECISION_POINT_FIELDS = {"id", "position", "prompt", "options"}
OPTION_FIELDS = {"id", "label", "text"}


def test_title_details_show_the_decision_points_with_their_options(client, auth_headers, db):
    data = seed_data(
        chapters=[
            {
                "number": 1,
                "decision_points": [
                    {"prompt": "First", "options": [{"label": "B", "text": "Right"}, {"label": "A", "text": "Left"}]},
                    {"prompt": "Second", "options": [{"label": "A"}, {"label": "B"}]},
                ],
            },
            {"number": 2},
        ]
    )
    load(db, data)
    item = game_of(db, data)

    response = client.get(f"/catalog/{item.id}", headers=auth_headers)

    assert response.status_code == 200
    first, second = response.json()["chapters"]
    assert second["decision_points"] == []
    points = first["decision_points"]
    assert [p["prompt"] for p in points] == ["First", "Second"]  # by position
    assert all(set(p) == DECISION_POINT_FIELDS for p in points)
    options = points[0]["options"]
    assert [o["label"] for o in options] == ["A", "B"]  # by label, as the file gave "B" first
    assert all(set(o) == OPTION_FIELDS for o in options)
    assert [o["text"] for o in options] == ["Left", "Right"]
    assert points[1]["options"][0]["text"] is None


def test_the_decision_points_of_an_episode_are_shown_the_same_way(client, auth_headers, db):
    series = create_media(client, auth_headers, media_type="SERIES")
    episode_id = add_episode(db, series["id"])
    point_id = add_decision_point(db, episode_id, series["id"], labels=("A", "B", "C"))

    response = client.get(f"/catalog/{series['id']}", headers=auth_headers)

    (episode,) = response.json()["seasons"][0]["episodes"]
    (point,) = episode["decision_points"]
    assert point["id"] == point_id
    assert [o["label"] for o in point["options"]] == ["A", "B", "C"]
    assert set(point) == DECISION_POINT_FIELDS


def test_the_number_of_queries_does_not_grow_with_the_decision_points(client, auth_headers, db):
    def titled(points_per_chapter):
        chapters = [
            {
                "number": n,
                "decision_points": [
                    {"prompt": f"Q{k}", "options": [{"label": "A"}, {"label": "B"}]}
                    for k in range(points_per_chapter)
                ],
            }
            for n in range(1, 5)
        ]
        data = seed_data(chapters=chapters)
        load(db, data)
        return game_of(db, data).id

    def count_queries(media_id):
        count = []
        record = lambda *args, **kwargs: count.append(1)  # noqa: E731
        event.listen(engine, "before_cursor_execute", record)
        try:
            assert client.get(f"/catalog/{media_id}", headers=auth_headers).status_code == 200
        finally:
            event.remove(engine, "before_cursor_execute", record)
        return len(count)

    small, large = titled(1), titled(3)

    assert count_queries(small) == count_queries(large)


def test_a_user_can_choose_an_option_of_a_seeded_decision_point(client, auth_headers, db):
    """From the seed, through title details, to the decision of a user (US-12)."""
    data = seed_data()
    load(db, data)
    item = game_of(db, data)
    entry = add_to_library(client, auth_headers, item.id)

    chapter = client.get(f"/catalog/{item.id}", headers=auth_headers).json()["chapters"][0]
    point = chapter["decision_points"][0]
    label = point["options"][1]["label"]
    url = f"/library/{entry['id']}/chapters/{chapter['id']}"

    put = client.put(f"{url}/decision", json={"choice": label}, headers=auth_headers)
    progress = client.get(url, headers=auth_headers).json()

    assert put.status_code == 200, put.text
    assert progress["choice"] == label
    assert [d["decision_point_id"] for d in progress["decisions"]] == [point["id"]]


