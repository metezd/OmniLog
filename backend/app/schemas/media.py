from typing import List, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import ExternalId, NoNulStr
from app.models.entities import ChapterKind, MediaType


class MediaItemBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: NoNulStr = Field(min_length=1, max_length=200)
    media_type: MediaType
    poster_url: Optional[NoNulStr] = Field(default=None, min_length=1, max_length=500)
    release_date: Optional[NoNulStr] = Field(default=None, min_length=1, max_length=50)
    external_api_id: Optional[ExternalId] = None


# The image hosts of TMDB and IGDB. A title that a user adds may only point to these (#218).
POSTER_HOSTS = frozenset({"image.tmdb.org", "images.igdb.com"})


def poster_from_known_host(value: Optional[str]) -> Optional[str]:
    """Accept only an https address on the TMDB or IGDB image host (#218, #303).

    Every user loads the poster of a title, so an outside address would tell its owner who
    looked at the title, and a `javascript:` address has no place in an image. The address is
    taken apart with urllib, not matched with a regular expression, so a host that only starts
    like an allowed one, user info, or a port is refused.
    """
    if value is None:
        return value
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname not in POSTER_HOSTS
        or parts.port is not None
        or parts.username is not None
        or parts.password is not None
    ):
        raise ValueError("poster_url must be an https address on image.tmdb.org or images.igdb.com")
    return value


class MediaItemCreate(MediaItemBase):
    poster_host_check = field_validator("poster_url")(poster_from_known_host)


class MediaItemUpdate(BaseModel):
    """Partial Update. All areas are optional"""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[NoNulStr] = Field(default=None, min_length=1, max_length=200)
    media_type: Optional[MediaType] = None
    poster_url: Optional[NoNulStr] = Field(default=None, min_length=1, max_length=500)
    release_date: Optional[NoNulStr] = Field(default=None, min_length=1, max_length=50)
    external_api_id: Optional[ExternalId] = None

    poster_host_check = field_validator("poster_url")(poster_from_known_host)


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
