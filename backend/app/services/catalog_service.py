"""Catalog search (US-08) and title details (US-09), processes 3.1 and 3.2 in
docs/analysis/behavior/dfd-epic3-catalog.md.

Search order: cache, then the outside API (IGDB for games, TMDB for series and movies). Results are
saved in media_items, so the user can add a result to the library with its id. When the outside
API fails, saved titles that match are returned. When there are none, the caller gets a clear
"unavailable" error (NFR-04).

Title details: a series gets its seasons and episodes from TMDB (cache first), and they are saved
in `seasons` and `chapters`. The chapters of a game have no outside source, so they are only read
from the database (the seed in app/seed puts them there). Every chapter and episode comes with its
decision points and their options (US-12). Every title with an outside id also gets its description
and genres: games from IGDB, movies and series from TMDB (cache first, US-09). When TMDB fails for a
series, the saved copy is returned, or the "unavailable" error when the series was never loaded.
For a game or a movie a failure is not an error: the title is shown with what is saved.

Layers: Redis is the first cache (L1) and PostgreSQL is the second (L2). A title whose details
were loaded less than DB_CACHE_TTL_DAYS ago (media_items.last_synced) is served from its saved
rows, with no call to Redis or to the outside service. Empty answers (a search with no result, an
id that the service does not know) are cached for the short NEGATIVE_CACHE_TTL_SECONDS, so a miss
does not reach the outside API again and again.
"""
import hashlib
import logging
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import cache, config
from app.core.clock import utc_now
from app.integrations import igdb, tmdb
from app.integrations.common import (
    ExternalDetails,
    ExternalEpisode,
    ExternalSeason,
    ExternalServiceError,
    ExternalTitle,
    clean_date,
    clean_external_id,
    clean_number,
    clean_text,
    clean_title,
    clean_url,
    dedupe,
)
from app.integrations.genres import normalize_genres
from app.services.embedding_service import schedule_embedding
from app.models.entities import Chapter, ChapterKind, DecisionPoint, Genre, MediaItem, MediaType, Season

logger = logging.getLogger(__name__)

SEARCH_RESULT_LIMIT = 10
_TMDB_NOT_CONFIGURED_MSG = "TMDB is not set up"


class InvalidQueryError(Exception):
    """The search text has nothing to search for."""


class CatalogUnavailableError(Exception):
    """The outside catalog failed and nothing saved can be used instead."""


class TitleNotFoundError(Exception):
    """No title has this id."""


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

    _cache_search_result(key, titles)
    return _save(db, media_type, titles)


def _cache_search_result(key: str, titles: list[ExternalTitle]) -> None:
    """Cache a search result. An empty result is cached too (negative cache), but only for the
    short NEGATIVE_CACHE_TTL_SECONDS. A failed call never gets here, so it is never cached."""
    if titles:
        cache.set_json(key, [asdict(title) for title in titles], config.CACHE_TTL_SECONDS)
    elif config.NEGATIVE_CACHE_TTL_SECONDS > 0:
        cache.set_json(key, [], config.NEGATIVE_CACHE_TTL_SECONDS)


def _fetch_external(media_type: MediaType, query: str) -> list[ExternalTitle]:
    if media_type == MediaType.GAME:
        if not igdb.is_configured():
            raise ExternalServiceError("IGDB is not set up")
        return igdb.search_games(query, SEARCH_RESULT_LIMIT)

    if not tmdb.is_configured():
        raise ExternalServiceError(_TMDB_NOT_CONFIGURED_MSG)
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


# - title details (US-09)
def ensure_title_details(db: Session, item: MediaItem) -> None:
    """Make sure a title has its description and genres (and seasons for a series).

    Option 1 for issue #125: load details when a title is added to the library, so that
    titles added directly from search results without visiting their details page still have
    complete genres for personal statistics (US-15) and recommendations (US-13).

    If the title was added by hand (no external_api_id) or has already been synced,
    this is a no-op. Any failure from outside catalog services is caught and ignored so that
    adding to the library is never blocked (NFR-04).
    """
    if item.external_api_id is None or item.last_synced is not None:
        return

    try:
        if item.media_type == MediaType.SERIES:
            _refresh_series(db, item)
        else:
            _refresh_details(db, item)
    except Exception as exc:
        db.rollback()
        logger.warning(
            "Could not fetch details for media %s (%s) on library addition: %s",
            item.id,
            item.title,
            exc,
        )


