"""Schema of the personal statistics (US-15)."""
from typing import Dict, List

from pydantic import BaseModel


class GenreCount(BaseModel):
    genre: str
    count: int


class PlaytimeBucket(BaseModel):
    """Titles with a total playtime in one range, for example `5-10h`, or `100+h` at 100+ hours."""

    bucket: str
    count: int


class PlaytimeStats(BaseModel):
    """Playtime summary with exact total_minutes and a histogram of at most 21 buckets."""

    total_minutes: int
    histogram: List[PlaytimeBucket]


class StatsResponse(BaseModel):
    """Numbers computed from the library of the logged-in user.

    `media_split` has every media type and whole percents that add up to 100 (all 0 for an empty
    library). `rating_distribution` has the keys "1" to "10". `genre_breakdown` is sorted by count,
    largest first.
    """

    total_items: int
    media_split: Dict[str, int]
    rating_distribution: Dict[str, int]
    genre_breakdown: List[GenreCount]
    playtime: PlaytimeStats
