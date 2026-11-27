"""Episode lengths and episode playtime logging (#411).

- An episode without a length gets one: the length of the episode, then the usual episode length
  of the series, then the average of the episodes of the series, then a default.
- Episodes and cache entries saved before this fallback are loaded again once.
- "Mark completed" logs the full length of an episode that TMDB gave no length.
- The database engine tests a pooled connection before use, and a lost database answers 503.
"""
import copy
import itertools
import time

import pytest
from sqlalchemy.exc import OperationalError

from app.core import cache, config
from app.core.database import engine, engine_options
from app.integrations.common import (
    DEFAULT_EPISODE_RUNTIME_MINUTES,
    ExternalEpisode,
    ExternalSeason,
    average_runtime,
    fill_missing_runtimes,
)
from app.models.entities import Chapter
from app.services import catalog_service
from fake_external_apis import SERIES_DETAILS
from helpers import add_to_library, unique

_outside_ids = itertools.count(20_000_000 + time.time_ns() % 900_000_000)


def new_series(client, headers, fake, seasons=None, info=None):
    external_id = next(_outside_ids)
    fake.series[external_id] = {"name": "Runtime Show", "seasons": seasons} if seasons is not None \
        else copy.deepcopy(SERIES_DETAILS[70001])
    if info is not None:
        fake.series_info[external_id] = info
    response = client.post(
        "/media",
        json={"title": unique("series"), "media_type": "SERIES", "external_api_id": external_id},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def episodes_of(response):
    return {
        (season["season_number"], episode["number"]): episode
        for season in response.json()["seasons"]
        for episode in season["episodes"]
    }


def _episode(number, runtime):
    return {"id": 900_000 + number, "episode_number": number, "name": f"E{number}",
            "air_date": "2020-01-01", "runtime": runtime}


def _external_episode(number, runtime):
    return ExternalEpisode(number=number, title=None, release_date=None,
                           runtime_minutes=runtime, external_id=None)


# ---------------------------------------------------------------- the fallback chain
@pytest.mark.parametrize("values, expected", [
    ([42, 45], 44), ([], None), ([0, None, "x", True], None), ([30, 0], 30), (None, None), (42, None),
])
def test_average_runtime(values, expected):
    assert average_runtime(values) == expected


def test_a_known_length_is_never_changed():
    seasons = [ExternalSeason(1, None, None, [_external_episode(1, 3), _external_episode(2, None)])]

    filled = fill_missing_runtimes(seasons, 40)

    assert [e.runtime_minutes for e in filled[0].episodes] == [3, 40]


def test_the_series_length_comes_before_the_other_episodes(client, auth_headers, fake_external_apis):
    series = new_series(
        client, auth_headers, fake_external_apis,
        seasons=[{"season_number": 1, "name": "S1", "air_date": None,
                  "episodes": [_episode(1, 60), _episode(2, None), _episode(3, 0)]}],
        info={"episode_run_time": [42, 44]},
    )

    episodes = episodes_of(client.get(f"/catalog/{series['id']}", headers=auth_headers))

    assert [episodes[(1, n)]["runtime_minutes"] for n in (1, 2, 3)] == [60, 43, 43]


def test_without_a_series_length_the_average_of_the_episodes_is_used(
    client, auth_headers, fake_external_apis
):
    series = new_series(
        client, auth_headers, fake_external_apis,
        seasons=[{"season_number": 1, "name": "S1", "air_date": None, "episodes": [_episode(1, 20)]},
                 {"season_number": 2, "name": "S2", "air_date": None,
                  "episodes": [_episode(1, 30), _episode(2, None)]}],
        info={"episode_run_time": []},
    )

    episodes = episodes_of(client.get(f"/catalog/{series['id']}", headers=auth_headers))

    assert episodes[(2, 2)]["runtime_minutes"] == 25


def test_without_any_length_the_default_is_used(client, auth_headers, fake_external_apis):
    series = new_series(
        client, auth_headers, fake_external_apis,
        seasons=[{"season_number": 1, "name": "S1", "air_date": None,
                  "episodes": [_episode(1, None), _episode(2, None)]}],
    )

    episodes = episodes_of(client.get(f"/catalog/{series['id']}", headers=auth_headers))

    assert {e["runtime_minutes"] for e in episodes.values()} == {DEFAULT_EPISODE_RUNTIME_MINUTES}


# ---------------------------------------------------------------- rows saved before the fallback
def test_a_fresh_series_with_episodes_without_a_length_is_loaded_again(
    client, auth_headers, fake_external_apis, db, monkeypatch
):
    monkeypatch.setattr(config, "DB_CACHE_TTL_DAYS", 7)
    series = new_series(client, auth_headers, fake_external_apis)
    client.get(f"/catalog/{series['id']}", headers=auth_headers)
    # As it was saved before #411: one episode without a length
    episode = db.query(Chapter).filter(Chapter.media_item_id == series["id"]).order_by(Chapter.id).first()
    episode.runtime_minutes = None
    db.commit()
    cache.clear_prefix("omni:catalog:")
    calls = fake_external_apis.count("tmdb")

    response = client.get(f"/catalog/{series['id']}", headers=auth_headers)

    assert fake_external_apis.count("tmdb") > calls
    assert all(e["runtime_minutes"] for e in episodes_of(response).values())
    # Now every episode has a length, so the next view is served from the database
    calls = fake_external_apis.count("tmdb")
    cache.clear_prefix("omni:catalog:")
    client.get(f"/catalog/{series['id']}", headers=auth_headers)
    assert fake_external_apis.count("tmdb") == calls


def test_a_cache_entry_without_episode_lengths_is_a_miss(client, auth_headers, fake_external_apis):
    series = new_series(client, auth_headers, fake_external_apis)
    client.get(f"/catalog/{series['id']}", headers=auth_headers)
    key = catalog_service._details_cache_key(series["external_api_id"])
    cached = cache.get_json(key)
    cached["seasons"][1]["episodes"][2]["runtime_minutes"] = None  # as before #411

    assert catalog_service._outside_from_cache(cached) is None


# ---------------------------------------------------------------- logging an episode
def test_mark_completed_logs_the_fallback_length_and_it_stays(client, auth_headers, fake_external_apis):
    series = new_series(client, auth_headers, fake_external_apis)
    entry = add_to_library(client, auth_headers, series["id"])
    episode = episodes_of(client.get(f"/catalog/{series['id']}", headers=auth_headers))[(1, 3)]
    assert episode["runtime_minutes"] == 50  # TMDB gave no length

    logged = client.post(
        f"/library/{entry['id']}/chapters/{episode['id']}/playtime",
        json={"minutes": episode["runtime_minutes"]}, headers=auth_headers,
    )

    assert logged.status_code == 201, logged.text
    progress = client.get(f"/library/{entry['id']}/chapters/{episode['id']}", headers=auth_headers)
    assert progress.json()["playtime_minutes"] == 50


@pytest.mark.parametrize("minutes", [0, -5, None])
def test_zero_or_missing_minutes_are_refused(client, auth_headers, fake_external_apis, minutes):
    series = new_series(client, auth_headers, fake_external_apis)
    entry = add_to_library(client, auth_headers, series["id"])
    episode = episodes_of(client.get(f"/catalog/{series['id']}", headers=auth_headers))[(1, 1)]

    response = client.post(
        f"/library/{entry['id']}/chapters/{episode['id']}/playtime",
        json={"minutes": minutes}, headers=auth_headers,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- the database connection
def test_the_engine_tests_and_recycles_pooled_connections():
    assert engine.pool._pre_ping is True
    assert engine.pool._recycle == 300


def test_postgres_connections_get_keepalives_and_a_connect_timeout():
    options = engine_options("postgresql+psycopg2://u:p@db.example/omnilog")

    assert options["connect_args"]["keepalives"] == 1
    assert options["connect_args"]["connect_timeout"] == 10


def test_a_lost_database_answers_503(client, auth_headers, fake_external_apis, monkeypatch):
    series = new_series(client, auth_headers, fake_external_apis)
    entry = add_to_library(client, auth_headers, series["id"])

    def lost(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("server closed the connection unexpectedly"))

    monkeypatch.setattr("app.services.chapter_service.log_playtime", lost)

    response = client.post(f"/library/{entry['id']}/chapters/1/playtime",
                           json={"minutes": 10}, headers=auth_headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "The database is not available right now"}
    assert "closed the connection" not in response.text