@dataclass(frozen=True)
class SyncReport:
    """What a manual sync did (UC-EP3-03)."""

    selected: int  # titles that were unsynced and matched the filters
    synced: int  # titles that now have their details saved
    unsynced: int  # no data was saved: the outside service failed or does not know the id
    errors: int  # titles for which loading raised an error (the log has the reason)
    not_selected: int  # asked for by id, but unknown, added by hand or already synced


def sync_titles(
    db: Session,
    *,
    media_type: Optional[MediaType] = None,
    media_ids: Optional[list[int]] = None,
    limit: Optional[int] = None,
) -> SyncReport:
    """Load details and genres for the titles that have an outside id and were never synced.

    This is the manual sync (UC-EP3-03). It is the same load as when a title is opened, so the
    cache, the retries and the "an empty value never replaces a saved one" rule are the same.
    Titles that are already synced are left alone. One failing title never stops the others.

    media_type and media_ids narrow the choice, and limit stops after that many titles (oldest id
    first). A title that the outside service does not know stays unsynced and is tried again by the
    next run.
    """
    query = db.query(MediaItem).filter(
        MediaItem.external_api_id.isnot(None), MediaItem.last_synced.is_(None)
    )
    if media_type is not None:
        query = query.filter(MediaItem.media_type == media_type)
    if media_ids:
        query = query.filter(MediaItem.id.in_(media_ids))
    query = query.order_by(MediaItem.id)
    if limit is not None:
        query = query.limit(limit)
    items = query.all()
    item_ids = [item.id for item in items]

    _prefetch_game_details(items)

    synced = unsynced = errors = 0
    for item_id in item_ids:
        item = db.get(MediaItem, item_id)
        try:
            if item.media_type == MediaType.SERIES:
                _refresh_series(db, item)
            else:
                _refresh_details(db, item)
        except Exception as exc:
            db.rollback()
            errors += 1
            logger.warning("Failed to sync details for media %s: %s", item_id, exc)
            continue
        db.refresh(item)
        if item.last_synced is not None:
            synced += 1
        else:
            unsynced += 1

    not_selected = len(set(media_ids)) - len(item_ids) if media_ids else 0
    return SyncReport(
        selected=len(item_ids),
        synced=synced,
        unsynced=unsynced,
        errors=errors,
        not_selected=max(not_selected, 0),
    )


def _prefetch_game_details(items: list[MediaItem]) -> None:
    """Ask IGDB for the details of many games at once, and put them in the cache.

    One query (`where id = (...)`) serves up to 100 games, so a sync of many games does not send
    one request for each of them. The loop of the sync then finds every game in the cache, which
    is the same path as a normal load. A game that IGDB does not know is cached as unknown, for the
    short negative TTL. When the batch fails, nothing is cached and the loop asks for each game
    on its own, as before. Games that are already in the cache are not asked for again.
    """
    if not igdb.supports_batching():
        return
    missing = [
        item
        for item in items
        if item.media_type == MediaType.GAME
        and _details_from_cache(cache.get_json(_metadata_cache_key(item))) is None
    ]
    if len(missing) < 2:
        return  # one game costs one query either way

    try:
        found = igdb.fetch_games_details(item.external_api_id for item in missing)
    except ExternalServiceError as exc:
        logger.warning("Batch of %s games failed, loading them one by one: %s", len(missing), exc)
        return
    for item in missing:
        details = found.get(item.external_api_id)
        outside = (
            _OutsideDetails(found=True, details=details)
            if details is not None
            else _OutsideDetails(found=False, details=_NO_DETAILS)
        )
        _cache_outside(_metadata_cache_key(item), _details_to_cache(outside), outside.found)


