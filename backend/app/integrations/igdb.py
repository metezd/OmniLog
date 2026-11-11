"""IGDB client (games). Search, and the details of a game.

IGDB uses Twitch OAuth: the client id and secret are exchanged for an access token, which is
sent with every request. See https://api-docs.igdb.com
"""
import logging
import threading
import time
from typing import Any, Optional

import requests

from app.core import config
from app.integrations.genres import genres_from_entries
from app.integrations.common import (
    ExternalDetails,
    ExternalServiceError,
    ExternalTitle,
    clean_external_id,
    clean_text,
    clean_title,
    clean_url,
    date_from_unix,
    dedupe,
    is_safe_image_id,
    json_body,
    request_with_retry,
)

logger = logging.getLogger(__name__)

SOURCE = "IGDB"
AUTH_URL = "https://id.twitch.tv/oauth2/token"
GAMES_URL = "https://api.igdb.com/v4/games"
COVER_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"

# Renew the access token a little before it runs out
_EXPIRY_MARGIN_SECONDS = 60

_session = requests.Session()
_auth_lock = threading.Lock()
_access_token: Optional[str] = None
_access_token_expires_at = 0.0


def is_configured() -> bool:
    return bool(config.IGDB_CLIENT_ID and config.IGDB_CLIENT_SECRET)


def reset_access_token() -> None:
    """Forget the stored access token. Used by tests."""
    global _access_token, _access_token_expires_at
    with _auth_lock:
        _access_token = None
        _access_token_expires_at = 0.0


