"""Rate limits for the endpoints that cost CPU, money or a shared quota (#217).

Each limit counts the calls of one key (a client address or a user) in a fixed window of time,
for example 10 calls per minute. The count lives in Redis (INCR with an expiry), so all workers of
the backend share it. When Redis is down, the count lives in this process instead, in the same way
as app/core/cache.py, so the API keeps answering (NFR-04).

The limits are settings in app/core/config.py (RATE_LIMIT_*). The endpoints use them through the
dependencies in app/api/deps.py.
"""
import logging
import math
import threading
import time
from typing import Optional

import redis
from fastapi import HTTPException, status

from app.core import cache, config

logger = logging.getLogger(__name__)

_KEY_PREFIX = "omni:ratelimit:"
_LOCAL_MAX_KEYS = 10_000

_lock = threading.Lock()
_local: dict[str, tuple[int, float]] = {}  # key -> (count, end of the window)


def _limit(name: str) -> tuple[int, int]:
    """(count, period in seconds) of a limit. Read on every call, so tests can change it."""
    return getattr(config, f"RATE_LIMIT_{name.upper()}")


def reset() -> None:
    """Forget the counts kept in this process. Used by tests."""
    with _lock:
        _local.clear()


def _count_in_redis(client: redis.Redis, key: str, period: int) -> int:
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, period)
    return int(pipe.execute()[0])


def _count_locally(key: str, window_end: float, now: float) -> int:
    with _lock:
        if key not in _local and len(_local) >= _LOCAL_MAX_KEYS:
            for stale in [k for k, (_, end) in _local.items() if end <= now]:
                _local.pop(stale, None)
            if len(_local) >= _LOCAL_MAX_KEYS:
                # Still full: drop the key whose window ends first
                _local.pop(min(_local, key=lambda k: _local[k][1]), None)
        count, _ = _local.get(key, (0, window_end))
        count += 1
        _local[key] = (count, window_end)
        return count


def hit(name: str, identity: str) -> Optional[int]:
    """Count one call of `identity` for the limit `name`.

    Returns None when the call is allowed, or the number of seconds until the window ends when the
    limit is reached.
    """
    limit, period = _limit(name)
    now = time.time()
    window = int(now // period)
    window_end = (window + 1) * period
    key = f"{_KEY_PREFIX}{name}:{identity}:{window}"

    count: Optional[int] = None
    client = cache.redis_client()
    if client is not None:
        try:
            count = _count_in_redis(client, key, period)
        except redis.RedisError as exc:
            cache.mark_redis_down(exc)
    if count is None:
        count = _count_locally(key, window_end, now)

    if count <= limit:
        return None
    return max(1, math.ceil(window_end - now))


def check(name: str, identity: str) -> None:
    """Raise 429 with Retry-After when `identity` has used up the limit `name`."""
    if not config.RATE_LIMIT_ENABLED:
        return
    retry_after = hit(name, identity)
    if retry_after is None:
        return
    # The key is not logged: a client address is personal data
    logger.info("Rate limit %s reached", name)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many requests. Try again in {retry_after} seconds.",
        headers={"Retry-After": str(retry_after)},
    )
