"""Schemas for the personal record of a chapter or episode (US-10, US-11 and US-12)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChapterRatingUpdate(BaseModel):
    """The rating of one chapter or episode.

    strict=True: JSON whole numbers only. Without it, 4.0 and "4" would be accepted (BR-10).
    """

    rating: int = Field(strict=True, ge=1, le=5)


class ChapterRatingResponse(BaseModel):
    """A saved chapter rating. Every field is always present after a successful PUT."""

    model_config = ConfigDict(from_attributes=True)

    library_entry_id: int
    chapter_id: int
    rating: int = Field(ge=1, le=5)
    updated_at: datetime


# One playtime entry is at most 100,000 minutes (about 69 days). The total of a chapter is
# limited in the service, so the INTEGER column can never overflow.
MAX_PLAYTIME_MINUTES = 100_000


class PlaytimeCreate(BaseModel):
    """One playtime entry. At least 1 minute (BR-12). Whole JSON numbers only."""

    minutes: int = Field(strict=True, ge=1, le=MAX_PLAYTIME_MINUTES)


class PlaytimeLogResponse(BaseModel):
    """The saved entry and the new total of the chapter."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    minutes: int
    logged_at: datetime
    playtime_minutes: int  # total of all entries of this chapter


class DecisionCreate(BaseModel):
    """The choice at a decision point, given as the label of an option such as "A".

    The label is at most 10 characters, like the label column. The decision point is only needed
    when the chapter has more than one.
    """

    choice: str = Field(strict=True, min_length=1, max_length=10)
    decision_point_id: Optional[int] = Field(default=None, strict=True, ge=1, le=2**31 - 1)


class DecisionItem(BaseModel):
    """The choice of the user at one decision point."""

    decision_point_id: int
    choice: str
    decided_at: datetime


class DecisionResponse(DecisionItem):
    """A saved choice and where it belongs."""

    library_entry_id: int
    chapter_id: int


class ChapterProgressResponse(BaseModel):
    """What the user has recorded for a chapter.

    A chapter without data has no rating, 0 minutes and no choice. `choice` is the choice at the
    first decision point that the user answered, and `decided_at` is the time of that choice. A
    chapter with several decision points lists all choices in `decisions`, ordered by the position
    of the decision point.
    """

    model_config = ConfigDict(from_attributes=True)

    library_entry_id: int
    chapter_id: int
    rating: Optional[int] = None
    playtime_minutes: int = 0
    updated_at: Optional[datetime] = None
    choice: Optional[str] = None
    decided_at: Optional[datetime] = None
    decisions: list[DecisionItem] = []
