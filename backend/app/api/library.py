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
    data: UserLibraryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return library_service.update_entry(db, user, entry_id, data)
    except LibraryEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
