"""Business logic for the media catalog entries."""
from sqlalchemy.orm import Session

from app.models.entities import MediaItem
from app.schemas.media import MediaItemCreate


def create_media_item(db: Session, data: MediaItemCreate) -> MediaItem:
    item = MediaItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
