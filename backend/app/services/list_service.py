"""Business logic for custom lists and list items (US-06, Issue #117)."""
from sqlalchemy.orm import Session

from app.models.entities import CustomList, CustomListItem, User
from app.services.diary_service import DiaryAction, record_event


class ListNotFoundError(Exception):
    """The custom list does not exist or belongs to another user."""


class ListItemNotFoundError(Exception):
    """The list item does not exist or belongs to another user's list."""


def _get_own_list(db: Session, user: User, list_id: int) -> CustomList:
    custom_list = (
        db.query(CustomList)
        .filter(CustomList.id == list_id, CustomList.user_id == user.id)
        .first()
    )
    if custom_list is None:
        raise ListNotFoundError("Custom list not found")
    return custom_list


def delete_list(db: Session, user: User, list_id: int) -> None:
    """Delete a custom list and record a LIST_DELETED diary event."""
    custom_list = _get_own_list(db, user, list_id)
    
    db.delete(custom_list)
    record_event(
        db, 
        user.id, 
        DiaryAction.LIST_DELETED, 
        None, 
        f"Deleted list '{custom_list.name}'"
    )
    db.commit()


def remove_list_item(db: Session, user: User, list_id: int, media_item_id: int) -> None:
    """Remove a media item from a custom list and record a LIST_ITEM_REMOVED diary event."""
    # First, ensure the list belongs to the user (prevents accessing other users' lists)
    custom_list = _get_own_list(db, user, list_id)

    item = (
        db.query(CustomListItem)
        .filter(
            CustomListItem.list_id == custom_list.id,
            CustomListItem.media_item_id == media_item_id
        )
        .first()
    )
    if item is None:
        raise ListItemNotFoundError("List item not found")

    db.delete(item)
    record_event(
        db, 
        user.id, 
        DiaryAction.LIST_ITEM_REMOVED, 
        media_item_id, 
        f"Removed from list '{custom_list.name}'"
    )
    db.commit()