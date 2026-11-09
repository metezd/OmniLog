from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    # Sorted by name. Empty until the details of the title were loaded (US-09).
    genres: List[str] = []

    @field_validator("genres", mode="before")
    @classmethod
    def genre_names(cls, value):
        """The model holds Genre rows. The answer holds their names."""
        return [getattr(genre, "name", genre) for genre in value] if value is not None else []


# --- US-09: Title details
class DecisionOptionResponse(BaseModel):
    """One answer that a player can choose at a decision point (US-12)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str  # Short label such as A or B. `PUT .../decision` takes this value as `choice`.
    text: Optional[str] = None


class DecisionPointResponse(BaseModel):
    """A question of a chapter with its options, in the order that the player sees them."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    prompt: str
    options: List[DecisionOptionResponse] = []


class ChapterResponse(BaseModel):
    """An episode of a season, or a chapter of a game."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    kind: ChapterKind
    title: Optional[str] = None
    release_date: Optional[str] = None
    runtime_minutes: Optional[int] = None
    # Empty for a chapter without a decision. The options are sorted by label.
    decision_points: List[DecisionPointResponse] = []


class SeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_number: int  # 0 is used for specials
    title: Optional[str] = None
    air_date: Optional[str] = None
    episodes: List[ChapterResponse] = []


class MediaDetailResponse(MediaItemResponse):
    """A title with its parts: `seasons` (with episodes) for a series, `chapters` for a game.

    A list is empty when the title has no parts of that kind, for example both for a movie. The
    description is only here, not in lists of titles, because a synopsis can be long.
    """

    description: Optional[str] = None
    seasons: List[SeasonResponse] = []
    chapters: List[ChapterResponse] = []
