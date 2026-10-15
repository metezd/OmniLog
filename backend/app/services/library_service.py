"""Business logic for a user's library (US-04, US-05)."""
from typing import List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import MediaItem, User, UserLibrary
from app.schemas.library import UserLibraryCreate, UserLibraryUpdate


class MediaNotFoundError(Exception):
    """The media item does not exist."""


class LibraryConflictError(Exception):
    """The user already has this media item in the library."""


class LibraryEntryNotFoundError(Exception):
    """The entry does not exist or belongs to another user.

    Both cases raise the same error so one user cannot discover another user's entries.
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
        db.commit()
    except IntegrityError:
        # The unique constraint (user, media item) caught a duplicate
        db.rollback()
        raise LibraryConflictError("This title is already in your library")
    db.refresh(entry)
    return entry


def list_entries(db: Session, user: User) -> List[UserLibrary]:
    return (
        db.query(UserLibrary)
        .filter(UserLibrary.user_id == user.id)
        .order_by(UserLibrary.id)
        .all()
    )


def update_entry(db: Session, user: User, entry_id: int, data: UserLibraryUpdate) -> UserLibrary:
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == user.id)
        .first()
    )
    if entry is None:
        raise LibraryEntryNotFoundError("Library entry not found")

    # Only apply the fields the client actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry
