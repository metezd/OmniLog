"""Episodic logging endpoints: rate a chapter or episode (US-10)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.chapter import ChapterRatingResponse, ChapterRatingUpdate
from app.services import chapter_service
from app.services.chapter_service import ChapterNotFoundError
from app.services.library_service import LibraryEntryNotFoundError

router = APIRouter(prefix="/library/{entry_id}/chapters", tags=["Episodic Logging"])

# Ids are 32 bit integers in the database. A larger id cannot exist, so it is a 404 and
# the query is never sent (it would fail with a database error).
MAX_ID = 2**31 - 1


@router.put("/{chapter_id}/rating", response_model=ChapterRatingResponse)
def rate_chapter(
    entry_id: int,
    chapter_id: int,
    payload: ChapterRatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Give a chapter or episode of a title in the library a rating from 1 to 5 (US-10).

    The call can be repeated. A new rating replaces the old one. The change is recorded in the
    diary as CHAPTER_RATED (US-07).
    """
    if not (0 < entry_id <= MAX_ID and 0 < chapter_id <= MAX_ID):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    try:
        return chapter_service.rate_chapter(db, current_user, entry_id, chapter_id, payload.rating)
    except (LibraryEntryNotFoundError, ChapterNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
