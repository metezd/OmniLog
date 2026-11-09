"""Business logic for a user's library (US-04, US-05, removal)."""
from typing import List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.entities import MediaItem, User, UserLibrary
from app.schemas.library import UserLibraryCreate, UserLibraryUpdate
from app.services.diary_service import DiaryAction, record_event


class MediaNotFoundError(Exception):
    """The media item does not exist."""


class LibraryConflictError(Exception):
    """The user already has this media item in the library."""


class LibraryEntryNotFoundError(Exception):
    """The entry does not exist or belongs to another user.

    Both cases raise the same error, so one user cannot tell whether another user's entry exists.
    """


def add_entry(db: Session, user: User, data: UserLibraryCreate) -> UserLibrary:
    if db.get(MediaItem, data.media_item_id) is None:
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
    db.refresh(entry)
    return entry


def list_entries(db: Session, user: User) -> List[UserLibrary]:
    # Load the media item in the same query. Without this, the response runs one query per entry.
    return (
        db.query(UserLibrary)
        .options(joinedload(UserLibrary.media_item))
        .filter(UserLibrary.user_id == user.id)
        .order_by(UserLibrary.id)
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
    db.refresh(entry)
    return entry


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
