"""Multi-layer cache: Redis (L1), PostgreSQL (L2) and the negative cache (NFR-01, NFR-04).

L2: a title whose details were loaded less than DB_CACHE_TTL_DAYS ago is served from its saved
rows, with no call to Redis or to the outside service.
Negative cache: an empty answer from IGDB or TMDB is cached for the short
NEGATIVE_CACHE_TTL_SECONDS only.
Redis: REDIS_URL can be a managed Redis with TLS (rediss://), such as Upstash.
"""
import copy
import itertools
import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import pytest
import redis

from app.core import cache, config
from app.core.clock import utc_now
from app.models.entities import MediaItem
from app.services import catalog_service
from fake_external_apis import SERIES_DETAILS
from helpers import unique

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"

# Every test that loads a series gets an outside id of its own (the tests share one database)
_outside_ids = itertools.count(30_000_000 + time.time_ns() % 900_000_000)


# ---------------------------------------------------------------- helpers
@pytest.fixture
def db_cache_on(monkeypatch):
    """Turn L2 on (it is off in the other tests, see tests/conftest.py)."""
    monkeypatch.setattr(config, "DB_CACHE_TTL_DAYS", 7)


@pytest.fixture
def recorded_ttls(monkeypatch):
    """Record (key, ttl) of every cache write, so a test does not need a running Redis."""
    writes = []
    real = cache.set_json

    def record(key, value, ttl_seconds):
        writes.append((key, ttl_seconds))
        real(key, value, ttl_seconds)

    monkeypatch.setattr(cache, "set_json", record)
    return writes


def new_series(client, headers, fake, template=70001):
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


def open_title(client, headers, media_id):
    return client.get(f"/catalog/{media_id}", headers=headers)


def search(client, headers, text, media_type="GAME"):
    return client.get("/catalog/search", params={"q": text, "type": media_type}, headers=headers)


def age_last_synced(db, media_id, days):
    db.query(MediaItem).filter(MediaItem.id == media_id).update(
        {"last_synced": utc_now() - timedelta(days=days)}
    )
    db.commit()


# ---------------------------------------------------------------- L2: the database cache
def test_a_recently_loaded_title_is_served_from_the_database(
    client, auth_headers, fake_external_apis, db_cache_on
):
    """Redis lost the entry, but the saved rows are young: no call to TMDB."""
    series = new_series(client, auth_headers, fake_external_apis)
    first = open_title(client, auth_headers, series["id"])
    calls = fake_external_apis.count("tmdb")
    cache.clear_prefix("omni:catalog:")

    second = open_title(client, auth_headers, series["id"])

    assert second.status_code == 200
    assert fake_external_apis.count("tmdb") == calls
    assert second.json()["seasons"] == first.json()["seasons"]
    assert cache.get_json(catalog_service._details_cache_key(series["fake_key"])) is None


def test_a_game_is_served_from_the_database_too(client, auth_headers, fake_external_apis, db_cache_on):
    """The same rule for the description and genres of a game (IGDB)."""
    found = search(client, auth_headers, "Life is Strange").json()
    game = next(item for item in found if item["external_api_id"] == 90001)
    open_title(client, auth_headers, game["id"])
    calls = fake_external_apis.count("igdb")
    cache.clear_prefix("omni:catalog:")

    response = open_title(client, auth_headers, game["id"])

    assert response.status_code == 200
    assert fake_external_apis.count("igdb") == calls
    assert set(response.json()["genres"]) == {"Adventure", "Indie"}


