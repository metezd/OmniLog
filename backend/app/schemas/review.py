"""Schemas for library entry reviews and spoiler moderation (US-14)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Review text cannot be blank")
        return cleaned


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    library_entry_id: int
    text: str
    contains_spoiler: Optional[bool] = None
    spoiler_score: Optional[float] = None
    spoiler_model_version: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
