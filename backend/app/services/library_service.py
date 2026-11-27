"""Business logic for a user's library (US-04, US-05, removal)."""
from typing import List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.entities import MediaItem, MediaType, PlaytimeLog, User, UserLibrary
from app.schemas.library import UserLibraryCreate, UserLibraryUpdate
from app.services import catalog_service
from app.services.diary_service import DiaryAction, record_event
from app.services.stats_service import invalidate_stats_cache


class MediaNotFoundError(Exception):
    """The media item does not exist."""


class LibraryConflictError(Exception):
    """The user already has this media item in the library."""


# A series is logged on its episodes. Games and movies can also be logged as a whole (#413).
TITLE_PLAYTIME_MEDIA_TYPES = frozenset({MediaType.GAME, MediaType.MOVIE})
# The total playtime of one title, like the limit of one chapter. Far below the INTEGER limit.
MAX_TOTAL_TITLE_PLAYTIME_MINUTES = 10_000_000


class TitlePlaytimeNotAllowedError(Exception):
    """The title is a series, so its time is logged on the episodes."""


class TitlePlaytimeLimitError(Exception):
    """The new entry would make the total playtime of the title too large."""


class LibraryEntryNotFoundError(Exception):
    """The entry does not exist or belongs to another user.

    Both cases raise the same error, so one user cannot tell whether another user's entry exists.
    """


def add_entry(db: Session, user: User, data: UserLibraryCreate) -> UserLibrary:
    item = db.get(MediaItem, data.media_item_id)
    if item is None:
        raise MediaNotFoundError("Media item not found")

    entry = UserLibrary(
        user_id=user.id,
        media_item_id=data.media_item_id,
        status=data.status,
        rating=data.rating,
    )
    db.add(entry)
    try:
        db.flush()  # sends the INSERT now, so a duplicate is caught before the events are written
    except IntegrityError:
        db.rollback()
        raise LibraryConflictError("Media item already in library")

    record_event(
        db, user.id, DiaryAction.LIBRARY_ADDED, data.media_item_id,
        f"Added with status {data.status.value}",
    )
    if data.rating is not None:
        record_event(
            db, user.id, DiaryAction.RATED, data.media_item_id,
            f"Rated {data.rating:g}",
        )

    db.commit()
    catalog_service.ensure_title_details(db, item)
    invalidate_stats_cache(user.id)
    return _load_with_media(db, entry.id)


def _load_with_media(db: Session, entry_id: int) -> UserLibrary:
    """One entry with its media item and genres, read fresh after a commit.

    The answer holds the media item, so it is loaded in the same query instead of one lazy load
    for the item and one for its genres after the response starts to be built.
    """
    return (
        db.query(UserLibrary)
        .options(joinedload(UserLibrary.media_item).selectinload(MediaItem.genres))
        .filter(UserLibrary.id == entry_id)
        .populate_existing()
        .one()
    )


def list_entries(
    db: Session, user: User, limit: int | None = None, offset: int = 0
) -> List[UserLibrary]:
    """The user's entries, oldest first. `limit=None` returns all of them."""
    # Load the media item in the same query. Without this, the response runs one query per entry.
    return (
        db.query(UserLibrary)
        .options(joinedload(UserLibrary.media_item).selectinload(MediaItem.genres))
        .filter(UserLibrary.user_id == user.id)
        .order_by(UserLibrary.id)
        .limit(limit)
        .offset(offset)
        .all()
    )


def _get_own_entry(db: Session, user: User, entry_id: int) -> UserLibrary:
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == user.id)
        .first()
    )
    if entry is None:
        raise LibraryEntryNotFoundError("Library entry not found")
    return entry


def update_entry(db: Session, user: User, entry_id: int, data: UserLibraryUpdate) -> UserLibrary:
    entry = _get_own_entry(db, user, entry_id)

    # Only fields the client sent are considered. Events are written only for real changes.
    changes = data.model_dump(exclude_unset=True)

    if "status" in changes and changes["status"] != entry.status:
        entry.status = changes["status"]
        record_event(
            db, user.id, DiaryAction.STATUS_CHANGED, entry.media_item_id,
            f"Status changed to {entry.status.value}",
        )

    if "rating" in changes and changes["rating"] != entry.rating:
        entry.rating = changes["rating"]
        text = "Rating removed" if entry.rating is None else f"Rated {entry.rating:g}"
        record_event(db, user.id, DiaryAction.RATED, entry.media_item_id, text)

    db.commit()
    invalidate_stats_cache(user.id)
    return _load_with_media(db, entry.id)


def remove_entry(db: Session, user: User, entry_id: int) -> None:
    """Remove a title from the library of the user.

    The ratings, playtime and decisions that the user logged for the chapters of this title go
    with it: the database deletes them together with the entry (ON DELETE CASCADE). The title
    itself stays in the catalog, and so do the older diary events about it. The removal is a new
    diary event, written in the same transaction as the delete.
    """
    entry = _get_own_entry(db, user, entry_id)
    media_item_id = entry.media_item_id

    db.delete(entry)
    record_event(db, user.id, DiaryAction.LIBRARY_REMOVED, media_item_id, "Removed from library")
    db.commit()
    invalidate_stats_cache(user.id)


def log_title_playtime(
    db: Session, user: User, entry_id: int, minutes: int
) -> tuple[PlaytimeLog, UserLibrary]:
    """Add one playtime entry to a whole game or movie, without a chapter (#413).

    The entry, the new total of the library entry and the PLAYTIME_LOGGED event are saved in one
    transaction. The total is raised by the database itself (SET total = total + minutes), so two
    entries sent at the same moment are both counted.
    """
    entry = _get_own_entry(db, user, entry_id)

    # Plain values are kept here, because a rollback expires the loaded objects
    user_id = user.id
    entry_pk = entry.id
    media_item_id = entry.media_item_id

    media_type = db.query(MediaItem.media_type).filter(MediaItem.id == media_item_id).scalar()
    if media_type not in TITLE_PLAYTIME_MEDIA_TYPES:
        raise TitlePlaytimeNotAllowedError("The time of a series is logged on its episodes")
    if entry.playtime_minutes + minutes > MAX_TOTAL_TITLE_PLAYTIME_MINUTES:
        raise TitlePlaytimeLimitError("The total playtime of a title is too large")

    log = PlaytimeLog(library_entry_id=entry_pk, minutes=minutes)
    db.add(log)
    db.query(UserLibrary).filter(UserLibrary.id == entry_pk).update(
        {UserLibrary.playtime_minutes: UserLibrary.playtime_minutes + minutes},
        synchronize_session=False,
    )
    record_event(db, user_id, DiaryAction.PLAYTIME_LOGGED, media_item_id, f"Logged {minutes} min")
    db.commit()
    db.refresh(log)
    invalidate_stats_cache(user_id)
    return log, _load_with_media(db, entry_pk)