def test_an_old_title_is_loaded_again(client, auth_headers, fake_external_apis, db, db_cache_on):
    """After DB_CACHE_TTL_DAYS the title goes to TMDB again, and last_synced moves forward."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    age_last_synced(db, series["id"], days=8)
    show = fake_external_apis.series[series["fake_key"]]
    next(s for s in show["seasons"] if s["season_number"] == 1)["name"] = "The Beginning"
    cache.clear_prefix("omni:catalog:")
    calls = fake_external_apis.count("tmdb")

    response = open_title(client, auth_headers, series["id"])

    assert fake_external_apis.count("tmdb") > calls
    seasons = {s["season_number"]: s for s in response.json()["seasons"]}
    assert seasons[1]["title"] == "The Beginning"
    db.expire_all()
    assert utc_now() - db.get(MediaItem, series["id"]).last_synced < timedelta(minutes=1)


def test_an_old_title_is_still_served_when_tmdb_is_down(
    client, auth_headers, fake_external_apis, db, db_cache_on
):
    """NFR-04: an expired saved copy is better than an error."""
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    age_last_synced(db, series["id"], days=30)
    cache.clear_prefix("omni:catalog:")
    fake_external_apis.fail("tmdb", status=503, times=None)

    response = open_title(client, auth_headers, series["id"])

    assert response.status_code == 200
    assert len(response.json()["seasons"]) == 3


def test_the_database_cache_can_be_turned_off(client, auth_headers, fake_external_apis, monkeypatch):
    """DB_CACHE_TTL_DAYS=0 keeps the old behavior: every cache miss asks the outside service."""
    monkeypatch.setattr(config, "DB_CACHE_TTL_DAYS", 0)
    series = new_series(client, auth_headers, fake_external_apis)
    open_title(client, auth_headers, series["id"])
    calls = fake_external_apis.count("tmdb")
    cache.clear_prefix("omni:catalog:")

    open_title(client, auth_headers, series["id"])

    assert fake_external_apis.count("tmdb") > calls


def test_a_title_that_was_never_loaded_is_not_fresh(client, auth_headers, fake_external_apis, db_cache_on):
    series = new_series(client, auth_headers, fake_external_apis)

    response = open_title(client, auth_headers, series["id"])

    assert fake_external_apis.count("tmdb") > 0
    assert len(response.json()["seasons"]) == 3


@pytest.mark.parametrize(
    ("last_synced_days_ago", "ttl_days", "expected"),
    [
        (None, 7, False),  # never loaded
        (0, 7, True),
        (6.9, 7, True),
        (7.1, 7, False),
        (1, 0, False),  # turned off
        (-1, 7, False),  # a time in the future is not trusted
        (0.4, 0.5, True),  # a fraction of a day works
    ],
)
def test_is_fresh(monkeypatch, last_synced_days_ago, ttl_days, expected):
    monkeypatch.setattr(config, "DB_CACHE_TTL_DAYS", ttl_days)
    item = MediaItem(title="x", external_api_id=1)
    if last_synced_days_ago is not None:
        item.last_synced = utc_now() - timedelta(days=last_synced_days_ago)

    assert catalog_service.is_fresh(item) is expected


# ---------------------------------------------------------------- negative cache: search
def test_an_empty_search_is_cached_for_a_short_time(
    client, auth_headers, fake_external_apis, recorded_ttls, monkeypatch
):
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)
    assert search(client, auth_headers, "zzzzqqqqxxxxnonexistenttitle").json() == []
    calls = fake_external_apis.count()

    assert search(client, auth_headers, "zzzzqqqqxxxxnonexistenttitle").json() == []

    assert fake_external_apis.count() == calls
    key = catalog_service._cache_key(
        catalog_service.MediaType.GAME, catalog_service.normalize_query("zzzzqqqqxxxxnonexistenttitle")
    )
    assert (key, 300) in recorded_ttls
    assert all(ttl != config.CACHE_TTL_SECONDS for stored_key, ttl in recorded_ttls if stored_key == key)


def test_a_search_with_results_keeps_the_long_ttl(
    client, auth_headers, fake_external_apis, recorded_ttls, monkeypatch
):
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)

    search(client, auth_headers, "Life is Strange")

    ttls = [ttl for key, ttl in recorded_ttls if key.startswith("omni:search:")]
    assert ttls == [config.CACHE_TTL_SECONDS]


def test_the_negative_search_cache_can_be_turned_off(client, auth_headers, fake_external_apis, monkeypatch):
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 0)
    search(client, auth_headers, "zzzzqqqqxxxxnonexistenttitle")
    calls = fake_external_apis.count()

    search(client, auth_headers, "zzzzqqqqxxxxnonexistenttitle")

    assert fake_external_apis.count() > calls


def test_a_failed_search_is_not_cached_as_empty(client, auth_headers, fake_external_apis, monkeypatch):
    """An outage is not "no result": the failure leaves no entry, so the next search asks again."""
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)
    text = "zzzzqqqqxxxxoutagecheck"  # no saved title matches, so there is no fallback
    key = catalog_service._cache_key(catalog_service.MediaType.GAME, text)
    fake_external_apis.fail("igdb", status=503, times=None)
    assert search(client, auth_headers, text).status_code == 503
    assert cache.get_json(key) is None
    fake_external_apis._scripted.clear()
    calls = fake_external_apis.count("igdb")

    response = search(client, auth_headers, text)

    assert response.status_code == 200
    assert fake_external_apis.count("igdb") > calls  # it really asked IGDB again


# ---------------------------------------------------------------- negative cache: details
def test_an_unknown_series_is_cached_with_the_short_ttl(
    client, auth_headers, fake_external_apis, recorded_ttls, monkeypatch
):
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)
    series = new_series(client, auth_headers, fake_external_apis)
    del fake_external_apis.series[series["fake_key"]]

    open_title(client, auth_headers, series["id"])

    key = catalog_service._details_cache_key(series["fake_key"])
    assert [ttl for stored_key, ttl in recorded_ttls if stored_key == key] == [300]


def test_a_known_series_keeps_the_long_details_ttl(
    client, auth_headers, fake_external_apis, recorded_ttls
):
    series = new_series(client, auth_headers, fake_external_apis)

    open_title(client, auth_headers, series["id"])

    key = catalog_service._details_cache_key(series["fake_key"])
    assert [ttl for stored_key, ttl in recorded_ttls if stored_key == key] == [
        config.DETAILS_CACHE_TTL_SECONDS
    ]


def test_an_unknown_title_is_asked_for_again_after_the_short_ttl(
    client, auth_headers, fake_external_apis, monkeypatch
):
    """The title can appear at TMDB later, so the miss must not live as long as a hit."""
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)
    series = new_series(client, auth_headers, fake_external_apis)
    show = fake_external_apis.series.pop(series["fake_key"])
    open_title(client, auth_headers, series["id"])
    fake_external_apis.series[series["fake_key"]] = show
    cache.clear_prefix("omni:catalog:")  # stands for the end of the short TTL

    response = open_title(client, auth_headers, series["id"])

    assert len(response.json()["seasons"]) == 3


# ---------------------------------------------------------------- Redis: a managed instance
def test_a_tls_address_makes_a_tls_connection(monkeypatch):
    """Upstash gives a rediss:// address. The client is built without connecting."""
    monkeypatch.setattr(config, "REDIS_URL", "rediss://default:secret@example.upstash.io:6379")
    cache.reset_connection()
    try:
        client = cache._redis()

        assert client is not None
        pool = client.connection_pool
        assert pool.connection_class is redis.SSLConnection
        assert pool.connection_kwargs["host"] == "example.upstash.io"
    finally:
        cache.reset_connection()


