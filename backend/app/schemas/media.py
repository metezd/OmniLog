from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import MediaType


class MediaItemBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    media_type: MediaType
    poster_url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    release_date: Optional[str] = Field(default=None, min_length=1, max_length=50)
    external_api_id: Optional[int] = None


class MediaItemCreate(MediaItemBase):
    pass


class MediaItemUpdate(BaseModel):
    """Partial Update. All areas are optional"""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    media_type: Optional[MediaType] = None
    poster_url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    release_date: Optional[str] = Field(default=None, min_length=1, max_length=50)
    external_api_id: Optional[int] = None


class MediaItemResponse(MediaItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int