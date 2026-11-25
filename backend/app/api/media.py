"""Media catalog endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import config
from app.core.database import get_db
from app.models.entities import MediaItem, User
from app.schemas.media import MediaItemCreate, MediaItemResponse
from app.services import media_service
from app.services.media_service import DuplicateMediaError

router = APIRouter(prefix="/media", tags=["Media"])


def media_create_enabled() -> None:
    """Answer 404 unless ALLOW_MEDIA_CREATE is on (#218).

    Titles come from the catalog search, so nobody needs to write to the shared catalog. The
    check runs before the login check, so the route looks like it does not exist.
    """
    if not config.ALLOW_MEDIA_CREATE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


@router.post(
    "",
    response_model=MediaItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(media_create_enabled)],
)
def create_media(
    payload: MediaItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new media item in the catalog. Off by default, see ALLOW_MEDIA_CREATE."""
    try:
        return media_service.create_media_item(db, payload)
    except DuplicateMediaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/{media_id}", response_model=MediaItemResponse)
def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single media item by ID. Needs a login, like every other catalog endpoint."""
    item = db.get(MediaItem, media_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found",
        )
    return item
