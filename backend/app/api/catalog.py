"""Catalog endpoints. US-08 Search the catalog."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import MediaType, User
from app.schemas.media import MediaItemResponse
from app.services import catalog_service
from app.services.catalog_service import CatalogUnavailableError, InvalidQueryError

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
