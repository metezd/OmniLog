"""TMDB client (TV series and movies). Search, the details of a movie, and a series with its seasons.

See https://developer.themoviedb.org
"""
import logging
import re
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
_UNEXPECTED_ANSWER_MSG = "TMDB sent an unexpected answer"

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
    if config.TMDB_API_KEY == "public":
        return _search_public(media_type, query, limit)

    path, title_field, date_field = _ENDPOINTS[media_type]

    response = _get(path, {"query": query, "include_adult": "false", "page": 1})
    if response.status_code != 200:
        raise ExternalServiceError(f"TMDB answered {response.status_code}")

    body = json_body(response, SOURCE)
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        raise ExternalServiceError(_UNEXPECTED_ANSWER_MSG)

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
    if config.TMDB_API_KEY == "public":
        return _fetch_public_movie_details(external_id)

    # int(): the id is only ever a number in the URL
    response = _get(f"/movie/{int(external_id)}", {})
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ExternalServiceError(f"TMDB answered {response.status_code}")

    body = json_body(response, SOURCE)
    if not isinstance(body, dict):
        raise ExternalServiceError(_UNEXPECTED_ANSWER_MSG)
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
    if config.TMDB_API_KEY == "public":
        return _fetch_public_series(external_id)

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
        raise ExternalServiceError(_UNEXPECTED_ANSWER_MSG)
    return body


def _listed_seasons(show: dict) -> dict[int, dict]:
    """The seasons named in the series answer: season number -> the entry."""
    seasons = show.get("seasons")
    if not isinstance(seasons, list):
        raise ExternalServiceError(_UNEXPECTED_ANSWER_MSG)

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


# ---------------------------------------------------------------- public keyless fallback
def _strip_html(text: Any) -> Optional[str]:
    if not isinstance(text, str):
        return None
    # A tag becomes a space, and runs of spaces become one, so "A <b>big</b> day" stays readable
    return clean_text(" ".join(re.sub(r"<[^>]+>", " ", text).split()))


def _search_public(media_type: MediaType, query: str, limit: int) -> list[ExternalTitle]:
    """Keyless public search via TVMaze (SERIES) and Wikidata (MOVIE) when TMDB_API_KEY='public'."""
    if media_type == MediaType.SERIES:
        return _search_public_series(query, limit)
    return _search_public_movies(query, limit)


def _search_public_series(query: str, limit: int) -> list[ExternalTitle]:
    response = request_with_retry(
        _session,
        "GET",
        "https://api.tvmaze.com/search/shows",
        source=SOURCE,
        params={"q": query},
    )
    if response.status_code != 200:
        raise ExternalServiceError(f"TVMaze answered {response.status_code}")
    body = json_body(response, SOURCE)
    if not isinstance(body, list):
        return []

    results: list[ExternalTitle] = []
    for entry in body[: int(limit)]:
        title = _parse_tvmaze_entry(entry)
        if title is not None:
            results.append(title)
    return dedupe(results)


def _parse_tvmaze_entry(entry: Any) -> Optional[ExternalTitle]:
    show = entry.get("show") if isinstance(entry, dict) else None
    if not isinstance(show, dict):
        return None
    ext_id = clean_external_id(show.get("id"))
    title = clean_title(show.get("name"))
    if ext_id is None or title is None:
        return None
    img = show.get("image") if isinstance(show.get("image"), dict) else {}
    poster = clean_url(img.get("original") or img.get("medium"))
    return ExternalTitle(
        external_id=ext_id,
        title=title,
        poster_url=poster,
        release_date=clean_date(show.get("premiered")),
    )


# Keyless movies come from Wikidata (#370). iTunes stopped answering movie searches in November
# 2026, also for "Titanic". Wikidata needs no key, but asks every client for a User-Agent that names
# it (https://meta.wikimedia.org/wiki/User-Agent_policy).
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
_WIKIDATA_HEADERS = {"Accept": "application/json", "User-Agent": "OmniLog/0.8 (https://github.com/metezd/OmniLog)"}
_WIKIDATA_MAX = 50  # the most items one wbsearchentities or wbgetentities call takes

