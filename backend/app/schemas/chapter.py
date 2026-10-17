"""Schemas for the personal record of a chapter or episode (US-10)."""
from datetime import datetime

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
