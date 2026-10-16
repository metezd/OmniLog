"""JSON cache for catalog search results.

Redis is used when it can be reached. When Redis is down, an in-process cache takes over, so the
API keeps answering (NFR-04). After a Redis failure Redis is skipped for a short time, so a
broken Redis does not slow down every request.

Key patterns are in docs/analysis/data/er-diagram.md, section 7.
"""
import json
import logging
import threading
import time
from typing import Any, Optional

import redis

from app.core import config

logger = logging.getLogger(__name__)

_REDIS_RETRY_AFTER_SECONDS = 30
_LOCAL_MAX_ENTRIES = 1000

_lock = threading.Lock()
_local: dict[str, tuple[float, str]] = {}  # key -> (expires at, JSON text)
_client: Optional[redis.Redis] = None
_redis_down_until = 0.0


def reset_connection() -> None:
    """Forget the Redis connection and the "Redis is down" mark. Used by tests."""
    global _client, _redis_down_until
    with _lock:
        _client = None
        _redis_down_until = 0.0


def _redis() -> Optional[redis.Redis]:
    global _client
    with _lock:
        if time.monotonic() < _redis_down_until:
            return None
        if _client is None:
            # Short timeouts: a cache must never make a request wait long
            _client = redis.Redis.from_url(
                config.REDIS_URL,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                decode_responses=True,
            )
        return _client


def _mark_redis_down(exc: Exception) -> None:
    global _redis_down_until
    with _lock:
        _redis_down_until = time.monotonic() + _REDIS_RETRY_AFTER_SECONDS
    logger.warning(
        "Redis is unavailable (%s). Using the in-process cache for %s seconds.",
        exc.__class__.__name__,
        _REDIS_RETRY_AFTER_SECONDS,
    )


def get_json(key: str) -> Optional[Any]:
    """Return the cached value, or None on a miss or an unreadable entry."""
    client = _redis()
    if client is not None:
        try:
            text = client.get(key)
        except redis.RedisError as exc:
            _mark_redis_down(exc)
        else:
            return _loads(text)

    with _lock:
        entry = _local.get(key)
        if entry is None:
            return None
        expires_at, text = entry
        if expires_at <= time.monotonic():
            _local.pop(key, None)
            return None
    return _loads(text)


def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    text = json.dumps(value, ensure_ascii=False)
    client = _redis()
    if client is not None:
        try:
            client.set(key, text, ex=ttl_seconds)
            return
        except redis.RedisError as exc:
            _mark_redis_down(exc)

    with _lock:
        now = time.monotonic()
        if len(_local) >= _LOCAL_MAX_ENTRIES:
            for stale in [k for k, (expires, _) in _local.items() if expires <= now]:
                _local.pop(stale, None)
        if len(_local) >= _LOCAL_MAX_ENTRIES:
            # Still full: drop the entry that would expire first
            _local.pop(min(_local, key=lambda k: _local[k][0]), None)
        _local[key] = (now + ttl_seconds, text)


def clear_prefix(prefix: str) -> None:
    """Delete all cached entries whose key starts with the prefix."""
    with _lock:
        for key in [k for k in _local if k.startswith(prefix)]:
            _local.pop(key, None)

    client = _redis()
    if client is None:
        return
    try:
        for key in client.scan_iter(match=f"{prefix}*"):
            client.delete(key)
    except redis.RedisError as exc:
        _mark_redis_down(exc)


def _loads(text: Optional[str]) -> Optional[Any]:
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None
