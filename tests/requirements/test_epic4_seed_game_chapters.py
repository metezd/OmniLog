"""Chapters and decision points of games from the seed file (US-09, US-12, open point 3 in
docs/analysis/data/domain-model.md).

IGDB gives no chapters and no decision points, so `python -m app.seed` loads them from
backend/app/seed/game_chapters.json. These tests cover the load (rules in app/seed/loader.py) and
how the rows look in the database. Title details are tested in
test_epic4_decision_points_in_details.py.
"""
import copy
import json

import pytest

from app.models.entities import Chapter, DecisionOption, DecisionPoint, MediaItem, MediaType
from app.seed import __main__ as seed_cli
from app.seed import loader
from app.seed.loader import SeedError, read_seed_file
from epic4_seed_helpers import game_of, load, next_external_id, seed_data


def chapters_of(db, item):
    db.expire_all()
    return db.query(Chapter).filter(Chapter.media_item_id == item.id).order_by(Chapter.number).all()


def row_counts(db, item):
    db.expire_all()
    chapter_ids = [c.id for c in db.query(Chapter).filter(Chapter.media_item_id == item.id)]
    points = db.query(DecisionPoint).filter(DecisionPoint.media_item_id == item.id).all()
    options = db.query(DecisionOption).filter(
        DecisionOption.decision_point_id.in_([p.id for p in points])
    ).count()
    return len(chapter_ids), len(points), options


# ---------------------------------------------------------------- the load
def test_the_seed_creates_the_game_its_chapters_decision_points_and_options(db):
    data = seed_data()

    report = load(db, data)

    assert (report.games_created, report.chapters_created) == (1, 2)
    assert (report.decision_points_created, report.options_created) == (1, 2)
    item = game_of(db, data)
    assert (item.title, item.media_type) == ("Seed Game", MediaType.GAME)
    first, second = chapters_of(db, item)
    assert (first.number, first.title, first.kind.value, first.season_id) == (1, "One", "CHAPTER", None)
    assert second.title == "Two"
    (point,) = first.decision_points
    assert (point.position, point.prompt, point.media_item_id) == (1, "Which way?", item.id)
    assert [(o.label, o.text) for o in point.options] == [("A", "Left"), ("B", "Right")]
    assert second.decision_points == []


def test_the_decision_points_of_a_chapter_get_their_position_from_the_list(db):
    points = [
        {"prompt": f"Question {n}", "options": [{"label": "A"}, {"label": "B"}]} for n in (1, 2, 3)
    ]
    data = seed_data(chapters=[{"number": 1, "decision_points": points}])

    load(db, data)

    (chapter,) = chapters_of(db, game_of(db, data))
    assert [(p.position, p.prompt) for p in chapter.decision_points] == [
        (1, "Question 1"), (2, "Question 2"), (3, "Question 3"),
    ]


def test_running_the_seed_again_changes_nothing(db):
    data = seed_data()
    load(db, data)
    item = game_of(db, data)
    ids_before = [c.id for c in chapters_of(db, item)]

    report = load(db, data)

    assert not report.changed
    assert report.warnings == []
    assert [c.id for c in chapters_of(db, item)] == ids_before
    assert row_counts(db, item) == (2, 1, 2)


def test_a_changed_file_updates_the_rows_in_place(db):
    data = seed_data()
    load(db, data)
    item = game_of(db, data)
    ids_before = [c.id for c in chapters_of(db, item)]
    point_id = chapters_of(db, item)[0].decision_points[0].id

    changed = copy.deepcopy(data)
    chapter = changed["games"][0]["chapters"][0]
    chapter["title"] = "One, renamed"
    chapter["runtime_minutes"] = 90
    chapter["decision_points"][0]["prompt"] = "Which way now?"
    chapter["decision_points"][0]["options"][1]["text"] = "Straight on"
    report = load(db, changed)

    assert (report.chapters_updated, report.decision_points_updated, report.options_updated) == (1, 1, 1)
    first = chapters_of(db, item)[0]
    assert [c.id for c in chapters_of(db, item)] == ids_before  # the same rows
    assert (first.title, first.runtime_minutes) == ("One, renamed", 90)
    assert first.decision_points[0].id == point_id  # the choices of users point to it
    assert first.decision_points[0].prompt == "Which way now?"
    assert [o.text for o in first.decision_points[0].options] == ["Left", "Straight on"]


def test_a_new_chapter_is_added_next_to_the_old_ones(db):
    data = seed_data()
    load(db, data)
    item = game_of(db, data)
    ids_before = [c.id for c in chapters_of(db, item)]

    extended = copy.deepcopy(data)
    extended["games"][0]["chapters"].append({"number": 3, "title": "Three"})
    report = load(db, extended)

    assert (report.chapters_created, report.chapters_updated) == (1, 0)
    assert [c.number for c in chapters_of(db, item)] == [1, 2, 3]
    assert [c.id for c in chapters_of(db, item)][:2] == ids_before


