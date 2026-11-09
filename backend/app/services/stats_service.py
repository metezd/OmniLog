"""Personal statistics of a user's library (US-15, process 6.1 to 6.5).

Everything is computed from the library of the user on each request. Epic 6 has no tables of its
own. The Redis cache of the design (`omni:stats:{user_id}`) is not used yet: a cache needs the
clearing after every change of the library and of the playtime, and the two come together.
"""
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

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

# A bucket of the playtime histogram is 5 hours wide
BUCKET_MINUTES = 5 * 60
MIN_RATING, MAX_RATING = 1, 10


def get_stats(db: Session, user: User) -> StatsResponse:
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

    return StatsResponse(
        total_items=len(rows),
        media_split=_media_split(type_counts),
        rating_distribution=_rating_distribution([rating for _, _, rating in rows]),
        genre_breakdown=_genre_breakdown(genre_rows),
        playtime=_playtime_stats([playtime_by_entry.get(entry_id, 0) for entry_id, _, _ in rows]),
    )


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
    5 hours is in `5-10h`. Buckets between the first and the last are listed even when they are
    empty, so a chart has no gaps.
    """
    if not totals:
        return PlaytimeStats(total_minutes=0, histogram=[])

    counts = [0] * (max(totals) // BUCKET_MINUTES + 1)
    for minutes in totals:
        counts[minutes // BUCKET_MINUTES] += 1

    hours = BUCKET_MINUTES // 60
    histogram = [
        PlaytimeBucket(bucket=f"{index * hours}-{(index + 1) * hours}h", count=count)
        for index, count in enumerate(counts)
    ]
    return PlaytimeStats(total_minutes=sum(totals), histogram=histogram)
