from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import MediaItem, MediaType, User, UserLibrary

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", status_code=status.HTTP_200_OK)
def get_recommendations(
    target: Optional[MediaType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """US-13: Cross-media recommendations excluding owned items."""
    owned_ids_query = db.query(UserLibrary.media_item_id).filter(
        UserLibrary.user_id == current_user.id
    )
    owned_ids = [row[0] for row in owned_ids_query.all()]

    query = db.query(MediaItem)

    if target:
        query = query.filter(MediaItem.media_type == target)

    if owned_ids:
        query = query.filter(MediaItem.id.notin_(owned_ids))

    items = query.all()

    return [
        {
            "id": item.id,
            "title": item.title,
            "media_type": item.media_type.value if hasattr(item.media_type, "value") else str(item.media_type),
            "poster_url": item.poster_url,
            "release_date": item.release_date,
            "description": item.description,
        }
        for item in items
    ]
