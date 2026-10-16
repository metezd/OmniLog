"""Shared pieces for the IGDB and TMDB clients."""
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional

import requests

from app.core import config

logger = logging.getLogger(__name__)

# Never wait longer than this between two tries, even when the source asks for more
_MAX_DELAY_SECONDS = 5.0
_CONNECT_TIMEOUT_SECONDS = 3.05

# Fits the Integer column of media_items.external_api_id
_MAX_EXTERNAL_ID = 2**31 - 1

# Limits of the media_items columns and of the response schema
MAX_TITLE_LENGTH = 200
MAX_URL_LENGTH = 500

# Replaced in tests, so retries do not really wait
sleep = time.sleep


class ExternalServiceError(Exception):
    """An outside API failed, is rate limited, is not set up, or sent data we cannot use."""


@dataclass(frozen=True)
class ExternalTitle:
    """One search result in the OmniLog format (the output of process 3.4)."""

    external_id: int
    title: str
    poster_url: Optional[str]
    release_date: Optional[str]


def request_with_retry(
    session: requests.Session, method: str, url: str, *, source: str, **kwargs: Any
) -> requests.Response:
    """Send a request. Timeouts, connection errors, HTTP 429 and 5xx are tried again with a
    growing wait (NFR-04). Any other answer is returned as it is, for the caller to judge.
    Raises ExternalServiceError when all tries fail.
    """
    tries = max(config.EXTERNAL_API_MAX_RETRIES, 0) + 1
    reason = f"{source} did not answer"

    for attempt in range(tries):
        retry_after = None
        try:
            response = session.request(
                method,
                url,
                timeout=(_CONNECT_TIMEOUT_SECONDS, config.EXTERNAL_API_TIMEOUT_SECONDS),
                **kwargs,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            reason = f"{source} request failed ({exc.__class__.__name__})"
        except requests.exceptions.RequestException as exc:
            # Not a temporary problem, so a retry would not help
            raise ExternalServiceError(
                f"{source} request failed ({exc.__class__.__name__})"
            ) from exc
        else:
            if response.status_code != 429 and response.status_code < 500:
                return response
            reason = f"{source} answered {response.status_code}"
            retry_after = _retry_after_seconds(response)

        if attempt < tries - 1:
            sleep(_delay_seconds(attempt, retry_after))

    raise ExternalServiceError(reason)


def _retry_after_seconds(response: requests.Response) -> Optional[float]:
    value = response.headers.get("Retry-After", "")
    try:
        seconds = float(value)
    except ValueError:
        return None  # a date, or missing. The normal wait is used.
    return seconds if seconds >= 0 else None


def _delay_seconds(attempt: int, retry_after: Optional[float]) -> float:
    wait = config.EXTERNAL_API_BACKOFF_SECONDS * (2**attempt)
    if retry_after is not None:
        wait = max(wait, retry_after)
    return min(wait, _MAX_DELAY_SECONDS)


def json_body(response: requests.Response, source: str) -> Any:
    try:
        return response.json()
    except ValueError as exc:
        raise ExternalServiceError(f"{source} sent an answer that is not JSON") from exc


# ---------------------------------------------------------------- cleaning of outside data
def clean_external_id(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if 0 < value <= _MAX_EXTERNAL_ID else None


def clean_title(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    title = " ".join(value.split())
    return title[:MAX_TITLE_LENGTH] if title else None


def clean_url(value: Optional[str]) -> Optional[str]:
    if value is None or len(value) > MAX_URL_LENGTH:
        return None
    return value


def clean_date(value: Any) -> Optional[str]:
    """Accept a YYYY-MM-DD text only. TMDB sends an empty text for an unknown date."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def date_from_unix(value: Any) -> Optional[str]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


_SAFE_IMAGE_ID = re.compile(r"[A-Za-z0-9_-]{1,50}")
_SAFE_IMAGE_PATH = re.compile(r"/[A-Za-z0-9_.-]{1,100}")


def is_safe_image_id(value: Any) -> bool:
    return isinstance(value, str) and _SAFE_IMAGE_ID.fullmatch(value) is not None


def is_safe_image_path(value: Any) -> bool:
    return isinstance(value, str) and _SAFE_IMAGE_PATH.fullmatch(value) is not None


def dedupe(titles: list[ExternalTitle]) -> list[ExternalTitle]:
    """Keep the first result for each outside id."""
    seen: set[int] = set()
    unique = []
    for title in titles:
        if title.external_id not in seen:
            seen.add(title.external_id)
            unique.append(title)
    return unique
