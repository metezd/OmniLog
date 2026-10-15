from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import CustomList, CustomListItem, DiaryEntry, MediaItem, User
from app.schemas.journal import (
    CustomListCreate,
    CustomListItemCreate,
    CustomListItemResponse,
    CustomListResponse,
    DiaryEntryResponse,
)

router = APIRouter(tags=["Journal"])


# ---------------------------------------------------------------- US-06: Custom Lists
@router.post(
    "/lists",
    response_model=CustomListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_list(
    payload: CustomListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new custom list for the logged-in user."""
    custom_list = CustomList(name=payload.name, user_id=current_user.id)
    db.add(custom_list)
    db.commit()
    db.refresh(custom_list)
    return custom_list


@router.post(
    "/lists/{list_id}/items",
    response_model=CustomListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_item_to_list(
    list_id: int,
    payload: CustomListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a media title to a user's custom list."""
    custom_list = (
        db.query(CustomList)
        .filter(CustomList.id == list_id, CustomList.user_id == current_user.id)
        .first()
    )
    if not custom_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    media = db.get(MediaItem, payload.media_item_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found",
        )

    # Varsa mükerrer kaydı engelle ya da mevcut olanı dön
    existing_item = (
        db.query(CustomListItem)
        .filter(
            CustomListItem.list_id == list_id,
            CustomListItem.media_item_id == payload.media_item_id,
        )
        .first()
    )
    if existing_item:
        return existing_item

    item = CustomListItem(list_id=list_id, media_item_id=payload.media_item_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get(
    "/lists/{list_id}",
    response_model=CustomListResponse,
    status_code=status.HTTP_200_OK,
)
def get_custom_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list details along with its items."""
    custom_list = (
        db.query(CustomList)
        .filter(CustomList.id == list_id, CustomList.user_id == current_user.id)
        .first()
    )
    if not custom_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )
    return custom_list


# ---------------------------------------------------------------- US-07: Activity Diary
@router.get(
    "/diary",
    response_model=List[DiaryEntryResponse],
    status_code=status.HTTP_200_OK,
)
def get_activity_diary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chronological activity diary events (newest first)."""
    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == current_user.id)
        .order_by(DiaryEntry.created_at.desc(), DiaryEntry.id.desc())
        .all()
    )
    return entries