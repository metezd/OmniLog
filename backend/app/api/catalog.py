"""Catalog endpoints. US-08 Search the catalog, US-09 View title details."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import MediaType, User
from app.schemas.media import MediaDetailResponse, MediaItemResponse
from app.services import catalog_service
from app.services.catalog_service import (
    CatalogUnavailableError,
    InvalidQueryError,
    TitleNotFoundError,
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/search", response_model=List[MediaItemResponse])
def search_catalog(
    q: str = Query(..., min_length=1, max_length=100, description="Title to search for"),
    media_type: MediaType = Query(..., alias="type", description="GAME, SERIES or MOVIE"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search games (IGDB) or series and movies (TMDB) by title.

    Each result is saved in the catalog and has an `id`, so it can be added to the library with
    `POST /library`. A search with no match returns an empty list. When the outside service is
    down, saved titles that match are returned, or 503 when there are none.
    """
    try:
        return catalog_service.search_catalog(db, media_type, q)
    except InvalidQueryError as exc:
        # Same error shape as the other validation errors
        raise RequestValidationError(
            [{"type": "value_error", "loc": ("query", "q"), "msg": str(exc), "input": q}]
        )
    except CatalogUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            headers={"Retry-After": "30"},
        )


# Declared after /search, so the text "search" is never read as an id
@router.get("/{media_id}", response_model=MediaDetailResponse)
def get_title_details(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open a title: its metadata and artwork, and its seasons with episodes or its chapters.

    A series gets its seasons and episodes from TMDB the first time it is opened. They are saved
    and cached, so later requests do not call TMDB again. The chapters of a game have no outside
    source, so they come from the database only. A movie has neither. When TMDB is down, the saved
    copy is returned, or 503 when the series was never loaded.
    """
    try:
        return catalog_service.get_title_details(db, media_id)
    except TitleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CatalogUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            headers={"Retry-After": "30"},
        )
