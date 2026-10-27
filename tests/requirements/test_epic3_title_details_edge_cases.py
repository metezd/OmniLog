"""Edge cases for title details (US-09, NFR-01, NFR-04).

A series gets its seasons and episodes from TMDB, which is faked at the HTTP level (see
fake_external_apis.py), so the real client code runs. The chapters of a game have no outside
source, and no endpoint creates them yet (open point 3 in docs/analysis/data/domain-model.md).
The tests that need game chapters therefore put them in the database directly.
"""
import copy
import itertools

import pytest
from sqlalchemy.exc import IntegrityError

from app.core import cache, config
from app.core.database import SessionLocal
from app.integrations import tmdb
from app.models.entities import Chapter, ChapterKind, MediaItem, MediaType, Season
from app.services import catalog_service
from fake_external_apis import SERIES_DETAILS
from helpers import create_media, unique

# The tests share one database, so every test that loads a series gets an outside id of its own
_outside_ids = itertools.count(1_000_000)

DETAIL_FIELDS = {
    "id", "title", "media_type", "poster_url", "release_date", "external_api_id",
    "genres", "description", "seasons", "chapters",
}


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------- helpers
def open_title(client, headers, media_id):
    return client.get(f"/catalog/{media_id}", headers=headers)


def new_series(client, headers, fake, template=70001):
    """Add a series to the catalog by hand, with its own outside id, and teach the fake TMDB
    its seasons. Returns the catalog id."""
    external_id = next(_outside_ids)
    fake.series[external_id] = copy.deepcopy(SERIES_DETAILS[template])
    response = client.post(
        "/media",
        json={"title": unique("series"), "media_type": "SERIES", "external_api_id": external_id},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    body["fake_key"] = external_id
    return body


def add_chapters(db, media_id, titles, first_number=1):
    for number, title in enumerate(titles, first_number):
        db.add(Chapter(media_item_id=media_id, number=number, kind=ChapterKind.CHAPTER, title=title))
    db.commit()


def seasons_of(response):
    return {season["season_number"]: season for season in response.json()["seasons"]}


def cache_key(series):
    return catalog_service._details_cache_key(series["external_api_id"])


# ---------------------------------------------------------------- access and validation
def test_details_require_authentication(client, fake_external_apis):
    """NFR-02: opening a title without a token returns 401 and calls no outside service."""
    response = client.get("/catalog/1")

    assert response.status_code == 401
    assert fake_external_apis.count() == 0


def test_a_text_id_returns_422(client, auth_headers):
    """US-09: an id that is not a number is a validation error."""
    assert client.get("/catalog/abc", headers=auth_headers).status_code == 422


@pytest.mark.parametrize("media_id", ["0", "-5", str(2**31), "99999999999999999999"])
def test_ids_that_cannot_exist_return_404(client, auth_headers, media_id):
    """US-09: an id that cannot exist (zero, negative, too large) is unknown (404), never a 500."""
    assert client.get(f"/catalog/{media_id}", headers=auth_headers).status_code == 404


def test_search_is_not_taken_for_an_id(client, auth_headers):
    """US-08 and US-09: /catalog/search still reaches the search, not the details."""
    response = client.get("/catalog/search", params={"q": "Life is Strange", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 200


def test_the_response_has_the_documented_fields_only(client, auth_headers, fake_external_apis):
    """US-09: the answer shows no internal columns, such as the sync time or outside episode ids."""
    series = new_series(client, auth_headers, fake_external_apis)

    body = open_title(client, auth_headers, series["id"]).json()

    assert set(body) == DETAIL_FIELDS
    assert set(body["seasons"][1]) == {"id", "season_number", "title", "air_date", "episodes"}
    assert set(body["seasons"][1]["episodes"][0]) == {
        "id", "number", "kind", "title", "release_date", "runtime_minutes", "decision_points",
    }


# ---------------------------------------------------------------- series: the data
def test_series_details_have_metadata_and_artwork(client, auth_headers):
    """US-09: a title from the catalog shows its metadata and its poster."""
    found = client.get("/catalog/search", params={"q": "Breaking Bad", "type": "SERIES"}, headers=auth_headers)
    series = next(item for item in found.json() if item["title"] == "Breaking Bad")

    body = open_title(client, auth_headers, series["id"]).json()

    assert body["media_type"] == "SERIES"
    assert body["poster_url"] == "https://image.tmdb.org/t/p/w500/bb.jpg"
    assert body["release_date"] == "2008-01-20"
    assert body["external_api_id"] == 70001


def test_series_seasons_and_episodes_are_complete(client, auth_headers, fake_external_apis):
    """US-09: every season and episode of the series is returned with its fields."""
    series = new_series(client, auth_headers, fake_external_apis)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    body = response.json()
    assert body["chapters"] == []  # episodes belong to a season, not to the title
    seasons = seasons_of(response)
    assert sorted(seasons) == [0, 1, 2]

    specials = seasons[0]
    assert (specials["title"], specials["air_date"]) == ("Specials", None)
    assert [e["title"] for e in specials["episodes"]] == ["Making of the pilot"]

    season_one = seasons[1]
    assert isinstance(season_one["id"], int)
    assert (season_one["title"], season_one["air_date"]) == ("Season 1", "2008-01-20")
    first, second, third = season_one["episodes"]
    assert isinstance(first["id"], int)
    assert first == {**first, "number": 1, "kind": "EPISODE", "title": "Pilot",
                     "release_date": "2008-01-20", "runtime_minutes": 58}
    assert second["title"] == "Cat's in the Bag..."
    assert third["runtime_minutes"] is None  # TMDB did not know the length
    assert [e["number"] for e in seasons[2]["episodes"]] == [1, 2]


def test_seasons_and_episodes_are_sorted_by_number(client, auth_headers, fake_external_apis):
    """US-09: the order does not depend on the order in which TMDB sends them."""
    series = new_series(client, auth_headers, fake_external_apis)
    show = fake_external_apis.series[series["fake_key"]]
    show["seasons"].reverse()
    for season in show["seasons"]:
        season["episodes"].reverse()

    response = open_title(client, auth_headers, series["id"])

    assert [s["season_number"] for s in response.json()["seasons"]] == [0, 1, 2]
    assert [e["number"] for e in seasons_of(response)[1]["episodes"]] == [1, 2, 3]


def test_a_series_without_seasons_returns_an_empty_list(client, auth_headers, fake_external_apis, db):
    """US-09: a series that has no seasons is not an error. It counts as loaded."""
    series = new_series(client, auth_headers, fake_external_apis, template=70002)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert response.json()["seasons"] == []
    assert fake_external_apis.count("tmdb") == 1  # no seasons, so no call for episodes
    assert db.get(MediaItem, series["id"]).last_synced is not None

    open_title(client, auth_headers, series["id"])
    assert fake_external_apis.count("tmdb") == 1


# ---------------------------------------------------------------- series: calls to TMDB
def test_seasons_are_asked_for_in_one_extra_call(client, auth_headers, fake_external_apis):
    """US-09: one call lists the seasons, one more call brings all their episodes."""
    series = new_series(client, auth_headers, fake_external_apis)

    open_title(client, auth_headers, series["id"])

    first, second = fake_external_apis.calls_to("tmdb")
    assert first.url.endswith(f"/tv/{series['fake_key']}")
    assert "append_to_response" not in first.params
    assert second.params["append_to_response"] == "season/0,season/1,season/2"


def test_many_seasons_are_asked_for_in_groups_of_20(client, auth_headers, fake_external_apis):
    """US-09: TMDB answers 20 appended requests at most, so 45 seasons take 3 more calls."""
    series = new_series(client, auth_headers, fake_external_apis, template=70003)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert [s["season_number"] for s in response.json()["seasons"]] == list(range(1, 46))
    assert all(len(s["episodes"]) == 2 for s in response.json()["seasons"])
    asked = [call.params.get("append_to_response", "").count("season/")
             for call in fake_external_apis.calls_to("tmdb")]
    assert asked == [0, 20, 20, 5]


def test_the_series_id_in_the_url_is_a_number(client, auth_headers, fake_external_apis):
    """Security: only the number of the saved outside id goes into the TMDB path."""
    series = new_series(client, auth_headers, fake_external_apis)

    open_title(client, auth_headers, series["id"])

    path = fake_external_apis.calls_to("tmdb")[0].url
    assert path == f"https://api.themoviedb.org/3/tv/{series['fake_key']}"


# ---------------------------------------------------------------- cache (R-EP3-02, NFR-01)
def test_a_second_request_does_not_call_tmdb(client, auth_headers, fake_external_apis):
    """US-09: a series that was loaded is answered without any outside call."""
    series = new_series(client, auth_headers, fake_external_apis)
    first = open_title(client, auth_headers, series["id"])
    calls = fake_external_apis.count()

    second = open_title(client, auth_headers, series["id"])

    assert calls == 2
    assert fake_external_apis.count() == calls
    assert second.json() == first.json()


def test_the_saved_copy_is_rebuilt_from_the_cache(client, auth_headers, fake_external_apis, db):
    """US-09: when the cache has the series but the database does not, TMDB is still not called."""
    series = new_series(client, auth_headers, fake_external_apis)
    first = open_title(client, auth_headers, series["id"])
    db.query(Season).filter(Season.media_item_id == series["id"]).delete()  # episodes go with them
    db.query(MediaItem).filter(MediaItem.id == series["id"]).update({"last_synced": None})
    db.commit()
    calls = fake_external_apis.count()

    second = open_title(client, auth_headers, series["id"])

    assert fake_external_apis.count() == calls
    assert [s["season_number"] for s in second.json()["seasons"]] == [0, 1, 2]
    assert [e["title"] for e in seasons_of(second)[1]["episodes"]] == [
        e["title"] for e in seasons_of(first)[1]["episodes"]
    ]


def test_the_cache_entry_has_a_time_to_live(client, auth_headers, fake_external_apis):
    """US-09: the cache entry expires after DETAILS_CACHE_TTL_SECONDS (configurable, AN-2)."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])

    client_ = cache._redis()
    if client_ is None:
        pytest.skip("Redis is not running")
    ttl = client_.ttl(cache_key(series))

    assert 0 < ttl <= config.DETAILS_CACHE_TTL_SECONDS


def test_a_refresh_updates_the_saved_rows_in_place(client, auth_headers, fake_external_apis, db):
    """US-09: after the cache expires, changes at TMDB are saved. Ids stay the same."""
    series = new_series(client, auth_headers, fake_external_apis)
    before = open_title(client, auth_headers, series["id"])
    show = fake_external_apis.series[series["fake_key"]]
    season_one = next(s for s in show["seasons"] if s["season_number"] == 1)
    season_one["name"] = "The Beginning"
    season_one["episodes"][0]["name"] = "Pilot (renamed)"
    season_one["episodes"][0]["runtime"] = 60
    season_one["episodes"].append(
        {"id": 5104, "episode_number": 4, "name": "Added later", "air_date": "2008-02-17", "runtime": 48}
    )
    show["seasons"].append(
        {"season_number": 3, "name": "Season 3", "air_date": "2010-03-21",
         "episodes": [{"id": 5301, "episode_number": 1, "name": "No Más", "air_date": "2010-03-21", "runtime": 47}]}
    )
    cache.clear_prefix("omni:catalog:")

    after = open_title(client, auth_headers, series["id"])

    old, new = seasons_of(before), seasons_of(after)
    assert sorted(new) == [0, 1, 2, 3]
    assert new[1]["id"] == old[1]["id"]
    assert new[1]["title"] == "The Beginning"
    assert [e["id"] for e in new[1]["episodes"][:3]] == [e["id"] for e in old[1]["episodes"]]
    assert new[1]["episodes"][0]["title"] == "Pilot (renamed)"
    assert new[1]["episodes"][0]["runtime_minutes"] == 60
    assert [e["number"] for e in new[1]["episodes"]] == [1, 2, 3, 4]
    assert new[3]["episodes"][0]["title"] == "No Más"
    assert db.query(Season).filter(Season.media_item_id == series["id"]).count() == 4


def test_episodes_that_tmdb_no_longer_lists_are_kept(client, auth_headers, fake_external_apis):
    """Data safety: a refresh never deletes rows. A rating of a user (Epic 4) will point to them."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    show = fake_external_apis.series[series["fake_key"]]
    show["seasons"] = [s for s in show["seasons"] if s["season_number"] != 2]
    next(s for s in show["seasons"] if s["season_number"] == 1)["episodes"].pop()
    cache.clear_prefix("omni:catalog:")

    after = open_title(client, auth_headers, series["id"])

    assert fake_external_apis.count("tmdb") == 4  # it really asked again
    assert sorted(seasons_of(after)) == [0, 1, 2]
    assert [e["number"] for e in seasons_of(after)[1]["episodes"]] == [1, 2, 3]


def test_a_series_that_tmdb_does_not_know_is_not_an_error(client, auth_headers, fake_external_apis, db):
    """US-09: TMDB answers 404 for the outside id. The title is returned with no seasons."""
    series = new_series(client, auth_headers, fake_external_apis)
    del fake_external_apis.series[series["fake_key"]]

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert response.json()["seasons"] == []
    assert db.get(MediaItem, series["id"]).last_synced is None  # nothing was loaded


def test_an_unknown_series_is_cached_for_a_while(client, auth_headers, fake_external_apis):
    """NFR-04: a wrong outside id does not send a call to TMDB with every request."""
    series = new_series(client, auth_headers, fake_external_apis)
    del fake_external_apis.series[series["fake_key"]]
    open_title(client, auth_headers, series["id"])
    calls = fake_external_apis.count()

    open_title(client, auth_headers, series["id"])

    assert calls == 1
    assert fake_external_apis.count() == calls


def test_details_work_when_redis_is_down(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: with Redis down, the in-process cache keeps repeated requests off TMDB."""
    monkeypatch.setattr(config, "REDIS_URL", "redis://127.0.0.1:1/0")
    cache.reset_connection()
    series = new_series(client, auth_headers, fake_external_apis)

    first = open_title(client, auth_headers, series["id"])
    calls = fake_external_apis.count()
    second = open_title(client, auth_headers, series["id"])

    assert first.status_code == second.status_code == 200
    assert fake_external_apis.count() == calls


@pytest.mark.parametrize(
    "garbage",
    [
        "garbage",
        [],
        {"found": "yes"},
        {"found": True},
        {"found": True, "seasons": "nope"},
        {"found": True, "seasons": ["nope"]},
        {"found": True, "seasons": [{"season_number": 1}]},  # no episodes
        {"found": True, "seasons": [{"season_number": 1, "episodes": [{"title": "no number"}]}]},
        {"found": True, "seasons": [  # the same season twice
            {"season_number": 1, "episodes": []}, {"season_number": 1, "episodes": []},
        ]},
        {"found": True, "seasons": [  # the same episode twice
            {"season_number": 1, "episodes": [{"number": 1}, {"number": 1}]},
        ]},
    ],
)
def test_an_unreadable_cache_entry_is_a_miss(client, auth_headers, fake_external_apis, garbage):
    """US-09: a cache entry with a wrong shape is ignored, and TMDB is asked."""
    series = new_series(client, auth_headers, fake_external_apis)
    cache.set_json(cache_key(series), garbage, 60)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert [s["season_number"] for s in response.json()["seasons"]] == [0, 1, 2]
    assert fake_external_apis.count("tmdb") == 2


# ---------------------------------------------------------------- titles without outside data
def test_a_series_added_by_hand_makes_no_outside_call(client, auth_headers, fake_external_apis):
    """US-09: a series without an outside id has nothing to load. It has no seasons yet."""
    series = create_media(client, auth_headers, media_type="SERIES")

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert response.json()["seasons"] == []
    assert fake_external_apis.count() == 0


def test_a_movie_has_neither_seasons_nor_chapters(client, auth_headers, fake_external_apis):
    """US-09: a movie is a valid title. Both lists are empty."""
    movie = create_media(client, auth_headers, media_type="MOVIE")

    body = open_title(client, auth_headers, movie["id"]).json()

    assert (body["seasons"], body["chapters"]) == ([], [])
    assert fake_external_apis.count() == 0


# ---------------------------------------------------------------- games
def test_game_details_include_the_chapters_in_order(client, auth_headers, media_item, db):
    """US-09: an episodic game returns its chapters, sorted by number."""
    add_chapters(db, media_item["id"], ["Third", "Second"], first_number=3)
    add_chapters(db, media_item["id"], ["First"], first_number=1)
    chapters = open_title(client, auth_headers, media_item["id"]).json()["chapters"]

    assert [c["number"] for c in chapters] == [1, 3, 4]
    assert [c["title"] for c in chapters] == ["First", "Third", "Second"]
    assert all(c["kind"] == "CHAPTER" and isinstance(c["id"], int) for c in chapters)
    assert open_title(client, auth_headers, media_item["id"]).json()["seasons"] == []


def test_a_game_without_chapters_returns_an_empty_list(client, auth_headers, media_item):
    """US-09: a game that is not episodic has no chapters. That is not an error."""
    body = open_title(client, auth_headers, media_item["id"]).json()

    assert body["chapters"] == []


def test_the_chapters_of_one_game_do_not_show_in_another(client, auth_headers, media_item, db):
    """US-09: chapters belong to their own game."""
    other = create_media(client, auth_headers, media_type="GAME")
    add_chapters(db, media_item["id"], ["Only here"])

    assert open_title(client, auth_headers, other["id"]).json()["chapters"] == []


def test_game_details_ask_igdb_for_description_and_genres_only(client, auth_headers, fake_external_apis):
    """US-09: IGDB has no chapter list, so the chapters of a game come from the database. IGDB is
    asked once for the description and the genres, and TMDB is not asked at all."""
    found = client.get("/catalog/search", params={"q": "Life is Strange", "type": "GAME"}, headers=auth_headers)
    game = next(item for item in found.json() if item["title"] == "Life is Strange")
    calls = fake_external_apis.count()

    response = open_title(client, auth_headers, game["id"])

    assert response.status_code == 200
    assert fake_external_apis.count() == calls + 1
    assert fake_external_apis.calls_to("igdb")[-1].body.startswith("fields summary,genres.name; where id = ")
    assert fake_external_apis.calls_to("tmdb") == []


def test_a_game_added_by_hand_makes_no_outside_call(client, auth_headers, fake_external_apis, media_item):
    """US-09: a title without an outside id has nothing to ask for."""
    response = open_title(client, auth_headers, media_item["id"])

    assert response.status_code == 200
    assert fake_external_apis.count() == 0


def test_games_still_work_when_tmdb_is_down(client, auth_headers, fake_external_apis, media_item):
    """NFR-04: a TMDB outage does not touch the details of a game."""
    fake_external_apis.fail("tmdb", status=503, times=None)

    assert open_title(client, auth_headers, media_item["id"]).status_code == 200


# ---------------------------------------------------------------- outside failures (NFR-04)
def test_outage_without_a_saved_copy_returns_503(client, auth_headers, fake_external_apis):
    """NFR-04: TMDB down and the series never loaded is a clear 503 with Retry-After."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=503, times=4)  # all tries of one request

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"
    assert "not available" in response.json()["detail"]


def test_a_failed_load_is_not_cached(client, auth_headers, fake_external_apis):
    """NFR-04: when TMDB is back, the next request loads the series."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=503, times=4)
    assert open_title(client, auth_headers, series["id"]).status_code == 503
    assert cache.get_json(cache_key(series)) is None

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert len(response.json()["seasons"]) == 3


def test_outage_returns_the_saved_copy(client, auth_headers, fake_external_apis):
    """NFR-04: when the cache has expired and TMDB is down, the saved seasons are returned."""
    series = new_series(client, auth_headers, fake_external_apis)
    first = open_title(client, auth_headers, series["id"])
    cache.clear_prefix("omni:catalog:")
    fake_external_apis.fail("tmdb", status=503, times=None)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert response.json() == first.json()
    assert cache.get_json(cache_key(series)) is None  # the old copy is not cached again


def test_missing_tmdb_key_returns_503_for_series_only(client, auth_headers, fake_external_apis, monkeypatch, media_item):
    """NFR-04: with no TMDB key a series cannot be loaded, and a game still works."""
    series = new_series(client, auth_headers, fake_external_apis)
    monkeypatch.setattr(config, "TMDB_API_KEY", "")

    assert open_title(client, auth_headers, series["id"]).status_code == 503
    assert open_title(client, auth_headers, media_item["id"]).status_code == 200
    assert fake_external_apis.count("tmdb") == 0


def test_a_refused_tmdb_key_returns_503(client, auth_headers, fake_external_apis):
    """NFR-04: TMDB answers 401 for the key. That is a 503 for the user, not a 500."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=401, times=None)

    assert open_title(client, auth_headers, series["id"]).status_code == 503
    assert fake_external_apis.count("tmdb") == 1  # a refused key is not tried again


def test_temporary_tmdb_errors_are_retried(client, auth_headers, fake_external_apis):
    """NFR-04: a 500 from TMDB is tried again, and the user sees the result."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.fail("tmdb", status=500, times=2)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert fake_external_apis.count("tmdb") == 4  # 2 failed tries, then the 2 real calls


def test_a_failure_in_a_later_call_saves_nothing(client, auth_headers, fake_external_apis, db):
    """US-09: the series is saved as a whole. When the episode call fails, no season is saved."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.respond("tmdb", {"seasons": [{"season_number": 1, "name": "One"}]})  # call 1 is fine
    fake_external_apis.fail("tmdb", status=500, times=4)  # all tries of call 2

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 503
    assert db.query(Season).filter(Season.media_item_id == series["id"]).count() == 0
    assert db.get(MediaItem, series["id"]).last_synced is None


@pytest.mark.parametrize(
    "body",
    [
        {"seasons": "nope"},
        {"name": "no seasons key"},
        [1, 2, 3],
        b"<html>Bad gateway</html>",
    ],
)
def test_an_unusable_series_answer_returns_503(client, auth_headers, fake_external_apis, body):
    """NFR-04: an answer in the wrong shape is a 503, never a 500."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.respond("tmdb", body)

    assert open_title(client, auth_headers, series["id"]).status_code == 503


def test_an_answer_without_any_season_details_returns_503(client, auth_headers, fake_external_apis):
    """NFR-04: TMDB lists seasons but sends none of them. That is not saved as an empty series."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.respond("tmdb", {"seasons": [{"season_number": 1}, {"season_number": 2}]})
    fake_external_apis.respond("tmdb", {"id": 1})

    assert open_title(client, auth_headers, series["id"]).status_code == 503


def test_a_season_without_details_is_left_out(client, auth_headers, fake_external_apis):
    """US-09: TMDB leaves out a season it cannot load. The other seasons are still saved."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.respond("tmdb", {"seasons": [{"season_number": 1}, {"season_number": 2}]})
    fake_external_apis.respond("tmdb", {"season/2": {"name": "Two", "episodes": [{"episode_number": 1}]}})

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert sorted(seasons_of(response)) == [2]


def test_bad_values_in_an_answer_are_skipped_and_cleaned(client, auth_headers, fake_external_apis):
    """US-09: wrong numbers, dates and names from outside never reach the database."""
    series = new_series(client, auth_headers, fake_external_apis)
    fake_external_apis.respond("tmdb", {"seasons": [
        {"season_number": 1, "name": "ignored name"},
        "not an object",
        {"season_number": True},
        {"season_number": -1},
        {"season_number": "2"},
        {"season_number": 10 ** 9},
        {"season_number": 1, "name": "the same season again"},
    ]})
    fake_external_apis.respond("tmdb", {"season/1": {
        "name": "  Season   One ",
        "air_date": "not a date",
        "episodes": [
            {"episode_number": 1, "name": "x" * 300, "air_date": "2008-13-45", "runtime": -5, "id": 2 ** 40},
            {"episode_number": 1, "name": "the same number again"},
            {"episode_number": 2, "name": "   ", "runtime": 45.5, "id": True},
            {"episode_number": "3", "name": "text number"},
            {"episode_number": -1, "name": "negative"},
            {"name": "no number"},
            "not an object",
            {"episode_number": 4, "name": "Fine", "air_date": "2008-02-03", "runtime": 44, "id": 77},
        ],
    }})

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    seasons = seasons_of(response)
    assert sorted(seasons) == [1]
    assert (seasons[1]["title"], seasons[1]["air_date"]) == ("Season One", None)
    first, second, fine = seasons[1]["episodes"]
    assert first["title"] == "x" * 200
    assert (first["release_date"], first["runtime_minutes"]) == (None, None)
    assert (second["title"], second["runtime_minutes"]) == (None, None)
    assert (fine["number"], fine["title"], fine["runtime_minutes"]) == (4, "Fine", 44)


def test_the_number_of_seasons_and_episodes_is_limited(client, auth_headers, fake_external_apis, monkeypatch):
    """US-09: one series cannot fill the database. The limits are in the TMDB client."""
    monkeypatch.setattr(tmdb, "MAX_SEASONS", 3)
    monkeypatch.setattr(tmdb, "MAX_EPISODES_PER_SEASON", 1)
    series = new_series(client, auth_headers, fake_external_apis, template=70003)

    response = open_title(client, auth_headers, series["id"])

    assert [s["season_number"] for s in response.json()["seasons"]] == [1, 2, 3]
    assert all(len(s["episodes"]) == 1 for s in response.json()["seasons"])
    assert fake_external_apis.count("tmdb") == 2


def test_a_long_tmdb_key_is_sent_as_a_bearer_header(client, auth_headers, fake_external_apis, monkeypatch):
    """US-09: details use the same credentials rules as search."""
    monkeypatch.setattr(config, "TMDB_API_KEY", "eyJ-test-read-access-token")
    series = new_series(client, auth_headers, fake_external_apis)

    # The fake accepts a bearer token only when it equals the configured key
    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    for call in fake_external_apis.calls_to("tmdb"):
        assert call.headers["Authorization"] == "Bearer eyJ-test-read-access-token"
        assert "api_key" not in call.params


# ---------------------------------------------------------------- two requests at the same time
class _SeasonsHiddenOnce:
    """A session that, on its first look at the seasons, finds none, although another request
    has just saved them. The insert that follows then breaks the unique key, as in a real race."""

    def __init__(self, session, media_id):
        self._session = session
        self._media_id = media_id
        self._hidden = False

    def query(self, *args, **kwargs):
        if args and args[0] is Season and not self._hidden:
            self._hidden = True
            other = SessionLocal()
            try:
                season = Season(media_item_id=self._media_id, season_number=1, title="Saved first")
                season.episodes.append(
                    Chapter(media_item_id=self._media_id, number=1, kind=ChapterKind.EPISODE, title="Old")
                )
                other.add(season)
                other.commit()
            finally:
                other.close()

            class _Nothing:
                def options(self, *a, **k):
                    return self

                def filter(self, *a, **k):
                    return []

            return _Nothing()
        return self._session.query(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._session, name)


def test_two_requests_saving_the_same_series_do_not_fail(client, auth_headers, fake_external_apis, db):
    """US-09: when another request saved a season first, the save runs again and updates it."""
    series = new_series(client, auth_headers, fake_external_apis)
    seasons = tmdb.fetch_series_seasons(series["fake_key"])
    assert seasons is not None
    racing_session = _SeasonsHiddenOnce(db, series["id"])

    catalog_service._save_seasons(racing_session, series["id"], seasons)

    rows = db.query(Season).filter(Season.media_item_id == series["id"]).order_by(Season.season_number).all()
    assert [row.season_number for row in rows] == [0, 1, 2]  # season 1 once, not twice
    assert rows[1].title == "Season 1"  # the second try updated it
    assert [e.title for e in rows[1].episodes] == ["Pilot", "Cat's in the Bag...", "...And the Bag's in the River"]


def test_a_save_that_keeps_failing_is_raised(client, auth_headers, fake_external_apis, db, monkeypatch):
    """US-09: the save is tried twice. A second failure is not hidden."""
    series = new_series(client, auth_headers, fake_external_apis)
    calls = []

    def always_fail(*args, **kwargs):
        calls.append(1)
        raise IntegrityError("insert", {}, Exception("duplicate"))

    monkeypatch.setattr(catalog_service, "_save_seasons_once", always_fail)

    with pytest.raises(IntegrityError):
        catalog_service._save_seasons(db, series["id"], [])
    assert len(calls) == 2


# ---------------------------------------------------------------- database rules
def test_a_game_chapter_number_is_unique_inside_its_game(media_item, db):
    """Domain model: the number is unique inside the game when there is no season."""
    add_chapters(db, media_item["id"], ["One"])
    db.add(Chapter(media_item_id=media_item["id"], number=1, kind=ChapterKind.CHAPTER, title="Again"))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_the_same_chapter_number_is_allowed_in_other_games(client, auth_headers, media_item, db):
    other = create_media(client, auth_headers, media_type="GAME")

    add_chapters(db, media_item["id"], ["One"])
    add_chapters(db, other["id"], ["One"])

    assert db.query(Chapter).filter(Chapter.media_item_id.in_([media_item["id"], other["id"]])).count() == 2


def test_an_episode_number_is_unique_inside_its_season(client, auth_headers, fake_external_apis, db):
    """Domain model: the number is unique inside the season. Other seasons may reuse it."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])  # season 1 and season 2 both have an episode 1
    season = db.query(Season).filter_by(media_item_id=series["id"], season_number=1).one()
    db.add(Chapter(media_item_id=series["id"], season_id=season.id, number=1, kind=ChapterKind.EPISODE))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_a_season_number_is_unique_inside_its_series(client, auth_headers, fake_external_apis, db):
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    db.add(Season(media_item_id=series["id"], season_number=1))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize(
    "kind, with_season",
    [(ChapterKind.EPISODE, False), (ChapterKind.CHAPTER, True)],
)
def test_an_episode_needs_a_season_and_a_game_chapter_has_none(client, auth_headers, fake_external_apis, db, kind, with_season):
    """Domain model: an episode points to a season. A game chapter has no season."""
    series = new_series(client, auth_headers, fake_external_apis)
    season = Season(media_item_id=series["id"], season_number=1)
    db.add(season)
    db.flush()
    db.add(Chapter(media_item_id=series["id"], season_id=season.id if with_season else None,
                   number=1, kind=kind))

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field, value", [("number", -1), ("runtime_minutes", -1)])
def test_negative_numbers_are_refused_by_the_database(media_item, db, field, value):
    values = {"number": 1, "runtime_minutes": None, field: value}
    db.add(Chapter(media_item_id=media_item["id"], kind=ChapterKind.CHAPTER, **values))

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_deleting_a_title_deletes_its_seasons_and_chapters(client, auth_headers, fake_external_apis, db):
    """Domain model: the parts of a title are removed with it (ON DELETE CASCADE)."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    game = create_media(client, auth_headers, media_type="GAME")
    add_chapters(db, game["id"], ["One", "Two"])

    db.query(MediaItem).filter(MediaItem.id.in_([series["id"], game["id"]])).delete(synchronize_session=False)
    db.commit()

    assert db.query(Season).filter(Season.media_item_id == series["id"]).count() == 0
    assert db.query(Chapter).filter(Chapter.media_item_id.in_([series["id"], game["id"]])).count() == 0


def test_search_does_not_mark_a_series_as_loaded(client, auth_headers, db):
    """BR-09: a search result has no seasons, so it has no sync time until it is opened."""
    found = client.get("/catalog/search", params={"q": "Breaking Point", "type": "SERIES"}, headers=auth_headers)
    series_id = next(item["id"] for item in found.json() if item["title"] == "Breaking Point")

    assert db.get(MediaItem, series_id).last_synced is None
    assert db.get(MediaItem, series_id).media_type == MediaType.SERIES
