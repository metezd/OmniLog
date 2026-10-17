"""Business logic for the media catalog entries."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import MediaItem
from app.schemas.media import MediaItemCreate


class DuplicateMediaError(Exception):
    """A title with the same media type and outside id is already in the catalog."""


def create_media_item(db: Session, data: MediaItemCreate) -> MediaItem:
    item = MediaItem(**data.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateMediaError("A title with this media type and external id already exists")
    db.refresh(item)
    return item