def test_nothing_is_deleted_and_the_missing_rows_are_reported(db):
    """The choices of the users point to these rows, so a row that left the file stays."""
    data = seed_data(
        chapters=[
            {"number": 1, "decision_points": [{"prompt": "Q", "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}]}]},
            {"number": 2},
        ]
    )
    load(db, data)
    item = game_of(db, data)

    smaller = seed_data(
        external_id=data["games"][0]["external_api_id"],
        chapters=[{"number": 1, "decision_points": [{"prompt": "Q", "options": [{"label": "A"}, {"label": "B"}]}]}],
    )
    report = load(db, smaller)

    assert row_counts(db, item) == (2, 1, 3)
    assert not report.changed
    assert len(report.warnings) == 2
    assert any("chapter 2" in w for w in report.warnings)
    assert any("option C" in w for w in report.warnings)

    no_points = seed_data(external_id=data["games"][0]["external_api_id"], chapters=[{"number": 1}])
    assert any("decision point at position 1" in w for w in load(db, no_points).warnings)
    assert row_counts(db, item) == (2, 1, 3)


def test_a_game_that_is_in_the_catalog_keeps_its_own_metadata(db):
    """A search at IGDB wrote the title and the poster. The seed must not overwrite them."""
    external_id = next_external_id()
    db.add(
        MediaItem(
            title="Seed Game", media_type=MediaType.GAME, external_api_id=external_id,
            poster_url="https://images.igdb.com/real.jpg", release_date="2015-01-30",
        )
    )
    db.commit()
    data = seed_data(external_id=external_id, title="seed game")
    data["games"][0].update(poster_url="https://example.test/other.jpg", release_date="1999")

    report = load(db, data)

    item = game_of(db, data)
    assert (item.title, item.poster_url, item.release_date) == (
        "Seed Game", "https://images.igdb.com/real.jpg", "2015-01-30",
    )
    assert report.games_created == 0
    assert report.warnings == []  # the title is the same, only the case differs


def test_a_different_title_for_a_saved_id_is_reported_as_a_likely_wrong_id(db):
    external_id = next_external_id()
    db.add(MediaItem(title="Another Game", media_type=MediaType.GAME, external_api_id=external_id))
    db.commit()

    report = load(db, seed_data(external_id=external_id, title="Seed Game"))

    assert len(report.warnings) == 1
    assert "Another Game" in report.warnings[0] and "Check the id" in report.warnings[0]


def test_a_series_with_the_same_outside_id_is_not_taken_for_the_game(db):
    """IGDB and TMDB ids are different number spaces, so the media type is part of the key."""
    external_id = next_external_id()
    db.add(MediaItem(title="Series", media_type=MediaType.SERIES, external_api_id=external_id))
    db.commit()
    data = seed_data(external_id=external_id)

    report = load(db, data)

    assert report.games_created == 1
    assert game_of(db, data).media_type == MediaType.GAME


def test_a_failure_in_the_middle_saves_nothing(db, monkeypatch):
    """Everything is written in one transaction."""
    first, second = seed_data(), seed_data()
    both = {"games": first["games"] + second["games"]}
    real = loader._apply_game
    calls = []

    def fail_on_the_second(db_, game, report):
        calls.append(game.external_api_id)
        if len(calls) == 2:
            raise RuntimeError("the database went away")
        real(db_, game, report)

    monkeypatch.setattr(loader, "_apply_game", fail_on_the_second)

    with pytest.raises(RuntimeError):
        load(db, both)

    assert game_of(db, first) is None and game_of(db, second) is None


# ---------------------------------------------------------------- the file is checked first
def seed_with(mutate):
    data = seed_data()
    mutate(data["games"][0])
    return data


@pytest.mark.parametrize(
    "mutate, where, text",
    [
        (lambda g: g.update(external_api_id=0), "games[0].external_api_id", "IGDB id"),
        (lambda g: g.update(external_api_id="12"), "games[0].external_api_id", ""),
        (lambda g: g.update(title=""), "games[0].title", ""),
        (lambda g: g.update(title="x" * 201), "games[0].title", ""),
        (lambda g: g.update(chapters=[]), "games[0].chapters", ""),
        (lambda g: g["chapters"].append({"number": 1}), "games[0]", "chapter numbers must be unique"),
        (lambda g: g["chapters"][0].update(number=-1), "games[0].chapters[0].number", ""),
        (lambda g: g["chapters"][0].update(runtime_minutes=-5), "games[0].chapters[0].runtime_minutes", ""),
        (lambda g: g["chapters"][0].update(decison_points=[]), "games[0].chapters[0].decison_points", "Extra inputs"),
        (lambda g: g["chapters"][0]["decision_points"][0].update(options=[{"label": "A"}]), "options", ""),
        (
            lambda g: g["chapters"][0]["decision_points"][0].update(options=[{"label": "A"}, {"label": "A"}]),
            "games[0].chapters[0].decision_points[0]", "option labels must be unique",
        ),
        (
            lambda g: g["chapters"][0]["decision_points"][0]["options"][0].update(label="12345678901"),
            "options[0].label", "",
        ),
        (lambda g: g["chapters"][0]["decision_points"][0].update(prompt="x" * 301), "prompt", ""),
    ],
)
def test_a_file_with_an_error_is_refused_and_says_where(db, tmp_path, mutate, where, text):
    path = tmp_path / "seed.json"
    data = seed_with(mutate)
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SeedError) as error:
        read_seed_file(path)

    assert where in str(error.value)
    assert text in str(error.value)
    assert "Value error," not in str(error.value)


def test_the_same_game_twice_in_one_file_is_refused(tmp_path):
    first = seed_data(external_id=777)
    both = {"games": first["games"] + first["games"]}
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(both), encoding="utf-8")

    with pytest.raises(SeedError, match="repeated ids"):
        read_seed_file(path)


def test_every_problem_is_listed_on_its_own_line(tmp_path):
    data = seed_data()
    data["games"][0]["title"] = ""
    data["games"][0]["chapters"][0]["number"] = -1
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SeedError) as error:
        read_seed_file(path)

    assert len(str(error.value).splitlines()) == 2


