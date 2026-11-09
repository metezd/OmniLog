"""Statistics endpoint: the numbers behind the dashboard (US-15)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.schemas.stats import StatsResponse
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Media split, rating distribution, genre breakdown and playtime of the user's library."""
    return stats_service.get_stats(db, current_user)
