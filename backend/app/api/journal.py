"""Custom list and activity diary endpoints (US-06, US-07, removal)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.journal import (
    CustomListCreate,
    CustomListItemCreate,
    CustomListItemResponse,
    CustomListResponse,
    DiaryEntryResponse,
)
from app.services import journal_service
from app.services.journal_service import (
    DuplicateListNameError,
    ListItemNotFoundError,
    ListNotFoundError,
    MediaNotFoundError,
)

router = APIRouter(tags=["Journal"])


# ---------------------------------------------------------------- US-06: Custom lists
@router.post("/lists", response_model=CustomListResponse, status_code=status.HTTP_201_CREATED)
def create_custom_list(
    payload: CustomListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a list. The name must be unique for the user."""
    try:
        return journal_service.create_list(db, current_user, payload.name)
    except DuplicateListNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/lists", response_model=List[CustomListResponse])
def get_custom_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all lists of the logged-in user."""
    return journal_service.list_lists(db, current_user)


@router.get("/lists/{list_id}", response_model=CustomListResponse)
def get_custom_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one list with its items."""
    try:
        return journal_service.get_list(db, current_user, list_id)
    except ListNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/lists/{list_id}/items", response_model=CustomListItemResponse)
def add_item_to_list(
    list_id: int,
    payload: CustomListItemCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a title to a list. 201 when it is added, 200 when it was already in the list."""
    try:
        item, created = journal_service.add_item(db, current_user, list_id, payload.media_item_id)
    except (ListNotFoundError, MediaNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return item


@router.delete("/lists/{list_id}/items/{media_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_list(
    list_id: int,
    media_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Take a title out of a list. 404 when the list is not the user's or the title is not in it."""
    try:
        journal_service.remove_item(db, current_user, list_id, media_item_id)
    except (ListNotFoundError, ListItemNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a list with its items. The titles themselves are not touched."""
    try:
        journal_service.delete_list(db, current_user, list_id)
    except ListNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------- US-07: Activity diary
@router.get("/diary", response_model=List[DiaryEntryResponse])
def get_activity_diary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the activity events of the logged-in user, newest first."""
    return journal_service.diary_for_user(db, current_user)