def count_unsynced(
    db: Session, *, media_type: Optional[MediaType] = None, media_ids: Optional[list[int]] = None
) -> int:
    """How many titles a sync with the same filters would try (used by the dry run)."""
    query = db.query(func.count(MediaItem.id)).filter(
        MediaItem.external_api_id.isnot(None), MediaItem.last_synced.is_(None)
    )
    if media_type is not None:
        query = query.filter(MediaItem.media_type == media_type)
    if media_ids:
        query = query.filter(MediaItem.id.in_(media_ids))
    return query.scalar() or 0


def sync_missing_details(db: Session) -> int:
    """Sync every unsynced title with an outside id. Returns how many now have their details.

    Kept for the callers of issue #125. New code uses sync_titles, which also reports the titles
    that could not be synced.
    """
    return sync_titles(db).synced


def get_title_details(db: Session, media_id: int) -> MediaItem:
    """Return a title with its description and genres, and its seasons and episodes (series) or its
    chapters (games).

    A movie has no seasons and no chapters, so both lists are empty. Raises TitleNotFoundError for
    an unknown id.
    """
    item = db.get(MediaItem, media_id)
    if item is None:
        raise TitleNotFoundError("Title not found")

    # Only a title with an outside id can be loaded. A title that was added by hand has none.
    # A title that was loaded recently is served from the database (L2), with no outside call.
    if item.external_api_id is not None and (
        not is_fresh(item) or _series_lacks_runtimes(db, item)
    ):
        if item.media_type == MediaType.SERIES:
            _refresh_series(db, item)
        else:
            _refresh_details(db, item)

    item = _load_details(db, media_id)
    # The embedding is made after the answer, so the page never waits for OpenAI (#382)
    schedule_embedding(db, item)
    return item


def is_fresh(item: MediaItem) -> bool:
    """True when the saved details of the title are younger than DB_CACHE_TTL_DAYS.

    A title that was never loaded (last_synced is empty) is never fresh. A time in the future,
    from a clock that was wrong, is not trusted: the title is loaded again.
    """
    ttl_days = config.DB_CACHE_TTL_DAYS
    if ttl_days <= 0 or item.last_synced is None:
        return False
    age = utc_now() - item.last_synced
    return timedelta(0) <= age < timedelta(days=ttl_days)


def _series_lacks_runtimes(db: Session, item: MediaItem) -> bool:
    """True when an episode of the series was saved without a length (#411).

    Episodes saved before the runtime fallback have none, so such a series is loaded again once,
    even when its saved copy is fresh. After that every episode has a length.
    """
    if item.media_type != MediaType.SERIES:
        return False
    missing = (
        db.query(Chapter.id)
        .filter(
            Chapter.media_item_id == item.id,
            Chapter.kind == ChapterKind.EPISODE,
            or_(Chapter.runtime_minutes.is_(None), Chapter.runtime_minutes == 0),
        )
        .limit(1)
        .first()
    )
    return missing is not None


def _load_details(db: Session, media_id: int) -> MediaItem:
    """Load the title with its seasons, episodes, chapters and their decision points.

    The number of queries is fixed (eight), however many parts the title has.
    """
    return (
        db.query(MediaItem)
        .options(
            selectinload(MediaItem.seasons)
            .selectinload(Season.episodes)
            .selectinload(Chapter.decision_points)
            .selectinload(DecisionPoint.options),
            selectinload(MediaItem.chapters)
            .selectinload(Chapter.decision_points)
            .selectinload(DecisionPoint.options),
        )
        .filter(MediaItem.id == media_id)
        .populate_existing()
        .one()
    )


@dataclass(frozen=True)
class _OutsideSeasons:
    """What the outside service knows about the seasons of a series."""

    found: bool  # False when TMDB does not know the series
    seasons: list[ExternalSeason]
    details: ExternalDetails


