"""Edge cases for catalog search (US-08, NFR-01, NFR-04).

The outside services are faked at the HTTP level (see fake_external_apis.py), so the real client
code runs: sign-in, request building, retries and reading the answer.
"""
import re
import time

import pytest
import requests

from app.core import cache, config
from app.integrations import common
from app.models.entities import MediaType
from app.services import catalog_service
from helpers import unique

LIFE = "Life is Strange"


def search(client, headers, q, type_="GAME"):
    return client.get("/catalog/search", params={"q": q, "type": type_}, headers=headers)


def titles(response):
    return [item["title"] for item in response.json()]


# ---------------------------------------------------------------- access and validation
def test_search_requires_authentication(client, fake_external_apis):
    """NFR-02: searching without a token returns 401 and calls no outside service."""
    response = client.get("/catalog/search", params={"q": LIFE, "type": "GAME"})

    assert response.status_code == 401
    assert fake_external_apis.count() == 0


@pytest.mark.parametrize(
    "params",
    [
        {"type": "GAME"},  # no q
        {"q": "   ", "type": "GAME"},  # only spaces
        {"q": "\x01\x02\x03", "type": "GAME"},  # only control characters
        {"q": "x" * 101, "type": "GAME"},  # too long
        {"q": LIFE},  # no type
        {"q": LIFE, "type": "BOOK"},  # unknown type
    ],
)
def test_invalid_search_returns_422_without_an_outside_call(client, auth_headers, fake_external_apis, params):
    """US-08: a bad query is a 422, and no outside service is called."""
    response = client.get("/catalog/search", params=params, headers=auth_headers)

    assert response.status_code == 422
    assert fake_external_apis.count() == 0


def test_control_characters_in_the_query_are_removed(client, auth_headers):
    """US-08: a NUL byte inside the text is cleaned up. It must not cause a 500."""
    response = search(client, auth_headers, "Life\x00 is\x07 strange")

    assert response.status_code == 200
    assert LIFE in titles(response)


# ---------------------------------------------------------------- results
def test_game_results_have_the_required_fields(client, auth_headers):
    """US-08: id, title, type, poster URL, release date and outside id are present."""
    response = search(client, auth_headers, LIFE)

    assert response.status_code == 200
    first = next(item for item in response.json() if item["title"] == LIFE)
    assert isinstance(first["id"], int)
    assert first["media_type"] == "GAME"
    assert first["poster_url"] == "https://images.igdb.com/igdb/image/upload/t_cover_big/co1life.jpg"
    assert first["release_date"] == "2015-01-30"
    assert first["external_api_id"] == 90001


def test_game_without_a_cover_has_no_poster(client, auth_headers):
    """US-08: a game without a cover has poster_url null."""
    response = search(client, auth_headers, "Before the Storm")

    assert response.json()[0]["poster_url"] is None


def test_series_search_uses_tmdb(client, auth_headers, fake_external_apis):
    """US-08: series come from the TMDB TV endpoint, with a poster URL and a release date."""
    response = search(client, auth_headers, "Breaking Bad", "SERIES")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["media_type"] == "SERIES"
    assert item["poster_url"] == "https://image.tmdb.org/t/p/w500/bb.jpg"
    assert item["release_date"] == "2008-01-20"
    assert [c.url for c in fake_external_apis.calls_to("tmdb")] == [
        "https://api.themoviedb.org/3/search/tv"
    ]
    assert fake_external_apis.count("igdb") == 0


def test_movie_search_uses_the_tmdb_movie_endpoint(client, auth_headers, fake_external_apis):
    """US-08: movies come from the TMDB movie endpoint."""
    response = search(client, auth_headers, "Blade Runner", "MOVIE")

    assert titles(response) == ["Blade Runner"]
    assert fake_external_apis.calls_to("tmdb")[0].url.endswith("/search/movie")


def test_unknown_release_date_and_poster_are_null(client, auth_headers):
    """US-08: TMDB sends an empty date and no poster for some titles. Both become null."""
    response = search(client, auth_headers, "Breaking Point", "SERIES")

    item = response.json()[0]
    assert item["release_date"] is None
    assert item["poster_url"] is None