# "instance of" (P31) values that make an item a movie: film, short film, animated film,
# television film, documentary film, feature film. A soundtrack or a film series is not one.
_FILM_KINDS = frozenset({"Q11424", "Q24862", "Q202866", "Q506240", "Q93204", "Q24869"})
_QID = re.compile(r"^Q([1-9][0-9]{0,9})$")


def _wikidata(params: dict[str, Any]) -> Any:
    response = request_with_retry(
        _session,
        "GET",
        WIKIDATA_API,
        source=SOURCE,
        headers=_WIKIDATA_HEADERS,
        params={**params, "format": "json"},
    )
    if response.status_code != 200:
        raise ExternalServiceError(f"Wikidata answered {response.status_code}")
    return json_body(response, SOURCE)


def _wikidata_entities(ids: list[str], props: str) -> dict[str, Any]:
    if not ids:
        return {}
    body = _wikidata(
        # "mul" is the label for all languages, which many well-known items use instead of "en"
        {"action": "wbgetentities", "ids": "|".join(ids[:_WIKIDATA_MAX]), "props": props, "languages": "en|mul"}
    )
    entities = body.get("entities") if isinstance(body, dict) else None
    return entities if isinstance(entities, dict) else {}


def _claim_values(entity: dict[str, Any], prop: str) -> list[Any]:
    claims = entity.get("claims")
    values = []
    for item in (claims.get(prop) if isinstance(claims, dict) else None) or []:
        try:
            values.append(item["mainsnak"]["datavalue"]["value"])
        except (KeyError, TypeError):
            continue
    return values


def _english(entity: dict[str, Any], field: str) -> Optional[str]:
    """The English text of a field, or the one for all languages ("mul")."""
    for language in ("en", "mul"):
        try:
            value = entity[field][language]["value"]
        except (KeyError, TypeError):
            continue
        if isinstance(value, str):
            return value
    return None


def _is_film(entity: Any) -> bool:
    if not isinstance(entity, dict):
        return False
    return any(isinstance(value, dict) and value.get("id") in _FILM_KINDS for value in _claim_values(entity, "P31"))


def _earliest_release(entity: dict[str, Any]) -> Optional[str]:
    """The earliest publication date (P577) that is known to the day, as YYYY-MM-DD."""
    dates = []
    for value in _claim_values(entity, "P577"):
        if not isinstance(value, dict) or value.get("precision") != 11:
            continue
        time = value.get("time")
        if isinstance(time, str) and time.startswith("+"):
            day = clean_date(time[1:11])
            if day:
                dates.append(day)
    return min(dates) if dates else None


def _search_public_movies(query: str, limit: int) -> list[ExternalTitle]:
    body = _wikidata(
        {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "type": "item",
            # Ask for more than the limit, because songs, albums and series share the titles
            "limit": min(max(int(limit) * 3, 20), _WIKIDATA_MAX),
        }
    )
    found = body.get("search") if isinstance(body, dict) else None
    hits = [item for item in found or [] if isinstance(item, dict) and _QID.match(str(item.get("id", "")))]
    ids = [item["id"] for item in hits]
    search_labels = {item["id"]: item.get("label") for item in hits}
    entities = _wikidata_entities(ids, "labels|claims")

    results: list[ExternalTitle] = []
    for qid in ids:
        entity = entities.get(qid)
        if not _is_film(entity):
            continue
        title = clean_title(_english(entity, "labels") or search_labels.get(qid))
        if title is None:
            continue
        results.append(
            ExternalTitle(
                external_id=int(_QID.match(qid).group(1)),
                title=title,
                poster_url=None,  # posters of films are not free, so Wikidata has none to show
                release_date=_earliest_release(entity),
            )
        )
        if len(results) >= int(limit):
            break
    return dedupe(results)


