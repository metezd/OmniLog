"""Personal statistics of a user's library (US-15, process 6.1 to 6.5).

Everything is computed from the library of the user on each request. Epic 6 has no tables of its
own. The result is cached in Redis under `omni:stats:{user_id}` and is invalidated whenever the
user changes their library, ratings, playtime or decisions (US-15).
"""
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import cache
from app.models.entities import (
    ChapterProgress,
    Genre,
    MediaItem,
    MediaType,
    User,
    UserLibrary,
    media_item_genres,
)
from app.schemas.stats import GenreCount, PlaytimeBucket, PlaytimeStats, StatsResponse

# A bucket of the playtime histogram is 5 hours wide, capped at 100h with a final `100+h` bucket
BUCKET_MINUTES = 5 * 60
MAX_HISTOGRAM_HOURS = 100
MAX_BUCKET_INDEX = (MAX_HISTOGRAM_HOURS * 60) // BUCKET_MINUTES  # 20 -> at most 21 buckets (0..20)
OVERFLOW_BUCKET_LABEL = f"{MAX_HISTOGRAM_HOURS}+h"
MIN_RATING, MAX_RATING = 1, 10

# Cache TTL: 24 hours. The key is always deleted on write, so staleness is not a concern.
_STATS_TTL_SECONDS = 24 * 60 * 60
_STATS_KEY_PREFIX = "omni:stats:"


def _stats_key(user_id: int) -> str:
    return f"{_STATS_KEY_PREFIX}{user_id}"


def invalidate_stats_cache(user_id: int) -> None:
    """Delete the cached statistics for one user.

    Called by every service that changes library entries, ratings, playtime or decisions so
    that the next GET /stats recomputes fresh numbers.
    """
    cache.clear_prefix(_stats_key(user_id))


def get_stats(db: Session, user: User) -> StatsResponse:
    key = _stats_key(user.id)
    cached = cache.get_json(key)
    if cached is not None:
        return StatsResponse(**cached)

    # 6.1 Collect the data. Only the library of the logged-in user is read (BR-16).
    rows = (
        db.query(UserLibrary.id, MediaItem.media_type, UserLibrary.rating)
        .join(MediaItem, MediaItem.id == UserLibrary.media_item_id)
        .filter(UserLibrary.user_id == user.id)
        .all()
    )
    playtime_by_entry = _playtime_by_entry(db, user)
    genre_rows = (
        db.query(Genre.name, func.count(UserLibrary.id))
        .join(media_item_genres, media_item_genres.c.genre_id == Genre.id)
        .join(UserLibrary, UserLibrary.media_item_id == media_item_genres.c.media_item_id)
        .filter(UserLibrary.user_id == user.id)
        .group_by(Genre.name)
        .all()
    )

    # 6.2 to 6.4 work on data in memory
    type_counts = {media_type: 0 for media_type in MediaType}
    for _, media_type, _ in rows:
        type_counts[media_type] += 1

    result = StatsResponse(
        total_items=len(rows),
        media_split=_media_split(type_counts),
        rating_distribution=_rating_distribution([rating for _, _, rating in rows]),
        genre_breakdown=_genre_breakdown(genre_rows),
        playtime=_playtime_stats([playtime_by_entry.get(entry_id, 0) for entry_id, _, _ in rows]),
    )
    cache.set_json(key, result.model_dump(mode="json"), _STATS_TTL_SECONDS)
    return result


def _playtime_by_entry(db: Session, user: User) -> Dict[int, int]:
    """Total minutes for each library entry. An entry without playtime is not in the result."""
    rows = (
        db.query(ChapterProgress.library_entry_id, func.sum(ChapterProgress.playtime_minutes))
        .join(UserLibrary, UserLibrary.id == ChapterProgress.library_entry_id)
        .filter(UserLibrary.user_id == user.id)
        .group_by(ChapterProgress.library_entry_id)
        .all()
    )
    return {entry_id: int(total) for entry_id, total in rows}


def _media_split(type_counts: Dict[MediaType, int]) -> Dict[str, int]:
    """Whole percents that add up to 100. The largest remainders get the leftover points, so a
    split of three equal types is 34, 33 and 33 and never 99 (rule 6.2)."""
    total = sum(type_counts.values())
    if total == 0:
        return {media_type.value: 0 for media_type in MediaType}

    percents = {media_type: type_counts[media_type] * 100 // total for media_type in MediaType}
    leftover = 100 - sum(percents.values())
    # Largest remainder first. A tie goes to the earlier media type, so the answer is stable.
    by_remainder = sorted(
        MediaType, key=lambda media_type: -(type_counts[media_type] * 100 % total)
    )
    for media_type in by_remainder[:leftover]:
        percents[media_type] += 1
    return {media_type.value: percents[media_type] for media_type in MediaType}


def _rating_distribution(ratings: List[float]) -> Dict[str, int]:
    """Count of entries for each rating from 1 to 10. A rating with a decimal is rounded to the
    nearest whole number, halves go up. Entries without a rating are not counted (rule 6.2)."""
    distribution = {str(value): 0 for value in range(MIN_RATING, MAX_RATING + 1)}
    for rating in ratings:
        if rating is None:
            continue
        rounded = min(max(int(rating + 0.5), MIN_RATING), MAX_RATING)
        distribution[str(rounded)] += 1
    return distribution


def _genre_breakdown(genre_rows) -> List[GenreCount]:
    """One count for each genre, largest first. Equal counts are sorted by name (rule 6.3)."""
    ordered = sorted(genre_rows, key=lambda row: (-row[1], row[0]))
    return [GenreCount(genre=name, count=count) for name, count in ordered]


def _playtime_stats(totals: List[int]) -> PlaytimeStats:
    """Total minutes of the library and a histogram of the titles by their own total (rule 6.4).

    A title with no playtime is in the first bucket. A bucket includes its lower edge, so exactly
    5 hours is in `5-10h`. Buckets up to the highest active bucket are listed even when empty so
    a chart has no gaps, capped at `100+h` (at most 21 buckets). `total_minutes` is never capped.
    """
    if not totals:
        return PlaytimeStats(total_minutes=0, histogram=[])

    raw_indices = [min(max(minutes, 0) // BUCKET_MINUTES, MAX_BUCKET_INDEX) for minutes in totals]
    last_index = max(raw_indices)
    counts = [0] * (last_index + 1)
    for idx in raw_indices:
        counts[idx] += 1

    hours = BUCKET_MINUTES // 60
    histogram: List[PlaytimeBucket] = []
    for index, count in enumerate(counts):
        if index == MAX_BUCKET_INDEX:
            label = OVERFLOW_BUCKET_LABEL
        else:
            label = f"{index * hours}-{(index + 1) * hours}h"
        histogram.append(PlaytimeBucket(bucket=label, count=count))

    return PlaytimeStats(total_minutes=sum(totals), histogram=histogram)
