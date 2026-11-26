"""Efficiency of the calls to IGDB (NFR-01, NFR-04).

Batching: a sync of many games asks IGDB with one query (`where id = (...)`), not one per game.
Field projection: a query asks for explicit fields, never `fields *`.
Outgoing limit: the calls to IGDB are spaced, so IGDB never answers 429 for too many requests.
"""
import itertools
import re
import threading
import time

import pytest

from app.core import cache, config
from app.integrations import common, igdb
from app.integrations.common import ExternalServiceError, RequestLimiter
from app.models.entities import MediaItem, MediaType
from app.services import catalog_service
from helpers import unique

_outside_ids = itertools.count(50_000_000 + time.time_ns() % 900_000_000)


# ---------------------------------------------------------------- helpers
def add_game(client, headers, db, external_id):
    """A game with this outside id that was never synced. The tests share one database and a
    (type, outside id) pair is unique, so a game from an earlier test is reset and reused."""
    item = (
        db.query(MediaItem)
        .filter(MediaItem.media_type == MediaType.GAME, MediaItem.external_api_id == external_id)
        .first()
    )
    if item is None:
        response = client.post(
            "/media",
            json={"title": unique("game"), "media_type": "GAME", "external_api_id": external_id},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]
    item.last_synced, item.description, item.genres = None, None, []
    db.commit()
    return item.id


def igdb_bodies(fake):
    return [call.body for call in fake.calls_to("igdb")]


def sync(db, ids):
    return catalog_service.sync_titles(db, media_type=MediaType.GAME, media_ids=ids)