def _genre_name(label: str) -> str:
    """'science fiction film' -> 'Science Fiction', the form of the other sources."""
    name = re.sub(r"\s+film$", "", label.strip(), flags=re.IGNORECASE)
    return name.title()


def _fetch_public_movie_details(external_id: int) -> Optional[ExternalDetails]:
    qid = f"Q{int(external_id)}"
    try:
        entity = _wikidata_entities([qid], "labels|descriptions|claims").get(qid)
        if not _is_film(entity):
            return None
        genre_ids = [value["id"] for value in _claim_values(entity, "P136") if isinstance(value, dict) and value.get("id")]
        genres = _wikidata_entities(genre_ids, "labels")
    except ExternalServiceError:
        return None
    labels = [_english(genres.get(gid) or {}, "labels") for gid in genre_ids]
    return ExternalDetails(
        description=clean_text(_english(entity, "descriptions")),
        genres=genres_from_entries([{"name": _genre_name(label)} for label in labels if label]),
    )


def _fetch_public_series(external_id: int) -> Optional[ExternalSeries]:
    response = request_with_retry(
        _session,
        "GET",
        f"https://api.tvmaze.com/shows/{int(external_id)}",
        source=SOURCE,
        params=[("embed[]", "seasons"), ("embed[]", "episodes")],
    )
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ExternalServiceError(f"TVMaze answered {response.status_code}")
    show = json_body(response, SOURCE)
    if not isinstance(show, dict):
        return None

    raw_genres = show.get("genres")
    genre_entries = (
        [{"name": g} for g in raw_genres if isinstance(g, str)]
        if isinstance(raw_genres, list)
        else []
    )
    details = ExternalDetails(
        description=_strip_html(show.get("summary")),
        genres=genres_from_entries(genre_entries),
    )
    embedded = show.get("_embedded") if isinstance(show.get("_embedded"), dict) else {}
    raw_seasons = embedded.get("seasons") if isinstance(embedded.get("seasons"), list) else []
    raw_episodes = embedded.get("episodes") if isinstance(embedded.get("episodes"), list) else []

    eps_by_season = _group_public_episodes(raw_episodes)
    seasons = _build_public_seasons(raw_seasons, eps_by_season)
    return ExternalSeries(seasons=seasons, details=details)


def _group_public_episodes(raw_episodes: list[Any]) -> dict[int, dict[int, ExternalEpisode]]:
    eps_by_season: dict[int, dict[int, ExternalEpisode]] = {}
    for ep in raw_episodes:
        if not isinstance(ep, dict):
            continue
        s_num = clean_number(ep.get("season"))
        e_num = clean_number(ep.get("number"))
        if s_num is None or e_num is None:
            continue
        season_eps = eps_by_season.setdefault(s_num, {})
        if e_num not in season_eps and len(season_eps) < MAX_EPISODES_PER_SEASON:
            season_eps[e_num] = ExternalEpisode(
                number=e_num,
                title=clean_title(ep.get("name")),
                release_date=clean_date(ep.get("airdate")),
                runtime_minutes=clean_number(ep.get("runtime")),
                external_id=clean_external_id(ep.get("id")),
            )
    return eps_by_season


def _build_public_seasons(
    raw_seasons: list[Any], eps_by_season: dict[int, dict[int, ExternalEpisode]]
) -> list[ExternalSeason]:
    seasons_by_num: dict[int, ExternalSeason] = {}
    for s in raw_seasons:
        if not isinstance(s, dict):
            continue
        s_num = clean_number(s.get("number"))
        if s_num is None or s_num in seasons_by_num:
            continue
        ep_map = eps_by_season.get(s_num, {})
        seasons_by_num[s_num] = ExternalSeason(
            season_number=s_num,
            title=clean_title(s.get("name")) or f"Season {s_num}",
            air_date=clean_date(s.get("premiereDate")),
            episodes=[ep_map[n] for n in sorted(ep_map)],
        )
    return [seasons_by_num[n] for n in sorted(seasons_by_num)[:MAX_SEASONS]]