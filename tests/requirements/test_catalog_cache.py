"""The cache module (app/core/cache.py): Redis first, an in-process cache when Redis is down."""
import pytest
import redis

from app.core import cache, config


@pytest.fixture
def redis_down(monkeypatch):
    monkeypatch.setattr(config, "REDIS_URL", "redis://127.0.0.1:1/0")
    cache.reset_connection()
    yield
    cache.reset_connection()


def _redis_is_up() -> bool:
    try:
        return bool(cache._redis().ping())
    except redis.RedisError:
        return False


needs_redis = pytest.mark.skipif(not _redis_is_up(), reason="Redis is not running")


@needs_redis
def test_value_round_trip_in_redis():
    cache.set_json("omni:test:a", {"x": [1, 2]}, 60)

    assert cache.get_json("omni:test:a") == {"x": [1, 2]}
    cache.clear_prefix("omni:test:")


@needs_redis
def test_unreadable_redis_entry_is_a_miss():
    cache._redis().set("omni:test:bad", "{not json", ex=60)

    assert cache.get_json("omni:test:bad") is None
    cache.clear_prefix("omni:test:")


@needs_redis
def test_clear_prefix_keeps_other_keys():
    cache.set_json("omni:test:one", 1, 60)
    cache.set_json("omni:keep:one", 2, 60)

    cache.clear_prefix("omni:test:")

    assert cache.get_json("omni:test:one") is None
    assert cache.get_json("omni:keep:one") == 2
    cache.clear_prefix("omni:keep:")


def test_in_process_cache_is_used_when_redis_is_down(redis_down):
    cache.set_json("omni:test:local", {"ok": True}, 60)

    assert cache.get_json("omni:test:local") == {"ok": True}
    cache.clear_prefix("omni:test:")
    assert cache.get_json("omni:test:local") is None


def test_redis_is_skipped_for_a_while_after_a_failure(redis_down):
    assert cache.get_json("omni:test:missing") is None

    assert cache._redis() is None  # marked as down, so the next calls do not try to connect


def test_in_process_entries_expire(redis_down, monkeypatch):
    class Clock:
        now = 1000.0

        @classmethod
        def monotonic(cls):
            return cls.now

    monkeypatch.setattr(cache, "time", Clock)
    cache.set_json("omni:test:ttl", "v", 10)
    assert cache.get_json("omni:test:ttl") == "v"

    Clock.now += 11

    assert cache.get_json("omni:test:ttl") is None


def test_in_process_cache_has_a_size_limit(redis_down, monkeypatch):
    monkeypatch.setattr(cache, "_LOCAL_MAX_ENTRIES", 3)
    for n in range(5):
        cache.set_json(f"omni:test:limit{n}", n, 60 + n)

    stored = [k for k in cache._local if k.startswith("omni:test:limit")]

    assert len(stored) == 3
    assert "omni:test:limit4" in stored  # the newest entry is kept
    cache.clear_prefix("omni:test:")
