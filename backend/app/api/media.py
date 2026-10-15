"""Media catalog endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.media import MediaItemCreate, MediaItemResponse
from app.services import media_service

router = APIRouter(prefix="/media", tags=["media"])


@router.post("", response_model=MediaItemResponse, status_code=status.HTTP_201_CREATED)
def create_media(
    data: MediaItemCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # Any logged in user can add a title for now. Restricting this is an open decision.
    return media_service.create_media_item(db, data)
