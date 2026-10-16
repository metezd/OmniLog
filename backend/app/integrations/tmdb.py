"""TMDB client (TV series and movies). Search only. See https://developer.themoviedb.org"""
import logging
from typing import Any, Optional

import requests

from app.core import config
from app.integrations.common import (
    ExternalServiceError,
    ExternalTitle,
    clean_date,
    clean_external_id,
    clean_title,
    clean_url,
    dedupe,
    is_safe_image_path,
    json_body,
    request_with_retry,
)
from app.models.entities import MediaType

logger = logging.getLogger(__name__)

SOURCE = "TMDB"
BASE_URL = "https://api.themoviedb.org/3"
POSTER_URL = "https://image.tmdb.org/t/p/w500{path}"

# media type -> (search path, title field, date field)
_ENDPOINTS = {
    MediaType.SERIES: ("/search/tv", "name", "first_air_date"),
    MediaType.MOVIE: ("/search/movie", "title", "release_date"),
}

_session = requests.Session()


def is_configured() -> bool:
    return bool(config.TMDB_API_KEY)


def search(media_type: MediaType, query: str, limit: int) -> list[ExternalTitle]:
    path, title_field, date_field = _ENDPOINTS[media_type]

    headers = {"Accept": "application/json"}
    params = {"query": query, "include_adult": "false", "page": 1}
    key = config.TMDB_API_KEY
    if key.startswith("eyJ"):
        # The long "API Read Access Token" (a JWT) goes in a header
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key

    response = request_with_retry(
        _session, "GET", BASE_URL + path, source=SOURCE, headers=headers, params=params
    )
    if response.status_code == 401:
        logger.warning("TMDB refused the credentials")
        raise ExternalServiceError("TMDB refused the credentials")
    if response.status_code != 200:
        raise ExternalServiceError(f"TMDB answered {response.status_code}")

    body = json_body(response, SOURCE)
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        raise ExternalServiceError("TMDB sent an unexpected answer")

    titles = (_normalize(item, title_field, date_field) for item in results)
    return dedupe([t for t in titles if t])[:limit]


def _normalize(item: Any, title_field: str, date_field: str) -> Optional[ExternalTitle]:
    if not isinstance(item, dict):
        return None
    external_id = clean_external_id(item.get("id"))
    title = clean_title(item.get(title_field))
    if external_id is None or title is None:
        return None

    path = item.get("poster_path")
    poster_url = clean_url(POSTER_URL.format(path=path)) if is_safe_image_path(path) else None

    return ExternalTitle(
        external_id=external_id,
        title=title,
        poster_url=poster_url,
        release_date=clean_date(item.get(date_field)),
    )
