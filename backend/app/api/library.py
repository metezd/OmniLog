"""Library endpoints: add a title, list my library, rate, update and remove an entry (US-04, US-05)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session


from app.api.deps import get_current_user, limit_per_user
from app.api.pagination import Page, library_page
from app.core.database import get_db
from app.models.entities import User
from app.schemas.chapter import PlaytimeCreate
from app.schemas.library import (
    TitlePlaytimeLogResponse,
    UserLibraryCreate,
    UserLibraryResponse,
    UserLibraryUpdate,
)
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services import library_service, review_service
from app.services.library_service import (
    LibraryConflictError,
    LibraryEntryNotFoundError,
    MediaNotFoundError,
    TitlePlaytimeLimitError,
    TitlePlaytimeNotAllowedError,
)

router = APIRouter(prefix="/library", tags=["Library"])

# Ids are 32 bit integers in the database. A larger id cannot exist, so it is a 404 and the
# query is never sent (it would fail with a database error).
MAX_ID = 2**31 - 1


@router.post("", response_model=UserLibraryResponse, status_code=status.HTTP_201_CREATED)
def add_to_library(
    payload: UserLibraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a title to the user's library and record a diary event (US-04, US-07)."""
    try:
        return library_service.add_entry(db, current_user, payload)
    except MediaNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LibraryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=List[UserLibraryResponse])
def get_library(
    page: Page = Depends(library_page),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the library entries of the logged-in user only, oldest first.

    `limit` (1 to 500, default 200) and `offset` (default 0) page the answer. The answer stays a
    plain list. A limit above 500 gives 422.
    """
    return library_service.list_entries(db, current_user, limit=page.limit, offset=page.offset)


@router.patch("/{entry_id}", response_model=UserLibraryResponse)
def update_library_entry(
    entry_id: int,
    payload: UserLibraryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rate or change the status of an entry (US-05). Changes are recorded in the diary (US-07)."""
    try:
        return library_service.update_entry(db, current_user, entry_id, payload)
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_library_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a title from the library. The chapter ratings, playtime and decisions of the user for
    this title are deleted with it, so a client should ask for confirmation first. The removal is
    recorded in the diary."""
    try:
        library_service.remove_entry(db, current_user, entry_id)
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{entry_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_per_user("review"))],
)
def submit_review(
    entry_id: int,
    payload: ReviewCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit or replace the user's review for a library entry with spoiler detection (US-14)."""
    try:
        review, is_new = review_service.upsert_review(db, current_user, entry_id, payload)
        response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
        return review
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{entry_id}/review", response_model=ReviewResponse | None)
def get_review(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the user's review for a library entry, or null when no review has been posted yet."""
    try:
        review = review_service.get_review(db, current_user, entry_id)
        if review is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return review
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{entry_id}/playtime",
    response_model=TitlePlaytimeLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_title_playtime(
    entry_id: int,
    payload: PlaytimeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log the minutes spent on a whole game or movie, without a chapter (US-11, #413).

    Every call adds one entry, and the total of the title is the sum of the entries. A series
    answers 422, because its time is logged on the episodes. The entry is recorded in the diary
    as PLAYTIME_LOGGED (US-07) and counts in the statistics (US-15).
    """
    if not 0 < entry_id <= MAX_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    try:
        log, entry = library_service.log_title_playtime(db, current_user, entry_id, payload.minutes)
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (TitlePlaytimeNotAllowedError, TitlePlaytimeLimitError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    return TitlePlaytimeLogResponse(
        id=log.id,
        library_entry_id=entry.id,
        minutes=log.minutes,
        logged_at=log.logged_at,
        playtime_minutes=entry.playtime_minutes,
    )
