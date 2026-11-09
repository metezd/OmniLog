"""TMDB client (TV series and movies). Search, the details of a movie, and a series with its seasons.

See https://developer.themoviedb.org
"""
import logging
from typing import Any, Optional

import requests

from app.core import config
from app.integrations.common import (
    MAX_EPISODES_PER_SEASON,
    MAX_SEASONS,
    ExternalDetails,
    ExternalEpisode,
    ExternalSeason,
    ExternalSeries,
    ExternalServiceError,
    ExternalTitle,
    clean_date,
    clean_external_id,
    clean_number,
    clean_text,
    clean_title,
    clean_url,
    dedupe,
    is_safe_image_path,
    json_body,
    request_with_retry,
)
from app.integrations.genres import genres_from_entries
from app.models.entities import MediaType

logger = logging.getLogger(__name__)

SOURCE = "TMDB"
BASE_URL = "https://api.themoviedb.org/3"
POSTER_URL = "https://image.tmdb.org/t/p/w500{path}"

# TMDB answers at most 20 appended sub-requests in one call
SEASONS_PER_REQUEST = 20

# media type -> (search path, title field, date field)
_ENDPOINTS = {
    MediaType.SERIES: ("/search/tv", "name", "first_air_date"),
    MediaType.MOVIE: ("/search/movie", "title", "release_date"),
}

_session = requests.Session()


def is_configured() -> bool:
    return bool(config.TMDB_API_KEY)


def _get(path: str, params: dict[str, Any]) -> requests.Response:
    """Send a GET request with the TMDB credentials. A refused key becomes an error here."""
    headers = {"Accept": "application/json"}
    params = dict(params)
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
    return response


# ---------------------------------------------------------------- search (US-08)
def search(media_type: MediaType, query: str, limit: int) -> list[ExternalTitle]:
    path, title_field, date_field = _ENDPOINTS[media_type]

    response = _get(path, {"query": query, "include_adult": "false", "page": 1})
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


# ---------------------------------------------------------------- details (US-09)
def fetch_movie_details(external_id: int) -> Optional[ExternalDetails]:
    """The description and the genres of a movie. Returns None when TMDB does not know the movie.

    Raises ExternalServiceError when TMDB fails.
    """
    # int(): the id is only ever a number in the URL
    response = _get(f"/movie/{int(external_id)}", {})
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ExternalServiceError(f"TMDB answered {response.status_code}")

    body = json_body(response, SOURCE)
    if not isinstance(body, dict):
        raise ExternalServiceError("TMDB sent an unexpected answer")
    return _details_of(body)


def _details_of(body: dict) -> ExternalDetails:
    """The description and the genres in the answer for a movie or a series."""
    return ExternalDetails(
        description=clean_text(body.get("overview")),
        genres=genres_from_entries(body.get("genres")),
    )


def fetch_series_seasons(external_id: int) -> Optional[list[ExternalSeason]]:
    """The seasons of a series with their episodes, in season order. See fetch_series."""
    series = fetch_series(external_id)
    return None if series is None else series.seasons


def fetch_series(external_id: int) -> Optional[ExternalSeries]:
    """Return a series with its details and its seasons, each with its episodes, in season order.

    Returns None when TMDB does not know the series. Raises ExternalServiceError when TMDB
    fails, so the caller never saves half of a series.

    One call lists the seasons, and it also holds the description and the genres. The episodes
    come from further calls that ask for up to 20 seasons each (`append_to_response`), so a series
    with many seasons needs a few calls, not one call for each season.
    """
    show = _get_series(external_id)
    if show is None:
        return None

    listed = _listed_seasons(show)
    numbers = sorted(listed)

    details: dict[int, dict] = {}
    for start in range(0, len(numbers), SEASONS_PER_REQUEST):
        batch = numbers[start : start + SEASONS_PER_REQUEST]
        body = _get_series(external_id, [f"season/{number}" for number in batch])
        if body is None:
            raise ExternalServiceError("TMDB lost the series between two calls")
        for number in batch:
            detail = body.get(f"season/{number}")
            if isinstance(detail, dict):
                details[number] = detail

    if numbers and not details:
        raise ExternalServiceError("TMDB sent no season details")

    seasons = []
    for number in numbers:
        if number not in details:
            # TMDB leaves out a season it cannot load. It is saved with the next refresh.
            logger.warning("TMDB sent no details for season %s of series %s", number, external_id)
            continue
        seasons.append(_normalize_season(number, listed[number], details[number]))
    return ExternalSeries(seasons=seasons, details=_details_of(show))


def _get_series(external_id: int, append: Optional[list[str]] = None) -> Optional[dict]:
    params = {"append_to_response": ",".join(append)} if append else {}
    # int(): the id is only ever a number in the URL
    response = _get(f"/tv/{int(external_id)}", params)
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ExternalServiceError(f"TMDB answered {response.status_code}")

    body = json_body(response, SOURCE)
    if not isinstance(body, dict):
        raise ExternalServiceError("TMDB sent an unexpected answer")
    return body


def _listed_seasons(show: dict) -> dict[int, dict]:
    """The seasons named in the series answer: season number -> the entry."""
    seasons = show.get("seasons")
    if not isinstance(seasons, list):
        raise ExternalServiceError("TMDB sent an unexpected answer")

    listed: dict[int, dict] = {}
    for entry in seasons:
        if not isinstance(entry, dict):
            continue
        number = clean_number(entry.get("season_number"))
        if number is not None and number not in listed:
            listed[number] = entry

    if len(listed) > MAX_SEASONS:
        logger.warning("TMDB lists %s seasons. Only the first %s are used.", len(listed), MAX_SEASONS)
        listed = {number: listed[number] for number in sorted(listed)[:MAX_SEASONS]}
    return listed


def _normalize_season(number: int, listed: dict, detail: dict) -> ExternalSeason:
    episodes_raw = detail.get("episodes")
    episodes: dict[int, ExternalEpisode] = {}
    if isinstance(episodes_raw, list):
        for raw in episodes_raw[:MAX_EPISODES_PER_SEASON]:
            episode = _normalize_episode(raw)
            if episode is not None and episode.number not in episodes:
                episodes[episode.number] = episode

    return ExternalSeason(
        season_number=number,
        title=clean_title(detail.get("name")) or clean_title(listed.get("name")),
        air_date=clean_date(detail.get("air_date")) or clean_date(listed.get("air_date")),
        episodes=[episodes[n] for n in sorted(episodes)],
    )


def _normalize_episode(raw: Any) -> Optional[ExternalEpisode]:
    if not isinstance(raw, dict):
        return None
    number = clean_number(raw.get("episode_number"))
    if number is None:
        return None
    return ExternalEpisode(
        number=number,
        title=clean_title(raw.get("name")),
        release_date=clean_date(raw.get("air_date")),
        runtime_minutes=clean_number(raw.get("runtime")),
        external_id=clean_external_id(raw.get("id")),
    )