def _details_cache_key(external_id: int) -> str:
    # Key pattern from the Redis key dictionary: omni:catalog:{source}:{external_id}. TMDB ids of
    # series and movies are different number spaces, so the source says "tmdb_tv".
    return f"omni:catalog:tmdb_tv:{external_id}"


def _refresh_series(db: Session, item: MediaItem) -> None:
    """Make sure the seasons of the series are saved. Order: cache, then TMDB.

    The cache holds outside data only, not row ids (the same rule as for search). A cache hit
    means the data is fresh, so TMDB is not called. The saved copy is only written on a hit when
    the series was never saved. When TMDB fails, the saved copy is used, even if it is old.
    """
    key = _details_cache_key(item.external_api_id)
    outside = _outside_from_cache(cache.get_json(key))
    from_cache = outside is not None

    if outside is None:
        try:
            outside = _fetch_series_seasons(item.external_api_id)
        except ExternalServiceError as exc:
            logger.warning("Details of series %s failed: %s", item.id, exc)
            if item.last_synced is not None:
                return  # an older saved copy is better than an error
            raise CatalogUnavailableError(
                "The catalog service is not available right now. Please try again later."
            ) from exc
        _cache_outside(key, _outside_to_cache(outside), outside.found)

    if not outside.found:
        return  # TMDB does not know this id. There is nothing to save.
    if from_cache and item.last_synced is not None:
        return  # the saved copy is already there
    _save_seasons(db, item.id, outside.seasons)
    _save_details(db, item.id, outside.details)


def _cache_outside(key: str, value: dict, found: bool) -> None:
    """Cache the details of one title. A title that the service does not know is cached only for
    the short NEGATIVE_CACHE_TTL_SECONDS (negative cache): it can appear at the source later."""
    if found:
        cache.set_json(key, value, config.DETAILS_CACHE_TTL_SECONDS)
    elif config.NEGATIVE_CACHE_TTL_SECONDS > 0:
        cache.set_json(key, value, config.NEGATIVE_CACHE_TTL_SECONDS)


def _fetch_series_seasons(external_id: int) -> _OutsideSeasons:
    if not tmdb.is_configured():
        raise ExternalServiceError(_TMDB_NOT_CONFIGURED_MSG)
    series = tmdb.fetch_series(external_id)
    if series is None:
        return _OutsideSeasons(found=False, seasons=[], details=_NO_DETAILS)
    return _OutsideSeasons(found=True, seasons=series.seasons, details=series.details)


def _outside_to_cache(outside: _OutsideSeasons) -> dict:
    if not outside.found:
        return {"found": False}
    return {
        "found": True,
        "seasons": [asdict(season) for season in outside.seasons],
        **_details_to_cache_fields(outside.details),
    }


def _outside_from_cache(cached: object) -> Optional[_OutsideSeasons]:
    """Rebuild the seasons from the cache. An entry that does not look right counts as a miss."""
    if not isinstance(cached, dict):
        return None
    if cached.get("found") is False:
        return _OutsideSeasons(found=False, seasons=[], details=_NO_DETAILS)

    raw_seasons = cached.get("seasons")
    if cached.get("found") is not True or not isinstance(raw_seasons, list):
        return None
    # An entry from before the details were cached has no description and genres. It counts as a
    # miss, so they are loaded from TMDB and saved.
    details = _details_from_cache_fields(cached)
    if details is None:
        return None

    seasons = []
    for raw in raw_seasons:
        season = _season_from_cache(raw)
        if season is None:
            return None
        seasons.append(season)
    if len({season.season_number for season in seasons}) != len(seasons):
        return None  # a season twice would break the unique key when it is saved
    return _OutsideSeasons(found=True, seasons=seasons, details=details)


