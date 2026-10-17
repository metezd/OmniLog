"""Schemas for the personal record of a chapter or episode (US-10)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChapterRatingUpdate(BaseModel):
    """The rating of one chapter or episode.

    strict=True: JSON whole numbers only. Without it, 4.0 and "4" would be accepted (BR-10).
    """

    rating: int = Field(strict=True, ge=1, le=5)


class ChapterRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    library_entry_id: int
    chapter_id: int
    rating: Optional[int] = None
    updated_at: Optional[datetime] = None
