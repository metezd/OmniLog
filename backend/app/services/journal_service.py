"""Business logic for custom lists (US-06, removal) and the activity diary (US-07)."""
from typing import List, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.entities import CustomList, CustomListItem, DiaryEntry, MediaItem, User
from app.services.diary_service import DiaryAction, record_event


class ListNotFoundError(Exception):
    """The list does not exist or belongs to another user."""


class MediaNotFoundError(Exception):
    """The media item does not exist."""


class ListItemNotFoundError(Exception):
    """The title is not in the list."""


class DuplicateListNameError(Exception):
    """The user already has a list with this name."""


def create_list(db: Session, user: User, name: str) -> CustomList:
    existing = (
        db.query(CustomList)
        .filter(CustomList.user_id == user.id, CustomList.name == name)
        .first()
    )
    if existing:
        raise DuplicateListNameError("A list with this name already exists")

    custom_list = CustomList(user_id=user.id, name=name)
    db.add(custom_list)
    try:
        db.flush()  # the unique constraint (user, name) catches a race between two requests
    except IntegrityError:
        db.rollback()
        raise DuplicateListNameError("A list with this name already exists")

    record_event(db, user.id, DiaryAction.LIST_CREATED, None, f"Created list {name}")
    db.commit()
    db.refresh(custom_list)
    return custom_list


def _get_own_list(db: Session, user: User, list_id: int) -> CustomList:
    custom_list = (
        db.query(CustomList)
        .options(selectinload(CustomList.items))
        .filter(CustomList.id == list_id, CustomList.user_id == user.id)
        .first()
    )
    if custom_list is None:
        raise ListNotFoundError("List not found")
    return custom_list


def list_lists(db: Session, user: User) -> List[CustomList]:
    return (
        db.query(CustomList)
        .options(selectinload(CustomList.items))
        .filter(CustomList.user_id == user.id)
        .order_by(CustomList.id)
        .all()
    )


def get_list(db: Session, user: User, list_id: int) -> CustomList:
    return _get_own_list(db, user, list_id)


def add_item(
    db: Session, user: User, list_id: int, media_item_id: int
) -> Tuple[CustomListItem, bool]:
    """Add a title to a list. Returns the item and True if it was added now.

    A title that is already in the list is not added a second time. The existing item is returned
    and no diary event is written.
    """
    custom_list = _get_own_list(db, user, list_id)

    media = db.get(MediaItem, media_item_id)
    if media is None:
        raise MediaNotFoundError("Media item not found")

    existing = (
        db.query(CustomListItem)
        .filter(CustomListItem.list_id == custom_list.id, CustomListItem.media_item_id == media_item_id)
        .first()
    )
    if existing:
        return existing, False

    item = CustomListItem(list_id=custom_list.id, media_item_id=media_item_id)
    db.add(item)
    try:
        db.flush()
    except IntegrityError:
        # A concurrent request added the same title first. Return that item.
        db.rollback()
        existing = (
            db.query(CustomListItem)
            .filter(CustomListItem.list_id == list_id, CustomListItem.media_item_id == media_item_id)
            .first()
        )
        return existing, False

    record_event(
        db, user.id, DiaryAction.LIST_ITEM_ADDED, media_item_id,
        f"Added to list {custom_list.name}",
    )
    db.commit()
    db.refresh(item)
    return item, True


def remove_item(db: Session, user: User, list_id: int, media_item_id: int) -> None:
    """Take a title out of a list. The title stays in the catalog and in the library."""
    custom_list = _get_own_list(db, user, list_id)
    item = next((i for i in custom_list.items if i.media_item_id == media_item_id), None)
    if item is None:
        raise ListItemNotFoundError("Title is not in the list")

    db.delete(item)
    record_event(
        db, user.id, DiaryAction.LIST_ITEM_REMOVED, media_item_id,
        f"Removed from list {custom_list.name}",
    )
    db.commit()


def delete_list(db: Session, user: User, list_id: int) -> None:
    """Delete a list with its items. The titles stay in the catalog and in the library, and the
    name can be used again."""
    custom_list = _get_own_list(db, user, list_id)
    name = custom_list.name

    db.delete(custom_list)
    record_event(db, user.id, DiaryAction.LIST_DELETED, None, f"Deleted list {name}")
    db.commit()


def diary_for_user(db: Session, user: User) -> List[DiaryEntry]:
    """Newest events first. Only the user's own events."""
    return (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user.id)
        .order_by(DiaryEntry.created_at.desc(), DiaryEntry.id.desc())
        .all()
    )