def test_the_redis_timeout_is_a_setting(monkeypatch):
    monkeypatch.setattr(config, "REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setattr(config, "REDIS_SOCKET_TIMEOUT_SECONDS", 2.5)
    cache.reset_connection()
    try:
        kwargs = cache._redis().connection_pool.connection_kwargs

        assert kwargs["socket_timeout"] == 2.5
        assert kwargs["socket_connect_timeout"] == 2.5
    finally:
        cache.reset_connection()


def test_the_connection_string_is_not_logged_when_redis_fails(monkeypatch, caplog):
    """The address of a managed Redis holds its password."""
    monkeypatch.setattr(config, "REDIS_URL", "redis://:topsecretvalue@127.0.0.1:1/0")
    cache.reset_connection()
    try:
        cache.get_json("omni:test:missing")
    finally:
        cache.reset_connection()

    assert "topsecretvalue" not in caplog.text


# ---------------------------------------------------------------- settings are checked at start
def _setting(name, value):
    env = dict(os.environ)
    env[name] = value
    return subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", f"from app.core import config; print(config.{name})"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("DB_CACHE_TTL_DAYS", "14", "14.0"),
        ("DB_CACHE_TTL_DAYS", "0", "0.0"),
        ("NEGATIVE_CACHE_TTL_SECONDS", "600", "600"),
        ("NEGATIVE_CACHE_TTL_SECONDS", "0", "0"),
        ("REDIS_SOCKET_TIMEOUT_SECONDS", "1", "1.0"),
    ],
)
def test_cache_settings_are_read(name, value, expected):
    result = _setting(name, value)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DB_CACHE_TTL_DAYS", "-1"),
        ("NEGATIVE_CACHE_TTL_SECONDS", "-5"),
        ("REDIS_SOCKET_TIMEOUT_SECONDS", "0"),
    ],
)
def test_bad_cache_settings_stop_the_start(name, value):
    result = _setting(name, value)

    assert result.returncode != 0
    assert name in result.stderr


def test_cache_defaults():
    env = {k: v for k, v in os.environ.items()
           if k not in ("DB_CACHE_TTL_DAYS", "NEGATIVE_CACHE_TTL_SECONDS", "REDIS_SOCKET_TIMEOUT_SECONDS")}
    result = subprocess.run(  # noqa: S603 - fixed command, no user input
        [
            sys.executable,
            "-c",
            "from app.core import config; "
            "print(config.DB_CACHE_TTL_DAYS, config.NEGATIVE_CACHE_TTL_SECONDS, config.REDIS_SOCKET_TIMEOUT_SECONDS)",
        ],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["7.0", "300", "0.5"]