def _season_from_cache(raw: object) -> Optional[ExternalSeason]:
    if not isinstance(raw, dict):
        return None
    number = clean_number(raw.get("season_number"))
    raw_episodes = raw.get("episodes")
    if number is None or not isinstance(raw_episodes, list):
        return None

    episodes = []
    for entry in raw_episodes:
        if not isinstance(entry, dict):
            return None
        episode_number = clean_number(entry.get("number"))
        if episode_number is None:
            return None
        episodes.append(
            ExternalEpisode(
                number=episode_number,
                title=clean_title(entry.get("title")),
                release_date=clean_date(entry.get("release_date")),
                runtime_minutes=clean_number(entry.get("runtime_minutes")),
                external_id=clean_external_id(entry.get("external_id")),
            )
        )
    if len({episode.number for episode in episodes}) != len(episodes):
        return None
    if not all(episode.runtime_minutes for episode in episodes):
        # An entry from before the runtime fallback (#411) counts as a miss, so it is loaded again
        return None

    return ExternalSeason(
        season_number=number,
        title=clean_title(raw.get("title")),
        air_date=clean_date(raw.get("air_date")),
        episodes=episodes,
    )


# - description and genres (US-09)
_NO_DETAILS = ExternalDetails(description=None, genres=())


@dataclass(frozen=True)
class _OutsideDetails:
    """What the outside service knows about one game or movie."""

    found: bool  # False when the service does not know the title
    details: ExternalDetails


def _metadata_cache_key(item: MediaItem) -> str:
    # Key pattern from the Redis key dictionary: omni:catalog:{source}:{external_id}
    source = "igdb" if item.media_type == MediaType.GAME else "tmdb_movie"
    return f"omni:catalog:{source}:{item.external_api_id}"


def _refresh_details(db: Session, item: MediaItem) -> None:
    """Make sure the description and genres of a game or movie are saved. Order: cache, then the
    outside service (IGDB for games, TMDB for movies).

    The same rules as for the seasons of a series: the cache holds outside data only, a cache hit
    means the data is fresh, and the saved copy is only written on a hit when it was never saved.
    A failure is not shown to the user. A game or movie has always been shown without these
    fields, so it is shown with what is saved.
    """
    key = _metadata_cache_key(item)
    outside = _details_from_cache(cache.get_json(key))
    from_cache = outside is not None

    if outside is None:
        try:
            outside = _fetch_details(item)
        except ExternalServiceError as exc:
            logger.warning("Details of title %s failed: %s", item.id, exc)
            return
        _cache_outside(key, _details_to_cache(outside), outside.found)

    if not outside.found:
        return  # the service does not know this id. There is nothing to save.
    if from_cache and item.last_synced is not None:
        return  # the saved copy is already there
    _save_details(db, item.id, outside.details)


def _fetch_details(item: MediaItem) -> _OutsideDetails:
    if item.media_type == MediaType.GAME:
        if not igdb.is_configured():
            raise ExternalServiceError("IGDB is not set up")
        details = igdb.fetch_game_details(item.external_api_id)
    else:
        if not tmdb.is_configured():
            raise ExternalServiceError(_TMDB_NOT_CONFIGURED_MSG)
        details = tmdb.fetch_movie_details(item.external_api_id)
    if details is None:
        return _OutsideDetails(found=False, details=_NO_DETAILS)
    return _OutsideDetails(found=True, details=details)


def _details_to_cache_fields(details: ExternalDetails) -> dict:
    return {"description": details.description, "genres": list(details.genres)}


def _details_from_cache_fields(cached: dict) -> Optional[ExternalDetails]:
    """Read description and genres from a cache entry. Missing or odd fields count as a miss."""
    if "description" not in cached or "genres" not in cached:
        return None
    description, genres = cached["description"], cached["genres"]
    if description is not None and not isinstance(description, str):
        return None
    if not isinstance(genres, list) or not all(isinstance(name, str) for name in genres):
        return None
    # Cleaned again, so an entry that was changed by hand cannot bring in a bad value
    return ExternalDetails(description=clean_text(description), genres=normalize_genres(genres))


def _details_to_cache(outside: _OutsideDetails) -> dict:
    if not outside.found:
        return {"found": False}
    return {"found": True, **_details_to_cache_fields(outside.details)}


