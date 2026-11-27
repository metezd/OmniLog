"""Work that runs after the answer, so a user request never waits for OpenAI (#382).

A small pool of threads (BACKGROUND_WORKERS) runs the jobs. A job has a key, and a job whose key
is already queued or running is not added again, so opening the same title ten times makes one
embedding, not ten. A job opens its own database session: the session of the request is closed
when the answer is sent.

The jobs live in this process only. When the process stops, a queued job is lost, and the next
request or `python -m app.embeddings` does the work again.
"""
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor, wait
from typing import Callable

from app.core import config

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=config.BACKGROUND_WORKERS, thread_name_prefix="omnilog-background")
_pending: dict[str, Future] = {}


def submit_once(key: str, job: Callable[..., object], *args: object) -> bool:
    """Run job(*args) in the background. False when a job with the same key is still pending."""
    with _lock:
        if key in _pending:
            return False
        future = _executor.submit(_run, key, job, args)
        _pending[key] = future
    return True


def _run(key: str, job: Callable[..., object], args: tuple) -> None:
    try:
        job(*args)
    except Exception:  # noqa: BLE001 - a failed job must not stop the pool
        logger.exception("Background job %s failed", key)
    finally:
        with _lock:
            _pending.pop(key, None)


def wait_idle(timeout: float = 30.0) -> bool:
    """Wait until no job is pending. True when they all ended in time. Used by the tests."""
    with _lock:
        futures = list(_pending.values())
    if not futures:
        return True
    _done, not_done = wait(futures, timeout=timeout)
    return not not_done


def pending() -> int:
    with _lock:
        return len(_pending)
