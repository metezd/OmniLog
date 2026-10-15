from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User, MediaItem, UserLibrary, DiaryEntry, WatchStatus
from app.schemas.library import (
    UserLibraryCreate,
    UserLibraryUpdate,
    UserLibraryResponse,
)

router = APIRouter(prefix="/library", tags=["Library"])


@router.post("", response_model=UserLibraryResponse, status_code=status.HTTP_201_CREATED)
def add_to_library(
    payload: UserLibraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a title to the user's library and record a diary event (US-04 & US-07)."""
    media = db.get(MediaItem, payload.media_item_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found",
        )

    # Aynı başlık zaten kütüphanede varsa 409 dön
    existing = (
        db.query(UserLibrary)
        .filter(
            UserLibrary.user_id == current_user.id,
            UserLibrary.media_item_id == payload.media_item_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Media item already in library",
        )

    new_entry = UserLibrary(
        user_id=current_user.id,
        media_item_id=payload.media_item_id,
        status=payload.status,
    )
    db.add(new_entry)

    # US-07: Kütüphaneye ekleme günlüğü (Diary Event) oluştur
    diary_event = DiaryEntry(
        user_id=current_user.id,
        media_item_id=payload.media_item_id,
        action="ADDED",
        details=f"Added to library with status {payload.status.value}",
    )
    db.add(diary_event)

    db.commit()
    db.refresh(new_entry)
    return new_entry


@router.get("", response_model=List[UserLibraryResponse])
def get_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all library entries for the logged-in user."""
    return (
        db.query(UserLibrary)
        .filter(UserLibrary.user_id == current_user.id)
        .all()
    )
"""Library endpoints: add a title, list my library, rate and update an entry (US-04, US-05)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.library import UserLibraryCreate, UserLibraryResponse, UserLibraryUpdate
from app.services import library_service
from app.services.library_service import (
    LibraryConflictError,
    LibraryEntryNotFoundError,
    MediaNotFoundError,
)

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=List[UserLibraryResponse])
def list_library(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return library_service.list_entries(db, user)


@router.post("", response_model=UserLibraryResponse, status_code=status.HTTP_201_CREATED)
def add_to_library(
    data: UserLibraryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return library_service.add_entry(db, user, data)
    except MediaNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LibraryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch("/{entry_id}", response_model=UserLibraryResponse)
def update_library_entry(
    entry_id: int,
    payload: UserLibraryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rate or update status of an entry and record a diary event (US-05 & US-07)."""
    entry = db.get(UserLibrary, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library entry not found",
        )

    # Başka kullanıcının kaydını değiştirmeye çalışıyorsa 403 / 404
    if entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this entry",
        )

    # Rating aralık kontrolü (1-10) -> US-05
    if payload.rating is not None:
        if payload.rating < 1 or payload.rating > 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rating must be between 1 and 10",
            )
        entry.rating = payload.rating

    if payload.status is not None:
        entry.status = payload.status

    # US-07: Puanlama veya durum güncellemesi günlüğü (Diary Event)
    action = "RATED" if payload.rating is not None else "UPDATED"
    details = f"Rated {payload.rating}" if payload.rating is not None else f"Status: {payload.status}"
    diary_event = DiaryEntry(
        user_id=current_user.id,
        media_item_id=entry.media_item_id,
        action=action,
        details=details,
    )
    db.add(diary_event)

    db.commit()
    db.refresh(entry)
    return entry
    data: UserLibraryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return library_service.update_entry(db, user, entry_id, data)
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
