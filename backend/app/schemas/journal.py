from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# --- US-06: Custom Lists ---
class CustomListCreate(BaseModel):
    name: str = Field(..., min_length=1)


class CustomListItemCreate(BaseModel):
    media_item_id: int


class CustomListItemResponse(BaseModel):
    id: int
    list_id: int
    media_item_id: int
    added_at: datetime

    class Config:
        from_attributes = True


class CustomListResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    items: List[CustomListItemResponse] = []

    class Config:
        from_attributes = True


# --- US-07: Activity Diary ---
class DiaryEntryResponse(BaseModel):
    id: int
    media_item_id: int
    action: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True