def test_long_tmdb_key_is_sent_as_a_bearer_header(client, auth_headers, monkeypatch, fake_external_apis):
    """US-08: the v4 read access token (a JWT) goes in a header, not in the URL."""
    monkeypatch.setattr(config, "TMDB_API_KEY", "eyJ" + "a" * 40)

    response = search(client, auth_headers, "Breaking Bad", "SERIES")

    assert response.status_code == 200
    assert "api_key" not in fake_external_apis.calls_to("tmdb")[0].params


def test_query_cannot_add_igdb_clauses(client, auth_headers, fake_external_apis):
    """US-08: quotes in the text cannot end the IGDB string and add clauses of their own."""
    response = search(client, auth_headers, '" ; fields *; limit 500; search "x')

    assert response.status_code == 200
    body = fake_external_apis.calls_to("igdb")[0].body
    # One quoted string, then exactly the fields and limit clauses we wrote ourselves
    assert re.fullmatch(r'search "[^"]*"; fields [a-z_.,]+; limit 10;', body)


def test_search_text_is_not_sent_in_the_igdb_url(client, auth_headers, fake_external_apis):
    """US-08: the IGDB credentials are never part of a URL."""
    search(client, auth_headers, LIFE)

    urls = " ".join(call.url for call in fake_external_apis.calls)
    assert config.IGDB_CLIENT_SECRET not in urls
    assert "client_secret" not in urls


# ---------------------------------------------------------------- saving and the library
def test_results_are_saved_once_and_keep_their_ids(client, auth_headers):
    """US-08: a title found twice is one catalog row, even after the cache is cleared."""
    first = search(client, auth_headers, LIFE).json()
    cache.clear_prefix("omni:search:")
    second = search(client, auth_headers, LIFE).json()

    assert [i["id"] for i in first] == [i["id"] for i in second]
    from app.core.database import SessionLocal
    from app.models.entities import MediaItem

    with SessionLocal() as db:
        rows = db.query(MediaItem).filter_by(media_type=MediaType.GAME, external_api_id=90001).count()
    assert rows == 1


