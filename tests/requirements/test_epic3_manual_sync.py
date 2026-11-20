"""Manual sync of the catalog (UC-EP3-03, issue #125): `python -m app.sync`.

The tests share one database, and a sync with no filter would also load the unsynced titles of
other tests. So every test names its own titles with --id (or the `media_ids` argument).
TMDB and IGDB are faked at the HTTP level (see fake_external_apis.py).
"""
import copy
import itertools
import time

import pytest

from app import sync as sync_cli
from app.core.database import SessionLocal
from app.models.entities import MediaItem, MediaType
from app.services import catalog_service
from fake_external_apis import SERIES_DETAILS
from helpers import unique

# Own range, so these ids cannot collide with the ids of other test modules (Integer column)
_outside_ids = itertools.count(1_000_000_000 + time.time_ns() % 800_000_000)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------- helpers
def _post(client, headers, media_type, outside_id=None):
    payload = {"title": unique(media_type.lower()), "media_type": media_type}
    if outside_id is not None:
        payload["external_api_id"] = outside_id
    response = client.post("/media", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def new_movie(client, headers, fake, genres=("Comedy",), known=True):
    outside_id = next(_outside_ids)
    if known:
        fake.movies[outside_id] = {
            "title": unique("movie"),
            "overview": "Synced by hand.",
            "genres": [{"id": 100 + n, "name": name} for n, name in enumerate(genres)],
        }
    return _post(client, headers, "MOVIE", outside_id)


def new_series(client, headers, fake):
    outside_id = next(_outside_ids)
    fake.series[outside_id] = copy.deepcopy(SERIES_DETAILS[70001])
    return _post(client, headers, "SERIES", outside_id)


def new_game(client, headers, fake, genres=("Adventure",)):
    outside_id = next(_outside_ids)
    fake.games.append({
        "id": outside_id,
        "name": unique("game"),
        "summary": "A game for the sync.",
        "genres": [{"id": 200 + n, "name": name} for n, name in enumerate(genres)],
    })
    return _post(client, headers, "GAME", outside_id)


def row(db, media_id):
    db.expire_all()
    return db.get(MediaItem, media_id)


def run(args, capsys):
    code = sync_cli.main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def ids(*media_ids):
    args = []
    for media_id in media_ids:
        args += ["--id", str(media_id)]
    return args


# ---------------------------------------------------------------- what a sync loads
def test_a_movie_that_was_never_opened_gets_its_details(client, auth_headers, fake_external_apis, db, capsys):
    """UC-EP3-03: the sync loads the description and genres of an unopened title."""
    movie_id = new_movie(client, auth_headers, fake_external_apis, genres=("Comedy", "Romance"))
    assert row(db, movie_id).last_synced is None

    code, out, _ = run(ids(movie_id), capsys)

    item = row(db, movie_id)
    assert code == 0
    assert "Titles selected: 1" in out and "Synced: 1" in out
    assert item.last_synced is not None
    assert item.description == "Synced by hand."
    assert sorted(g.name for g in item.genres) == ["Comedy", "Romance"]


def test_a_game_gets_its_details_from_igdb(client, auth_headers, fake_external_apis, db, capsys):
    game_id = new_game(client, auth_headers, fake_external_apis, genres=("Adventure", "Indie"))

    code, _, _ = run(ids(game_id), capsys)

    item = row(db, game_id)
    assert code == 0 and item.last_synced is not None
    assert item.description == "A game for the sync."
    assert sorted(g.name for g in item.genres) == ["Adventure", "Indie"]
    assert fake_external_apis.count("igdb") >= 1


def test_a_series_gets_its_seasons_and_episodes(client, auth_headers, fake_external_apis, db, capsys):
    series_id = new_series(client, auth_headers, fake_external_apis)

    code, _, _ = run(ids(series_id), capsys)

    item = row(db, series_id)
    assert code == 0 and item.last_synced is not None
    assert len(item.seasons) == len(SERIES_DETAILS[70001]["seasons"])
    assert all(season.episodes for season in item.seasons)


def test_one_run_syncs_titles_of_every_type(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    game_id = new_game(client, auth_headers, fake_external_apis)
    series_id = new_series(client, auth_headers, fake_external_apis)

    code, out, _ = run(ids(movie_id, game_id, series_id), capsys)

    assert code == 0 and "Titles selected: 3" in out and "Synced: 3" in out
    assert all(row(db, i).last_synced is not None for i in (movie_id, game_id, series_id))


# ---------------------------------------------------------------- what a sync leaves alone
def test_a_title_that_is_already_synced_is_not_loaded_again(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    run(ids(movie_id), capsys)
    calls = fake_external_apis.count()

    code, out, _ = run(ids(movie_id), capsys)

    assert code == 0
    assert "Titles selected: 0" in out and "Not selected: 1" in out
    assert fake_external_apis.count() == calls


def test_a_title_added_by_hand_is_not_selected(client, auth_headers, fake_external_apis, db, capsys):
    """A title without an outside id has nothing to load."""
    manual_id = _post(client, auth_headers, "GAME")

    code, out, _ = run(ids(manual_id), capsys)

    assert code == 0
    assert "Titles selected: 0" in out and "Not selected: 1" in out
    assert row(db, manual_id).last_synced is None
    assert fake_external_apis.count() == 0


def test_an_unknown_id_is_reported_and_is_not_an_error(client, auth_headers, fake_external_apis, capsys):
    code, out, _ = run(ids(2_000_000_000), capsys)

    assert code == 0 and "Not selected: 1" in out


def test_the_type_filter_keeps_other_types_out(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    game_id = new_game(client, auth_headers, fake_external_apis)

    code, out, _ = run(["--type", "GAME", *ids(movie_id, game_id)], capsys)

    assert code == 0 and "Synced: 1" in out and "Not selected: 1" in out
    assert row(db, game_id).last_synced is not None
    assert row(db, movie_id).last_synced is None


def test_the_limit_stops_after_that_many_titles_oldest_first(client, auth_headers, fake_external_apis, db, capsys):
    first = new_movie(client, auth_headers, fake_external_apis)
    second = new_movie(client, auth_headers, fake_external_apis)

    code, out, _ = run(["--limit", "1", *ids(first, second)], capsys)

    assert code == 0 and "Titles selected: 1" in out
    assert row(db, first).last_synced is not None
    assert row(db, second).last_synced is None


def test_a_dry_run_counts_and_calls_no_outside_service(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    game_id = new_game(client, auth_headers, fake_external_apis)

    code, out, _ = run(["--dry-run", *ids(movie_id, game_id)], capsys)

    assert code == 0 and "Titles that would be synced: 2" in out
    assert fake_external_apis.count() == 0
    assert row(db, movie_id).last_synced is None


# ---------------------------------------------------------------- failures (NFR-04)
def test_a_title_the_outside_service_does_not_know_stays_unsynced(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis, known=False)

    code, out, _ = run(ids(movie_id), capsys)

    assert code == 0
    assert "Synced: 0" in out and "Not synced: 1" in out
    assert row(db, movie_id).last_synced is None


def test_an_outage_leaves_a_movie_unsynced_so_the_next_run_tries_again(client, auth_headers, fake_external_apis, db, capsys):
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=503, times=None)

    code, out, _ = run(ids(movie_id), capsys)
    assert code == 0 and "Not synced: 1" in out
    assert row(db, movie_id).last_synced is None

    fake_external_apis._scripted.clear()  # the service is back
    code, out, _ = run(ids(movie_id), capsys)
    assert code == 0 and "Synced: 1" in out
    assert row(db, movie_id).last_synced is not None


def test_a_failing_title_does_not_stop_the_others(client, auth_headers, fake_external_apis, db, capsys):
    """TMDB is down for the series (an error), and IGDB still serves the game."""
    series_id = new_series(client, auth_headers, fake_external_apis)
    game_id = new_game(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=503, times=None)

    code, out, _ = run(ids(series_id, game_id), capsys)

    assert code == 1  # a title raised an error
    assert "Synced: 1" in out and "Errors: 1" in out
    assert row(db, game_id).last_synced is not None
    assert row(db, series_id).last_synced is None


def test_a_database_failure_exits_with_1(monkeypatch, capsys):
    def broken(*args, **kwargs):
        raise RuntimeError("database is down")

    monkeypatch.setattr(catalog_service, "sync_titles", broken)

    code, _, err = run(["--id", "1"], capsys)

    assert code == 1 and "The sync could not run" in err and "database is down" in err


# ---------------------------------------------------------------- the command line
@pytest.mark.parametrize("args", [["--type", "BOOK"], ["--limit", "0"], ["--limit", "x"], ["--id", "x"], ["--nope"]])
def test_a_wrong_option_exits_with_2(args, capsys):
    code, _, err = run(args, capsys)

    assert code == 2 and err


def test_help_exits_with_0(capsys):
    code, out, _ = run(["--help"], capsys)

    assert code == 0 and "--dry-run" in out


# ---------------------------------------------------------------- the service
def test_sync_titles_returns_a_report(client, auth_headers, fake_external_apis, db):
    movie_id = new_movie(client, auth_headers, fake_external_apis)

    report = catalog_service.sync_titles(db, media_ids=[movie_id, 2_000_000_000])

    assert report == catalog_service.SyncReport(selected=1, synced=1, unsynced=0, errors=0, not_selected=1)


def test_sync_missing_details_still_returns_the_number_of_synced_titles(client, auth_headers, fake_external_apis, db, monkeypatch):
    """The older function of issue #125 keeps its meaning. It has no filter, so the test limits
    the work to its own title by narrowing what sync_titles may select."""
    movie_id = new_movie(client, auth_headers, fake_external_apis)
    real = catalog_service.sync_titles
    monkeypatch.setattr(
        catalog_service, "sync_titles", lambda session: real(session, media_ids=[movie_id])
    )

    assert catalog_service.sync_missing_details(db) == 1