def _get_access_token(rejected: Optional[str] = None) -> str:
    """Return a valid access token. `rejected` is a token IGDB just refused: it is replaced,
    unless another request has already done so."""
    global _access_token, _access_token_expires_at
    with _auth_lock:
        still_valid = _access_token and time.monotonic() < _access_token_expires_at
        if still_valid and _access_token != rejected:
            return _access_token

        response = request_with_retry(
            _session,
            "POST",
            AUTH_URL,
            source=SOURCE,
            # In the body, not in the URL, so the secret does not end up in logs
            data={
                "client_id": config.IGDB_CLIENT_ID,
                "client_secret": config.IGDB_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        if response.status_code != 200:
            logger.warning("IGDB sign-in was refused with status %s", response.status_code)
            raise ExternalServiceError("IGDB sign-in was refused")

        body = json_body(response, SOURCE)
        token = body.get("access_token") if isinstance(body, dict) else None
        expires_in = body.get("expires_in") if isinstance(body, dict) else None
        if not isinstance(token, str) or not token:
            raise ExternalServiceError("IGDB sign-in answer has no access token")
        if isinstance(expires_in, bool) or not isinstance(expires_in, (int, float)):
            expires_in = 0  # unknown lifetime: use it for this request only

        _access_token = token
        _access_token_expires_at = time.monotonic() + max(expires_in - _EXPIRY_MARGIN_SECONDS, 0)
        return token


def _quoted(text: str) -> str:
    """Put text into an Apicalypse string. Quotes and backslashes are removed, so the text can
    never end the string and add its own clauses."""
    safe = text.replace("\\", " ").replace('"', " ")
    return f'"{" ".join(safe.split())}"'


def search_games(query: str, limit: int) -> list[ExternalTitle]:
    if config.IGDB_CLIENT_ID == "public":
        return _search_steam_games(query, limit)
    games = _query(
        f"search {_quoted(query)}; "
        "fields name,first_release_date,cover.image_id; "
        f"limit {int(limit)};"
    )
    return dedupe([t for t in (_normalize(game) for game in games) if t])


def fetch_game_details(external_id: int) -> Optional[ExternalDetails]:
    """The description and the genres of a game. Returns None when IGDB does not know the game.

    Raises ExternalServiceError when IGDB fails.
    """
    if config.IGDB_CLIENT_ID == "public":
        return _fetch_steam_game_details(external_id)
    games = _query(f"fields summary,genres.name; where id = {int(external_id)}; limit 1;")
    game = games[0] if games else None
    if not isinstance(game, dict):
        return None
    return ExternalDetails(
        description=clean_text(game.get("summary")),
        genres=genres_from_entries(game.get("genres")),
    )


def _search_steam_games(query: str, limit: int) -> list[ExternalTitle]:
    """Keyless public game search via Steam Store API when IGDB_CLIENT_ID='public'."""
    response = request_with_retry(
        _session,
        "GET",
        "https://store.steampowered.com/api/storesearch/",
        source=SOURCE,
        params={"term": query, "l": "english", "cc": "US"},
    )
    if response.status_code != 200:
        raise ExternalServiceError(f"Steam Store answered {response.status_code}")
    body = json_body(response, SOURCE)
    items = body.get("items") if isinstance(body, dict) else None
    if not isinstance(items, list):
        return []
    results: list[ExternalTitle] = []
    for item in items[: int(limit)]:
        if not isinstance(item, dict):
            continue
        ext_id = clean_external_id(item.get("id"))
        title = clean_title(item.get("name"))
        if ext_id is None or title is None:
            continue
        poster = clean_url(
            f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{ext_id}/library_600x900.jpg"
        ) or clean_url(item.get("tiny_image"))
        results.append(
            ExternalTitle(
                external_id=ext_id,
                title=title,
                poster_url=poster,
                release_date=None,
            )
        )
    return dedupe(results)


def _fetch_steam_game_details(external_id: int) -> Optional[ExternalDetails]:
    """Keyless public game details via Steam Store API when IGDB_CLIENT_ID='public'."""
    response = request_with_retry(
        _session,
        "GET",
        "https://store.steampowered.com/api/appdetails",
        source=SOURCE,
        params={"appids": int(external_id), "l": "english"},
    )
    if response.status_code != 200:
        return None
    body = json_body(response, SOURCE)
    entry = body.get(str(int(external_id))) if isinstance(body, dict) else None
    if not isinstance(entry, dict) or not entry.get("success"):
        return None
    data = entry.get("data")
    if not isinstance(data, dict):
        return None
    raw_genres = data.get("genres")
    genre_entries = (
        [{"name": g.get("description")} for g in raw_genres if isinstance(g, dict)]
        if isinstance(raw_genres, list)
        else []
    )
    return ExternalDetails(
        description=clean_text(data.get("short_description")),
        genres=genres_from_entries(genre_entries),
    )


def _query(body: str) -> list:
    """Send an Apicalypse query to IGDB and return the list that it answers."""
    rejected: Optional[str] = None
    for attempt in range(2):
        access_token = _get_access_token(rejected)
        response = request_with_retry(
            _session,
            "POST",
            GAMES_URL,
            source=SOURCE,
            headers={
                "Client-ID": config.IGDB_CLIENT_ID,
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            data=body.encode("utf-8"),
        )
        if response.status_code == 401 and attempt == 0:
            rejected = access_token  # expired or revoked: get a new one and try once more
            continue
        break

    if response.status_code != 200:
        raise ExternalServiceError(f"IGDB answered {response.status_code}")

    games = json_body(response, SOURCE)
    if not isinstance(games, list):
        raise ExternalServiceError("IGDB sent an unexpected answer")
    return games


def _normalize(game: Any) -> Optional[ExternalTitle]:
    if not isinstance(game, dict):
        return None
    external_id = clean_external_id(game.get("id"))
    title = clean_title(game.get("name"))
    if external_id is None or title is None:
        return None

    cover = game.get("cover")
    image_id = cover.get("image_id") if isinstance(cover, dict) else None
    poster_url = clean_url(COVER_URL.format(image_id=image_id)) if is_safe_image_id(image_id) else None

    return ExternalTitle(
        external_id=external_id,
        title=title,
        poster_url=poster_url,
        release_date=date_from_unix(game.get("first_release_date")),
    )
