"""Schemas for custom lists (US-06) and the activity diary (US-07)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- US-06: Custom lists ---
class CustomListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be blank")
        return value


class CustomListItemCreate(BaseModel):
    media_item_id: int


class CustomListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_id: int
    media_item_id: int
    added_at: datetime


class CustomListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    items: List[CustomListItemResponse] = []


# --- US-07: Activity diary ---
class DiaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    # Empty for events that are not about a title, such as LIST_CREATED
    media_item_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime
