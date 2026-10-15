from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.entities import WatchStatus
from app.schemas.media import MediaItemResponse


class UserLibraryCreate(BaseModel):
    """user_id is NOT Present here: it will be retrieved from the token(current_user) in future, not from the client."""
    media_item_id: int
    status: WatchStatus = WatchStatus.PLAN_TO_WATCH
    rating: Optional[float] = Field(default=None, ge=1, le=10)


class UserLibraryUpdate(BaseModel):
    """Partial update. Omitted fields are unchanged. An explicit null rating clears the rating."""
    status: Optional[WatchStatus] = None
    rating: Optional[float] = Field(default=None, ge=1, le=10)

    @field_validator("status")
    @classmethod
    def status_cannot_be_null(cls, value):
        # Only runs when "status" is sent explicitly, because the default is not validated
        if value is None:
            raise ValueError("status cannot be null")
        return value


class UserLibraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    media_item_id: int
    status: WatchStatus
    rating: Optional[float] = None
    updated_at: Optional[datetime] = None
    media_item: MediaItemResponse