class FakeClock:
    """Time that only moves when the limiter sleeps, so a test never really waits."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)


@pytest.fixture
def limiter_clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(igdb._limiter, "clock", clock.monotonic)
    monkeypatch.setattr(igdb._limiter, "sleep", clock.sleep)
    monkeypatch.setattr(igdb._limiter, "_next_slot", 0.0)
    return clock


# ---------------------------------------------------------------- batching
def test_a_sync_of_many_games_is_one_igdb_query(client, auth_headers, fake_external_apis, db):
    ids = [add_game(client, auth_headers, db, game_id) for game_id in (90001, 90002, 90003)]
    fake_external_apis.calls.clear()

    report = sync(db, ids)

    assert (report.selected, report.synced) == (3, 3)
    detail_queries = [body for body in igdb_bodies(fake_external_apis) if "where id" in body]
    assert detail_queries == ["fields summary,genres.name; where id = (90001,90002,90003); limit 3;"]
    first = db.get(MediaItem, ids[0])
    assert first.description == "A student discovers that she can rewind time."
    assert sorted(genre.name for genre in first.genres) == ["Adventure", "Indie"]


def test_a_batch_is_split_after_the_maximum_size(client, auth_headers, fake_external_apis, db, monkeypatch):
    monkeypatch.setattr(igdb, "_MAX_BATCH_SIZE", 2)
    ids = [add_game(client, auth_headers, db, game_id) for game_id in (90001, 90002, 90003)]
    fake_external_apis.calls.clear()

    report = sync(db, ids)

    assert report.synced == 3
    detail_queries = [body for body in igdb_bodies(fake_external_apis) if "where id" in body]
    assert len(detail_queries) == 2
    assert "(90001,90002)" in detail_queries[0] and "(90003)" in detail_queries[1]


def test_one_game_is_not_batched(client, auth_headers, fake_external_apis, db):
    ids = [add_game(client, auth_headers, db, 90001)]
    fake_external_apis.calls.clear()

    report = sync(db, ids)

    assert report.synced == 1
    assert [b for b in igdb_bodies(fake_external_apis) if "where id" in b] == [
        "fields summary,genres.name; where id = 90001; limit 1;"
    ]


def test_games_in_the_cache_are_not_asked_for_again(client, auth_headers, fake_external_apis, db):
    ids = [add_game(client, auth_headers, db, game_id) for game_id in (90001, 90002, 90003)]
    client.get(f"/catalog/{ids[0]}", headers=auth_headers)  # 90001 is now in the cache
    db.query(MediaItem).filter(MediaItem.id == ids[0]).update({"last_synced": None})
    db.commit()
    fake_external_apis.calls.clear()

    report = sync(db, ids)

    assert report.synced == 3
    detail_queries = [b for b in igdb_bodies(fake_external_apis) if "where id" in b]
    assert detail_queries == ["fields summary,genres.name; where id = (90002,90003); limit 2;"]


def test_an_unknown_game_stays_unsynced_and_is_cached_as_unknown(
    client, auth_headers, fake_external_apis, db, monkeypatch
):
    monkeypatch.setattr(config, "NEGATIVE_CACHE_TTL_SECONDS", 300)
    known = add_game(client, auth_headers, db, 90001)
    unknown_id = next(_outside_ids)
    unknown = add_game(client, auth_headers, db, unknown_id)

    report = sync(db, [known, unknown])

    assert (report.synced, report.unsynced) == (1, 1)
    assert db.get(MediaItem, unknown).last_synced is None
    cached = cache.get_json(catalog_service._metadata_cache_key(db.get(MediaItem, unknown)))
    assert cached == {"found": False}


def test_a_failed_batch_falls_back_to_one_query_per_game(client, auth_headers, fake_external_apis, db):
    ids = [add_game(client, auth_headers, db, game_id) for game_id in (90001, 90002)]
    fake_external_apis.fail("igdb", status=503, times=config.EXTERNAL_API_MAX_RETRIES + 1)
    fake_external_apis.calls.clear()

    report = sync(db, ids)

    assert report.synced == 2
    single = [b for b in igdb_bodies(fake_external_apis) if re.search(r"where id = \d+;", b)]
    assert len(single) == 2


def test_an_id_that_was_not_asked_for_is_ignored(fake_external_apis, monkeypatch):
    fake_external_apis.respond(
        "igdb",
        [{"id": 90001, "summary": "ok", "genres": []}, {"id": 12345, "summary": "intruder"}],
    )

    found = igdb.fetch_games_details([90001, 90002])

    assert sorted(found) == [90001]


def test_the_keyless_steam_mode_has_no_batch(monkeypatch):
    monkeypatch.setattr(config, "IGDB_CLIENT_ID", "public")

    assert igdb.supports_batching() is False


# ---------------------------------------------------------------- field projection
def test_igdb_queries_ask_for_explicit_fields(client, auth_headers, fake_external_apis, db):
    client.get("/catalog/search", params={"q": "Life is Strange", "type": "GAME"}, headers=auth_headers)
    ids = [add_game(client, auth_headers, db, game_id) for game_id in (90001, 90002)]
    sync(db, ids)

    bodies = igdb_bodies(fake_external_apis)

    assert bodies
    for body in bodies:
        assert "fields *" not in body
        fields = re.search(r"fields ([^;]+);", body).group(1)
        assert fields in {"name,first_release_date,cover.image_id", "summary,genres.name"}


# ---------------------------------------------------------------- outgoing limit
def test_calls_are_spaced_by_the_rate(monkeypatch):
    monkeypatch.setattr(config, "IGDB_MAX_REQUESTS_PER_SECOND", 4)
    clock = FakeClock()
    limiter = RequestLimiter("IGDB", lambda: config.IGDB_MAX_REQUESTS_PER_SECOND)
    limiter.clock, limiter.sleep = clock.monotonic, clock.sleep

    for _ in range(4):
        limiter.acquire()

    assert clock.sleeps == pytest.approx([0.25, 0.5, 0.75])  # the first call goes at once


def test_a_pause_resets_the_spacing(monkeypatch):
    clock = FakeClock()
    limiter = RequestLimiter("IGDB", lambda: 2)
    limiter.clock, limiter.sleep = clock.monotonic, clock.sleep
    limiter.acquire()
    clock.now += 10

    limiter.acquire()

    assert clock.sleeps == []


def test_a_rate_of_zero_turns_the_limit_off():
    clock = FakeClock()
    limiter = RequestLimiter("IGDB", lambda: 0)
    limiter.clock, limiter.sleep = clock.monotonic, clock.sleep

    for _ in range(50):
        limiter.acquire()

    assert clock.sleeps == []


def test_threads_get_different_slots():
    """20 threads at the same moment: every one gets its own slot, none gets the same one."""
    clock = FakeClock()
    lock = threading.Lock()
    limiter = RequestLimiter("IGDB", lambda: 10)
    limiter.clock = clock.monotonic
    limiter.sleep = lambda seconds: (lock.acquire(), clock.sleeps.append(seconds), lock.release())

    threads = [threading.Thread(target=limiter.acquire) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(clock.sleeps) == pytest.approx([i / 10 for i in range(1, 20)])


def test_a_call_that_would_wait_too_long_fails_and_keeps_no_slot():
    clock = FakeClock()
    limiter = RequestLimiter("IGDB", lambda: 1)
    limiter.clock, limiter.sleep = clock.monotonic, clock.sleep
    for _ in range(6):  # the sixth call would wait 5 s: still allowed
        limiter.acquire()
    next_slot = limiter._next_slot

    with pytest.raises(ExternalServiceError, match="too many requests"):
        limiter.acquire()

    assert limiter._next_slot == next_slot


def test_every_igdb_call_waits_for_its_turn(client, auth_headers, fake_external_apis, monkeypatch, limiter_clock):
    monkeypatch.setattr(config, "IGDB_MAX_REQUESTS_PER_SECOND", 3)

    for text in ("Life is Strange", "Life is Strange 2", "Before the Storm"):
        assert client.get("/catalog/search", params={"q": text, "type": "GAME"}, headers=auth_headers).status_code == 200

    assert limiter_clock.sleeps == pytest.approx([1 / 3, 2 / 3])


def test_a_retry_waits_for_its_turn_too(client, auth_headers, fake_external_apis, monkeypatch, limiter_clock):
    monkeypatch.setattr(config, "IGDB_MAX_REQUESTS_PER_SECOND", 3)
    monkeypatch.setattr(common, "sleep", lambda seconds: None)
    fake_external_apis.fail("igdb", status=429, times=1)

    response = client.get("/catalog/search", params={"q": "Life is Strange", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 200
    assert fake_external_apis.count("igdb") == 2
    assert limiter_clock.sleeps == pytest.approx([1 / 3])  # the second try waited for its slot


def test_a_queue_that_is_too_long_gives_503_not_a_hang(client, auth_headers, fake_external_apis, monkeypatch, limiter_clock):
    """Text that no saved title matches has no fallback, so the error is shown."""
    monkeypatch.setattr(config, "IGDB_MAX_REQUESTS_PER_SECOND", 1)
    monkeypatch.setattr(igdb._limiter, "_next_slot", limiter_clock.now + 60)

    response = client.get("/catalog/search", params={"q": "zzzzqqqqxxxxqueue", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 503
    assert fake_external_apis.count("igdb") == 0


@pytest.mark.parametrize("value", ["-1", "-0.5"])
def test_a_negative_rate_stops_the_start(value):
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = dict(os.environ, IGDB_MAX_REQUESTS_PER_SECOND=value)
    result = subprocess.run(  # noqa: S603 - fixed command, no user input
        [sys.executable, "-c", "from app.core import config"],
        cwd=Path(__file__).resolve().parents[2] / "backend",
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0
    assert "IGDB_MAX_REQUESTS_PER_SECOND" in result.stderr
