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
    """US-13: Cross-media recommendations excluding owned items, ranked by genre and content similarity."""
    user_entries = (
        db.query(UserLibrary)
        .filter(UserLibrary.user_id == current_user.id)
        .all()
    )
    owned_ids = [entry.media_item_id for entry in user_entries]

    # Build genre preference weights from the user's library (weighted by rating when present)
    genre_weights: dict[str, float] = {}
    for entry in user_entries:
        if entry.media_item and entry.media_item.genres:
            weight = float(entry.rating) if entry.rating is not None else 5.0
            for genre in entry.media_item.genres:
                genre_weights[genre.name] = genre_weights.get(genre.name, 0.0) + weight

    query = db.query(MediaItem)

    if target:
        query = query.filter(MediaItem.media_type == target)

    if owned_ids:
        query = query.filter(MediaItem.id.notin_(owned_ids))

    items = query.all()

    def similarity_score(item: MediaItem) -> tuple[float, int]:
        item_genres = [g.name for g in (item.genres or [])]
        score = sum(genre_weights.get(g, 0.0) for g in item_genres)
        return (score, -item.id)

    ranked_items = sorted(items, key=similarity_score, reverse=True)

    return [
        {
            "id": item.id,
            "title": item.title,
            "media_type": item.media_type.value if hasattr(item.media_type, "value") else str(item.media_type),
            "poster_url": item.poster_url,
            "release_date": item.release_date,
            "description": item.description,
            "external_api_id": item.external_api_id,
            "genres": [g.name for g in (item.genres or [])],
        }
        for item in ranked_items
    ]