def test_a_file_that_is_not_json_or_does_not_exist_is_refused(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('{"games": [', encoding="utf-8")

    with pytest.raises(SeedError, match="not valid JSON"):
        read_seed_file(broken)
    with pytest.raises(SeedError, match="does not exist"):
        read_seed_file(tmp_path / "missing.json")


def test_an_empty_list_of_games_is_a_valid_file(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text('{"games": []}', encoding="utf-8")

    assert read_seed_file(path).games == []


# ---------------------------------------------------------------- the file that ships
def test_the_shipped_file_is_refused_until_the_igdb_id_is_filled_in():
    """The id could not be checked when the file was written. A wrong id would save the game
    under the wrong key, so the placeholder is refused instead of loaded."""
    with pytest.raises(SeedError, match="external_api_id must be the IGDB id"):
        read_seed_file()


def test_the_shipped_file_loads_once_the_id_is_filled_in(db):
    raw = json.loads(loader.DEFAULT_SEED_PATH.read_text(encoding="utf-8"))
    assert raw["games"], "the shipped file has no game"
    for game in raw["games"]:
        game["external_api_id"] = next_external_id()

    report = load(db, raw)

    chapters = sum(len(game["chapters"]) for game in raw["games"])
    assert report.chapters_created == chapters
    assert report.decision_points_created >= 1
    assert report.warnings == []


# ---------------------------------------------------------------- the command
def run_cli(args):
    return seed_cli.main(args)


def test_the_command_loads_a_file_and_reports_the_counts(tmp_path, capsys, db):
    data = seed_data()
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    assert run_cli([str(path)]) == 0
    out = capsys.readouterr().out
    assert "Games created: 1" in out
    assert "Chapters created: 2, updated: 0" in out
    assert "Decision points created: 1" in out
    assert "Options created: 2" in out
    assert game_of(db, data) is not None

    assert run_cli([str(path)]) == 0
    assert "The database already matched the file." in capsys.readouterr().out


def test_the_command_refuses_a_bad_file_with_exit_code_1(tmp_path, capsys, db):
    data = seed_data()
    data["games"][0]["chapters"][0]["number"] = -1
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    assert run_cli([str(path)]) == 1
    err = capsys.readouterr().err
    assert "Nothing was saved" in err and "chapters[0].number" in err
    assert game_of(db, data) is None


def test_the_command_does_nothing_for_a_file_without_games(tmp_path, capsys):
    path = tmp_path / "seed.json"
    path.write_text('{"games": []}', encoding="utf-8")

    assert run_cli([str(path)]) == 0
    assert "Nothing to do" in capsys.readouterr().out


def test_the_command_refuses_too_many_arguments(capsys):
    assert run_cli(["a.json", "b.json"]) == 1
    assert "Usage:" in capsys.readouterr().err


def test_the_command_uses_the_shipped_file_by_default_and_refuses_its_placeholder(capsys):
    assert run_cli([]) == 1
    assert "external_api_id must be the IGDB id" in capsys.readouterr().err
