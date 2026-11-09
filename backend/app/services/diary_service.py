"""Activity diary (US-07). Events are appended only. They are never edited or deleted. A removal
is a new event, and the older events about the same title stay."""
from sqlalchemy.orm import Session

from app.models.entities import DiaryEntry


class DiaryAction:
    """Event types from the domain model (section 3.5)."""

    LIBRARY_ADDED = "LIBRARY_ADDED"
    STATUS_CHANGED = "STATUS_CHANGED"
    RATED = "RATED"
    CHAPTER_RATED = "CHAPTER_RATED"
    PLAYTIME_LOGGED = "PLAYTIME_LOGGED"
    DECISION_RECORDED = "DECISION_RECORDED"
    LIST_CREATED = "LIST_CREATED"
    LIST_ITEM_ADDED = "LIST_ITEM_ADDED"
    LIBRARY_REMOVED = "LIBRARY_REMOVED"
    LIST_ITEM_REMOVED = "LIST_ITEM_REMOVED"
    LIST_DELETED = "LIST_DELETED"


def record_event(
    db: Session,
    user_id: int,
    action: str,
    media_item_id: int | None = None,
    details: str | None = None,
) -> None:
    """Add a diary event to the session. The caller commits it together with the change,
    so an event is never stored without the change it describes, and the reverse."""
    db.add(
        DiaryEntry(
            user_id=user_id,
            media_item_id=media_item_id,
            action=action,
            details=details[:255] if details else None,
        )
    )
