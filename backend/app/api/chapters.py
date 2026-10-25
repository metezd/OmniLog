"""Episodic logging endpoints: rate a chapter or episode (US-10), log playtime (US-11), record a
branching decision (US-12) and read what was recorded for a chapter."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.chapter import (
    ChapterProgressResponse,
    ChapterRatingResponse,
    ChapterRatingUpdate,
    DecisionCreate,
    DecisionItem,
    DecisionResponse,
    PlaytimeCreate,
    PlaytimeLogResponse,
)
from app.services import chapter_service
from app.services.chapter_service import (
    ChapterNotFoundError,
    DecisionNotAllowedError,
    DecisionPointNotFoundError,
    PlaytimeLimitError,
)
from app.services.library_service import LibraryEntryNotFoundError

router = APIRouter(prefix="/library/{entry_id}/chapters", tags=["Episodic Logging"])

# Ids are 32 bit integers in the database. A larger id cannot exist, so it is a 404 and
# the query is never sent (it would fail with a database error).
MAX_ID = 2**31 - 1


def _check_ids(entry_id: int, chapter_id: int) -> None:
    if not (0 < entry_id <= MAX_ID and 0 < chapter_id <= MAX_ID):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")


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
    _check_ids(entry_id, chapter_id)
    try:
        return chapter_service.rate_chapter(db, current_user, entry_id, chapter_id, payload.rating)
    except (LibraryEntryNotFoundError, ChapterNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{chapter_id}/playtime",
    response_model=PlaytimeLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_playtime(
    entry_id: int,
    chapter_id: int,
    payload: PlaytimeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log the minutes spent on a chapter or episode (US-11).

    Every call adds one entry. The total of the chapter is the sum of the entries, so 90 and
    later 30 minutes make 120. The entry is recorded in the diary as PLAYTIME_LOGGED (US-07).
    """
    _check_ids(entry_id, chapter_id)
    try:
        log, progress = chapter_service.log_playtime(
            db, current_user, entry_id, chapter_id, payload.minutes
        )
    except (LibraryEntryNotFoundError, ChapterNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PlaytimeLimitError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return PlaytimeLogResponse(
        id=log.id,
        chapter_id=progress.chapter_id,
        minutes=log.minutes,
        logged_at=log.logged_at,
        playtime_minutes=progress.playtime_minutes,
    )


@router.put("/{chapter_id}/decision", response_model=DecisionResponse)
def record_decision(
    entry_id: int,
    chapter_id: int,
    payload: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record the option chosen at a decision point of a chapter (US-12).

    The choice is the label of one of the options, such as "A". Any other value returns 422 and
    the message lists the allowed labels. A new choice replaces the old one, so only the latest
    is kept. A chapter with several decision points needs `decision_point_id`. The change is
    recorded in the diary as DECISION_RECORDED (US-07).
    """
    _check_ids(entry_id, chapter_id)
    try:
        point, option, decision = chapter_service.record_decision(
            db, current_user, entry_id, chapter_id, payload.choice, payload.decision_point_id
        )
    except (LibraryEntryNotFoundError, ChapterNotFoundError, DecisionPointNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DecisionNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DecisionResponse(
        library_entry_id=decision.library_entry_id,
        chapter_id=chapter_id,
        decision_point_id=point.id,
        choice=option.label,
        decided_at=decision.decided_at,
    )


@router.get("/{chapter_id}", response_model=ChapterProgressResponse)
def get_chapter_progress(
    entry_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """What the user has recorded for a chapter: the rating, the total playtime and the choices.

    A chapter without data returns no rating, 0 minutes and no choice. Reading creates nothing.
    """
    _check_ids(entry_id, chapter_id)
    try:
        view = chapter_service.get_chapter_progress(db, current_user, entry_id, chapter_id)
    except (LibraryEntryNotFoundError, ChapterNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    decisions = [
        DecisionItem(decision_point_id=point_id, choice=label, decided_at=decided_at)
        for point_id, label, decided_at in view.decisions
    ]
    return ChapterProgressResponse(
        library_entry_id=view.library_entry_id,
        chapter_id=view.chapter_id,
        rating=view.progress.rating if view.progress else None,
        playtime_minutes=view.progress.playtime_minutes if view.progress else 0,
        updated_at=view.progress.updated_at if view.progress else None,
        choice=decisions[0].choice if decisions else None,
        decided_at=decisions[0].decided_at if decisions else None,
        decisions=decisions,
    )