def test_a_search_result_can_be_added_to_the_library(client, auth_headers):
    """US-08: the goal of the story. Find a title, then add it without typing any details."""
    result = next(i for i in search(client, auth_headers, LIFE).json() if i["title"] == LIFE)

    response = client.post(
        "/library",
        json={"media_item_id": result["id"], "status": "PLAN_TO_WATCH"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["media_item"]["title"] == LIFE


def test_saved_title_is_updated_when_the_source_changes(client, auth_headers, fake_external_apis):
    """US-08: if IGDB sends a new cover, the saved row gets it and keeps its id."""
    before = search(client, auth_headers, LIFE).json()[0]
    cache.clear_prefix("omni:search:")
    changed = {"id": 90001, "name": LIFE, "first_release_date": 1422576000, "cover": {"image_id": "conew"}}
    fake_external_apis.respond("igdb", [changed])

    after = search(client, auth_headers, LIFE).json()[0]

    assert after["id"] == before["id"]
    assert after["poster_url"].endswith("/conew.jpg")


def test_manual_titles_with_the_same_outside_id_are_a_conflict(client, auth_headers):
    """Catalog: two rows with the same type and outside id are not allowed. POST /media says 409."""
    outside_id = time.time_ns() % 10**9
    payload = {"title": unique("dup"), "media_type": "GAME", "external_api_id": outside_id}

    first = client.post("/media", json=payload, headers=auth_headers)
    second = client.post("/media", json=payload, headers=auth_headers)
    other_type = client.post("/media", json={**payload, "media_type": "SERIES"}, headers=auth_headers)

    assert (first.status_code, second.status_code, other_type.status_code) == (201, 409, 201)


# ---------------------------------------------------------------- cache (US-08 criterion 3, NFR-01)
def test_repeated_search_does_not_call_the_outside_api(client, auth_headers, fake_external_apis):
    """US-08: the same search a second time is answered from the cache."""
    first = search(client, auth_headers, LIFE)
    calls_after_first = fake_external_apis.count()

    second = search(client, auth_headers, LIFE)

    assert calls_after_first == 2  # sign-in and one search
    assert fake_external_apis.count() == calls_after_first
    assert second.json() == first.json()


def test_equal_searches_share_one_cache_entry(client, auth_headers, fake_external_apis):
    """US-08: capital letters and extra spaces do not make a new search."""
    search(client, auth_headers, LIFE)
    calls = fake_external_apis.count()

    response = search(client, auth_headers, "  LIFE   is  strange ")

    assert response.status_code == 200
    assert fake_external_apis.count() == calls


def test_the_cache_is_separate_for_each_type(client, auth_headers, fake_external_apis):
    """US-08: the same text for another type is a new search."""
    search(client, auth_headers, "Breaking", "SERIES")
    search(client, auth_headers, "Breaking", "MOVIE")

    assert fake_external_apis.count("tmdb") == 2


def test_a_search_with_no_match_is_cached_too(client, auth_headers, fake_external_apis):
    """US-08: an empty answer is cached as well, so the same search is not repeated."""
    assert search(client, auth_headers, "zzzznomatch").json() == []
    calls = fake_external_apis.count()

    assert search(client, auth_headers, "zzzznomatch").json() == []
    assert fake_external_apis.count() == calls


def test_an_unreadable_cache_entry_is_a_miss(client, auth_headers, fake_external_apis):
    """US-08: a cache entry with a wrong shape is ignored, and the outside API is asked."""
    key = catalog_service._cache_key(MediaType.GAME, LIFE)
    cache.set_json(key, "garbage", 60)

    response = search(client, auth_headers, LIFE)

    assert response.status_code == 200
    assert fake_external_apis.count("igdb") == 1


def test_search_works_when_redis_is_down(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: with Redis down, the in-process cache keeps repeated searches off the outside API."""
    monkeypatch.setattr(config, "REDIS_URL", "redis://127.0.0.1:1/0")
    cache.reset_connection()

    first = search(client, auth_headers, LIFE)
    calls = fake_external_apis.count()
    second = search(client, auth_headers, LIFE)

    assert first.status_code == second.status_code == 200
    assert fake_external_apis.count() == calls


# ---------------------------------------------------------------- sign-in to IGDB
def test_igdb_access_token_is_reused(client, auth_headers, fake_external_apis):
    """US-08: one sign-in serves many searches."""
    search(client, auth_headers, LIFE)
    search(client, auth_headers, "Before the Storm")

    assert fake_external_apis.count("twitch") == 1
    assert fake_external_apis.count("igdb") == 2


def test_expired_igdb_access_token_is_renewed(client, auth_headers, fake_external_apis):
    """US-08: when IGDB answers 401, a new token is requested once and the search is repeated."""
    search(client, auth_headers, LIFE)
    fake_external_apis.expire_tokens()

    response = search(client, auth_headers, "Before the Storm")

    assert response.status_code == 200
    assert fake_external_apis.count("twitch") == 2


def test_igdb_sign_in_refused_returns_503(client, auth_headers, fake_external_apis):
    """NFR-04: wrong IGDB credentials are a 503, not a 500."""
    fake_external_apis.fail("twitch", status=403, times=None)

    response = search(client, auth_headers, unique("nomatch"))

    assert response.status_code == 503


# ---------------------------------------------------------------- outside failures (NFR-04)
def test_outage_without_saved_titles_returns_503(client, auth_headers, fake_external_apis):
    """NFR-04: IGDB down and nothing saved means a clear 503 with Retry-After."""
    fake_external_apis.fail("igdb", status=503, times=None)

    response = search(client, auth_headers, "uncached query")

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"
    assert "try again" in response.json()["detail"].lower()


def test_outage_returns_saved_titles_that_match(client, auth_headers, fake_external_apis):
    """NFR-04: when the outside API is down, saved titles that match are returned."""
    saved = search(client, auth_headers, LIFE).json()
    cache.clear_prefix("omni:search:")
    fake_external_apis.fail("igdb", status=503, times=None)

    response = search(client, auth_headers, "life is strange")

    assert response.status_code == 200
    assert {i["id"] for i in response.json()} >= {i["id"] for i in saved if i["title"] == LIFE}


def test_saved_titles_from_an_outage_are_not_cached(client, auth_headers, fake_external_apis):
    """NFR-04: an answer made from saved titles must not hide the real result later."""
    search(client, auth_headers, LIFE)
    cache.clear_prefix("omni:search:")
    fake_external_apis.fail("igdb", status=503, times=4)  # all tries of the first search fail
    search(client, auth_headers, LIFE)
    calls = fake_external_apis.count("igdb")

    search(client, auth_headers, LIFE)  # the service is back

    assert fake_external_apis.count("igdb") == calls + 1


def test_saved_titles_are_only_used_for_the_same_type(client, auth_headers, fake_external_apis):
    """NFR-04: a saved series is not returned for a game search."""
    search(client, auth_headers, "Breaking Bad", "SERIES")
    fake_external_apis.fail("igdb", status=503, times=None)

    response = search(client, auth_headers, "Breaking Bad", "GAME")

    assert response.status_code == 503


def test_percent_and_underscore_are_literal_in_the_saved_title_search(client, auth_headers, fake_external_apis):
    """NFR-04: % in the text matches a real %, not "anything"."""
    prefix = unique("wild")
    for name in (f"{prefix} 50% off", f"{prefix} 50 percent off"):
        client.post("/media", json={"title": name, "media_type": "GAME"}, headers=auth_headers)
    fake_external_apis.fail("twitch", status=503, times=None)

    response = search(client, auth_headers, f"{prefix} 50% off")

    assert titles(response) == [f"{prefix} 50% off"]


def test_temporary_errors_are_retried(client, auth_headers, fake_external_apis):
    """NFR-04: two 503 answers and then success is a 200."""
    fake_external_apis.fail("igdb", status=503, times=2)

    response = search(client, auth_headers, LIFE)

    assert response.status_code == 200
    assert fake_external_apis.count("igdb") == 3


def test_retries_stop_after_the_maximum(client, auth_headers, fake_external_apis):
    """NFR-04: the first try plus 3 retries, then 503."""
    fake_external_apis.fail("igdb", status=500, times=None)

    response = search(client, auth_headers, unique("nomatch"))

    assert response.status_code == 503
    assert fake_external_apis.count("igdb") == config.EXTERNAL_API_MAX_RETRIES + 1


def test_timeouts_are_retried_and_end_in_503(client, auth_headers, fake_external_apis):
    """NFR-04: a service that never answers is a 503 after the retries."""
    fake_external_apis.fail("tmdb", exception=requests.exceptions.Timeout(), times=None)

    response = search(client, auth_headers, unique("nomatch"), "SERIES")

    assert response.status_code == 503
    assert fake_external_apis.count("tmdb") == config.EXTERNAL_API_MAX_RETRIES + 1


def test_errors_that_a_retry_cannot_fix_are_not_retried(client, auth_headers, fake_external_apis):
    """NFR-04: an invalid URL error is a 503 after one call."""
    fake_external_apis.fail("tmdb", exception=requests.exceptions.InvalidURL(), times=None)

    response = search(client, auth_headers, unique("nomatch"), "SERIES")

    assert response.status_code == 503
    assert fake_external_apis.count("tmdb") == 1


def test_rate_limit_answer_waits_as_asked(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: after HTTP 429 the client waits for Retry-After, then tries again."""
    waits = []
    monkeypatch.setattr(common, "sleep", waits.append)
    fake_external_apis.fail("igdb", status=429, headers={"Retry-After": "2"}, times=1)

    response = search(client, auth_headers, LIFE)

    assert response.status_code == 200
    assert waits == [2.0]


def test_a_very_long_retry_after_is_capped(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: a request never waits more than 5 seconds between tries."""
    waits = []
    monkeypatch.setattr(common, "sleep", waits.append)
    fake_external_apis.fail("igdb", status=429, headers={"Retry-After": "9999"}, times=1)

    search(client, auth_headers, LIFE)

    assert waits == [5.0]


def test_the_wait_between_retries_doubles(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: exponential backoff: 0.5, 1, 2 seconds."""
    waits = []
    monkeypatch.setattr(common, "sleep", waits.append)
    monkeypatch.setattr(config, "EXTERNAL_API_BACKOFF_SECONDS", 0.5)
    fake_external_apis.fail("igdb", status=502, times=None)

    search(client, auth_headers, LIFE)

    assert waits == [0.5, 1.0, 2.0]


@pytest.mark.parametrize(
    "service, body, type_",
    [
        ("igdb", {"message": "not a list"}, "GAME"),
        ("igdb", b"<html>Bad gateway</html>", "GAME"),
        ("tmdb", {"results": "nope"}, "SERIES"),
        ("tmdb", [1, 2, 3], "SERIES"),
    ],
)
def test_unusable_answers_return_503(client, auth_headers, fake_external_apis, service, body, type_):
    """NFR-04: an answer in the wrong shape is a 503, never a 500."""
    fake_external_apis.respond(service, body)

    response = search(client, auth_headers, unique("nomatch"), type_)

    assert response.status_code == 503


def test_missing_credentials_return_503_for_that_source_only(client, auth_headers, fake_external_apis, monkeypatch):
    """NFR-04: with no IGDB keys games return 503, and series still work."""
    monkeypatch.setattr(config, "IGDB_CLIENT_ID", "")

    games = search(client, auth_headers, unique("nomatch"))
    series = search(client, auth_headers, "Breaking Bad", "SERIES")

    assert games.status_code == 503
    assert series.status_code == 200
    assert fake_external_apis.count("igdb") == 0


def test_bad_items_in_an_answer_are_skipped_and_values_are_cleaned(client, auth_headers, fake_external_apis):
    """US-08: items without an id or a name are skipped. Long titles and bad values are cleaned."""
    fake_external_apis.respond("igdb", [
        {"id": 1},                                    # no name
        {"name": "No id"},                            # no id
        "not an object",
        {"id": True, "name": "Boolean id"},
        {"id": 2 ** 40, "name": "Id too large"},
        {"id": 5, "name": "x" * 300, "first_release_date": 10 ** 20, "cover": {"image_id": "../evil"}},
        {"id": 6, "name": "  Good   Title ", "first_release_date": 1422576000},
        {"id": 6, "name": "Same id again"},
    ])

    response = search(client, auth_headers, "anything")

    assert response.status_code == 200
    long_title, good = response.json()
    assert long_title["title"] == "x" * 200
    assert long_title["release_date"] is None and long_title["poster_url"] is None
    assert good["title"] == "Good Title" and good["release_date"] == "2015-01-30"


def test_results_are_limited_to_ten(client, auth_headers, fake_external_apis):
    """US-08: at most 10 results."""
    fake_external_apis.respond(
        "tmdb", {"results": [{"id": 1000 + n, "name": f"Show {n}"} for n in range(20)]}
    )

    assert len(search(client, auth_headers, "Show", "SERIES").json()) == 10


# ---------------------------------------------------------------- query clean-up
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  a   b  ", "a b"),
        ("a\tb\nc", "a b c"),
        ("a\x00b", "a b"),
        ("\x1f", ""),
        ("s\u0327", "\u015f"),  # s + combining cedilla becomes one letter
    ],
)
def test_normalize_query(raw, expected):
    """US-08: control characters and spaces are cleaned, and Unicode is put in NFC form."""
    assert catalog_service.normalize_query(raw) == expected
    assert re.fullmatch(r"[^\x00-\x1f]*", catalog_service.normalize_query(raw))
