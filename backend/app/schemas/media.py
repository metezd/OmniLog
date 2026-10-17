from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import ChapterKind, MediaType


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


# --- US-09: Title details
class ChapterResponse(BaseModel):
    """An episode of a season, or a chapter of a game."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    kind: ChapterKind
    title: Optional[str] = None
    release_date: Optional[str] = None
    runtime_minutes: Optional[int] = None


class SeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_number: int  # 0 is used for specials
    title: Optional[str] = None
    air_date: Optional[str] = None
    episodes: List[ChapterResponse] = []


class MediaDetailResponse(MediaItemResponse):
    """A title with its parts: `seasons` (with episodes) for a series, `chapters` for a game.

    A list is empty when the title has no parts of that kind, for example both for a movie.
    """

    seasons: List[SeasonResponse] = []
    chapters: List[ChapterResponse] = []
