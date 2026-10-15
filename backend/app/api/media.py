from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import MediaItem, User
from app.schemas.media import MediaItemCreate, MediaItemResponse

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("", response_model=MediaItemResponse, status_code=status.HTTP_201_CREATED)
def create_media(
    payload: MediaItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new media item in the catalog."""
    item = MediaItem(
        title=payload.title,
        media_type=payload.media_type,
        poster_url=payload.poster_url,
        release_date=payload.release_date,
        external_api_id=payload.external_api_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{media_id}", response_model=MediaItemResponse)
def get_media(media_id: int, db: Session = Depends(get_db)):
    """Fetch a single media item by ID."""
    item = db.get(MediaItem, media_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found",
        )
    return item