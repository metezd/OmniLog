"""List endpoints: delete lists and remove items from lists (US-06, Issue #117)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.services import list_service
from app.services.list_service import ListNotFoundError, ListItemNotFoundError

router = APIRouter(prefix="/lists", tags=["Lists"])


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a custom list completely. Recorded in the diary as LIST_DELETED."""
    try:
        list_service.delete_list(db, current_user, list_id)
    except ListNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{list_id}/items/{media_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_list(
    list_id: int,
    media_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a media item from a custom list. Recorded in the diary as LIST_ITEM_REMOVED."""
    try:
        list_service.remove_list_item(db, current_user, list_id, media_item_id)
    except (ListNotFoundError, ListItemNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))