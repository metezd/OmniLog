"""Recommendations API endpoint (US-13)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import MediaType, User
from app.schemas.media import MediaItemResponse
from app.services.recommendations_service import (
    get_recommendations as fetch_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=list[MediaItemResponse], status_code=status.HTTP_200_OK)
def get_recommendations(
    target: Annotated[MediaType, Query(...)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recommend unowned titles of the requested media type."""
    return fetch_recommendations(
        db=db,
        user_id=current_user.id,
        target=target,
        limit=limit,
    )
