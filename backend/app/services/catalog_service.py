"""Catalog search (US-08), process 3.2 in docs/analysis/behavior/dfd-epic3-catalog.md.

Order: cache, then the outside API (IGDB for games, TMDB for series and movies). Results are
saved in media_items, so the user can add a result to the library with its id. When the outside
API fails, saved titles that match are returned. When there are none, the caller gets a clear
"unavailable" error (NFR-04).
"""
import hashlib
import logging
import unicodedata
from dataclasses import asdict
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import cache, config
from app.integrations import igdb, tmdb
from app.integrations.common import (
    ExternalServiceError,
    ExternalTitle,
    clean_date,
    clean_external_id,
    clean_title,
    clean_url,
    dedupe,
)
from app.models.entities import MediaItem, MediaType

logger = logging.getLogger(__name__)

SEARCH_RESULT_LIMIT = 10


class InvalidQueryError(Exception):
    """The search text has nothing to search for."""


class CatalogUnavailableError(Exception):
    """The outside catalog failed and nothing saved matches."""


def normalize_query(text: str) -> str:
    """Make the search text safe and the same for equal searches.

    Control characters (such as NUL) become spaces, repeated spaces are joined, and the text is
    put in Unicode NFC form, so "ş" typed in two ways is the same search.
    """
    text = unicodedata.normalize("NFC", text)
    text = "".join(" " if unicodedata.category(ch) in ("Cc", "Zl", "Zp") else ch for ch in text)
    text = text.encode("utf-8", "ignore").decode("utf-8")  # drops lone surrogates
    return " ".join(text.split())


def _cache_key(media_type: MediaType, query: str) -> str:
    # Key pattern from the Redis key dictionary: omni:search:{type}:{query_hash}
    digest = hashlib.sha256(query.casefold().encode("utf-8")).hexdigest()[:32]
    return f"omni:search:{media_type.value}:{digest}"


def search_catalog(db: Session, media_type: MediaType, text: str) -> list[MediaItem]:
    query = normalize_query(text)
    if not query:
        raise InvalidQueryError("The search text cannot be empty")

    key = _cache_key(media_type, query)

    cached = _titles_from_cache(cache.get_json(key))
    if cached is not None:
        return _save(db, media_type, cached)

    try:
        titles = _fetch_external(media_type, query)
    except ExternalServiceError as exc:
        logger.warning("Catalog search for %s failed: %s", media_type.value, exc)
        saved = _search_saved(db, media_type, query)
        if saved:
            return saved
        raise CatalogUnavailableError(
            "The catalog service is not available right now. Please try again later."
        ) from exc

    cache.set_json(key, [asdict(title) for title in titles], config.CACHE_TTL_SECONDS)
    return _save(db, media_type, titles)


def _fetch_external(media_type: MediaType, query: str) -> list[ExternalTitle]:
    if media_type == MediaType.GAME:
        if not igdb.is_configured():
            raise ExternalServiceError("IGDB is not set up")
        return igdb.search_games(query, SEARCH_RESULT_LIMIT)

    if not tmdb.is_configured():
        raise ExternalServiceError("TMDB is not set up")
    return tmdb.search(media_type, query, SEARCH_RESULT_LIMIT)


def _titles_from_cache(cached: object) -> Optional[list[ExternalTitle]]:
    """Rebuild results from the cache. An entry that does not look right counts as a miss."""
    if not isinstance(cached, list):
        return None
    titles = []
    for entry in cached:
        if not isinstance(entry, dict):
            return None
        external_id = clean_external_id(entry.get("external_id"))
        title = clean_title(entry.get("title"))
        if external_id is None or title is None:
            return None
        poster_url = entry.get("poster_url")
        release_date = entry.get("release_date")
        titles.append(
            ExternalTitle(
                external_id=external_id,
                title=title,
                poster_url=clean_url(poster_url) if isinstance(poster_url, str) else None,
                release_date=clean_date(release_date),
            )
        )
    return dedupe(titles)


def _save(db: Session, media_type: MediaType, titles: list[ExternalTitle]) -> list[MediaItem]:
    """Make sure every result is in media_items and return the rows in result order.

    The cache holds outside data only, not row ids. So this also runs on a cache hit. It then
    costs one SELECT, and writes only when a row is missing or has changed.
    """
    if not titles:
        return []

    for attempt in range(2):
        try:
            return _save_once(db, media_type, titles)
        except IntegrityError:
            # Another request saved the same title at the same moment. Run again: the rows
            # exist now, so this time they are found.
            db.rollback()
            if attempt == 1:
                raise
    return []  # not reached


def _save_once(db: Session, media_type: MediaType, titles: list[ExternalTitle]) -> list[MediaItem]:
    existing = {
        item.external_api_id: item
        for item in db.query(MediaItem).filter(
            MediaItem.media_type == media_type,
            MediaItem.external_api_id.in_([t.external_id for t in titles]),
        )
    }

    changed = False
    items = []
    for title in titles:
        item = existing.get(title.external_id)
        if item is None:
            item = MediaItem(
                title=title.title,
                media_type=media_type,
                poster_url=title.poster_url,
                release_date=title.release_date,
                external_api_id=title.external_id,
            )
            db.add(item)
            changed = True
        elif (item.title, item.poster_url, item.release_date) != (
            title.title,
            title.poster_url,
            title.release_date,
        ):
            item.title = title.title
            item.poster_url = title.poster_url
            item.release_date = title.release_date
            changed = True
        items.append(item)

    if not changed:
        return items

    db.flush()  # gives new rows their ids
    ids = [item.id for item in items]
    db.commit()
    # Committing expires the objects. One query loads them again, instead of one per row.
    by_id = {item.id: item for item in db.query(MediaItem).filter(MediaItem.id.in_(ids))}
    return [by_id[item_id] for item_id in ids]


def _search_saved(db: Session, media_type: MediaType, query: str) -> list[MediaItem]:
    """Saved titles that contain the search text. Used when the outside API is down."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return (
        db.query(MediaItem)
        .filter(MediaItem.media_type == media_type, MediaItem.title.ilike(f"%{escaped}%", escape="\\"))
        .order_by(MediaItem.title, MediaItem.id)
        .limit(SEARCH_RESULT_LIMIT)
        .all()
    )