def _details_from_cache(cached: object) -> Optional[_OutsideDetails]:
    if not isinstance(cached, dict):
        return None
    if cached.get("found") is False:
        return _OutsideDetails(found=False, details=_NO_DETAILS)
    if cached.get("found") is not True:
        return None
    details = _details_from_cache_fields(cached)
    return None if details is None else _OutsideDetails(found=True, details=details)


def _save_details(db: Session, media_id: int, details: ExternalDetails) -> None:
    for attempt in range(2):
        try:
            _save_details_once(db, media_id, details)
            return
        except IntegrityError:
            # Another request saved the same new genre at the same moment. Run again: the genre
            # exists now, so this time it is found.
            db.rollback()
            if attempt == 1:
                raise


def _save_details_once(db: Session, media_id: int, details: ExternalDetails) -> None:
    """Write the description and genres. An empty value never replaces a saved one: an outside
    service sometimes leaves a field out, and that is no reason to lose what we know."""
    item = db.get(MediaItem, media_id)
    if details.description is not None:
        item.description = details.description
    if details.genres:
        item.genres = _genres_named(db, details.genres)
    # The columns hold UTC time without a time zone, like the other timestamp columns
    item.last_synced = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


def _genres_named(db: Session, names: tuple[str, ...]) -> list[Genre]:
    """The genre rows for these names. A missing genre is created. The names are matched without
    regard to case, so two sources that write "Adventure" and "adventure" share one row."""
    existing = {
        genre.name.lower(): genre
        for genre in db.query(Genre).filter(func.lower(Genre.name).in_([name.lower() for name in names]))
    }
    genres = []
    for name in names:
        genre = existing.get(name.lower())
        if genre is None:
            genre = Genre(name=name)
            db.add(genre)
            existing[name.lower()] = genre
        genres.append(genre)
    return genres


def _save_seasons(db: Session, media_id: int, seasons: list[ExternalSeason]) -> None:
    for attempt in range(2):
        try:
            _save_seasons_once(db, media_id, seasons)
            return
        except IntegrityError:
            # Another request saved the same seasons at the same moment. Run again: the rows
            # exist now, so this time they are found and updated.
            db.rollback()
            if attempt == 1:
                raise


def _save_seasons_once(db: Session, media_id: int, seasons: list[ExternalSeason]) -> None:
    """Add the new seasons and episodes and update the ones that exist.

    Nothing is ever deleted here. The ratings and playtime of a user (Epic 4) will point to these
    rows, and an episode that TMDB no longer lists must not take that data with it.
    """
    existing = {
        season.season_number: season
        for season in db.query(Season)
        .options(selectinload(Season.episodes))
        .filter(Season.media_item_id == media_id)
    }

    for outside in seasons:
        season = existing.get(outside.season_number)
        if season is None:
            season = Season(
                media_item_id=media_id,
                season_number=outside.season_number,
                title=outside.title,
                air_date=outside.air_date,
            )
            db.add(season)
        else:
            season.title = outside.title
            season.air_date = outside.air_date

        episodes = {episode.number: episode for episode in season.episodes}
        for outside_episode in outside.episodes:
            episode = episodes.get(outside_episode.number)
            if episode is None:
                # Adding it to the season sets season_id, also for a season that is new
                season.episodes.append(
                    Chapter(
                        media_item_id=media_id,
                        number=outside_episode.number,
                        kind=ChapterKind.EPISODE,
                        title=outside_episode.title,
                        release_date=outside_episode.release_date,
                        runtime_minutes=outside_episode.runtime_minutes,
                        external_id=outside_episode.external_id,
                    )
                )
            else:
                episode.title = outside_episode.title
                episode.release_date = outside_episode.release_date
                episode.runtime_minutes = outside_episode.runtime_minutes
                episode.external_id = outside_episode.external_id

    item = db.get(MediaItem, media_id)
    # The columns hold UTC time without a time zone, like the other timestamp columns
    item.last_synced = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
