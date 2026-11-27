
"""OpenAI integration for embeddings and spoiler detection."""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

from app.core import config
from app.integrations.common import ExternalServiceError

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

# After a failed call, OpenAI is not called again until this time (time.monotonic()), so a slow or
# broken OpenAI costs one wait, not one wait for every request (#382)
_cooldown_lock = threading.Lock()
_down_until = 0.0


def reset_cooldown() -> None:
    """Forget an earlier failure. Used by the tests."""
    global _down_until
    with _cooldown_lock:
        _down_until = 0.0


def _mark_down(exc: Exception) -> None:
    """Pause OpenAI after a failure that the next call would likely meet too: no connection, a
    timeout, too many requests (429) or a server error (5xx). A refused request (4xx) does not
    pause it, since another text may work."""
    global _down_until
    if isinstance(exc, APIStatusError) and exc.status_code < 500 and exc.status_code != 429:
        return
    if config.OPENAI_COOLDOWN_SECONDS <= 0:
        return
    with _cooldown_lock:
        _down_until = time.monotonic() + config.OPENAI_COOLDOWN_SECONDS
    logger.warning("OpenAI is not called for %s seconds after a failure", config.OPENAI_COOLDOWN_SECONDS)


def _check_cooldown() -> None:
    with _cooldown_lock:
        cooling = time.monotonic() < _down_until
    if cooling:
        raise ExternalServiceError("OpenAI failed a moment ago and is not called for now")


def _get_client() -> OpenAI:
    """Return an OpenAI client or raise a safe service error."""
    global _client

    if not config.OPENAI_API_KEY:
        raise ExternalServiceError("OpenAI is not configured")

    if _client is None:
        _client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=config.OPENAI_TIMEOUT_SECONDS,
            max_retries=max(config.OPENAI_MAX_RETRIES, 0),
        )

    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector for each input text."""
    if not texts:
        return []

    cleaned_texts = [text.strip() for text in texts]

    if any(not text for text in cleaned_texts):
        raise ValueError("Embedding texts must not be empty")

    _check_cooldown()
    try:
        client = _get_client()
        response = client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=cleaned_texts,
            dimensions=config.EMBEDDING_DIMENSIONS,
        )

        vectors = [item.embedding for item in response.data]

        if len(vectors) != len(cleaned_texts):
            raise ExternalServiceError("OpenAI returned an unexpected number of embeddings")

        for vector in vectors:
            if len(vector) != config.EMBEDDING_DIMENSIONS:
                raise ExternalServiceError("OpenAI returned an unexpected embedding dimension")
            if not all(math.isfinite(value) for value in vector):
                raise ExternalServiceError("OpenAI returned an invalid embedding")

        return vectors

    except ExternalServiceError:
        raise
    except (APIConnectionError, APITimeoutError, APIStatusError) as exc:
        logger.warning("OpenAI embedding request failed (%s)", type(exc).__name__)
        _mark_down(exc)
        raise ExternalServiceError("OpenAI embedding service is unavailable") from exc
    except Exception as exc:
        logger.warning("OpenAI embedding request failed (%s)", type(exc).__name__)
        raise ExternalServiceError("OpenAI embedding service failed") from exc


def classify_spoiler(text: str) -> tuple[bool, float]:
    """Return (contains_spoiler, score) for the supplied text."""
    cleaned_text = text.strip()

    if not cleaned_text:
        return False, 0.0

    _check_cooldown()
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=config.SPOILER_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify whether a review reveals important plot spoilers. "
                        "Return only JSON with a boolean 'contains_spoiler' and a numeric "
                        "'score' from 0 to 1. A spoiler includes major character deaths, "
                        "hidden identities, betrayals, and ending revelations."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Review text to classify:\n"
                        + cleaned_text
                    ),
                },
            ],
        )

        import json

        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise ExternalServiceError("OpenAI returned an empty spoiler classification")

        result: Any = json.loads(content)
        if not isinstance(result, dict):
            raise ExternalServiceError("OpenAI returned an invalid spoiler classification")

        contains_spoiler = result.get("contains_spoiler")
        score = result.get("score")

        if not isinstance(contains_spoiler, bool):
            raise ExternalServiceError("OpenAI returned an invalid spoiler classification")

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ExternalServiceError("OpenAI returned an invalid spoiler score")

        score = float(score)
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ExternalServiceError("OpenAI returned an invalid spoiler score")

        return score >= config.SPOILER_THRESHOLD and contains_spoiler, score

    except ExternalServiceError:
        raise
    except (APIConnectionError, APITimeoutError, APIStatusError) as exc:
        logger.warning("OpenAI spoiler request failed (%s)", type(exc).__name__)
        _mark_down(exc)
        raise ExternalServiceError("OpenAI spoiler service is unavailable") from exc
    except Exception as exc:
        logger.warning("OpenAI spoiler request failed (%s)", type(exc).__name__)
        raise ExternalServiceError("OpenAI spoiler classification failed") from exc
