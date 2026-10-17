"""Business logic for the personal record of a chapter or episode (US-10 and US-11).

Process 4.1 (validate chapter access), 4.2 (rate chapter), 4.3 (log playtime) and 4.5 (serve
chapter progress) in docs/analysis/behavior/dfd-epic4-episodic.md.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import (
    Chapter,
    ChapterKind,
    ChapterProgress,
    PlaytimeLog,
    User,
    UserLibrary,
)
from app.services.diary_service import DiaryAction, record_event
from app.services.library_service import LibraryEntryNotFoundError

# The unique constraint that two first requests for the same chapter can collide on
PROGRESS_UNIQUE_CONSTRAINT = "uq_progress_entry_chapter"
# PostgreSQL error code of a unique violation
UNIQUE_VIOLATION = "23505"

# The total playtime of one chapter. About 19 years, far below the limit of the INTEGER column.
MAX_TOTAL_PLAYTIME_MINUTES = 10_000_000


class ChapterNotFoundError(Exception):
    """The chapter does not exist, or it does not belong to the title of the library entry.

    Both cases raise the same error, so a user cannot probe the chapters of other titles.
    """


class PlaytimeLimitError(Exception):
    """The new entry would make the total playtime of the chapter too large."""


def get_chapter_context(
    db: Session, user: User, entry_id: int, chapter_id: int
) -> tuple[UserLibrary, Chapter]:
    """Process 4.1: the entry must be the user's own, and the chapter must belong to its title.

    Raises LibraryEntryNotFoundError or ChapterNotFoundError. No data is changed (BR-11).
    """
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == user.id)
        .first()
    )
    if entry is None:
        raise LibraryEntryNotFoundError("Library entry not found")

    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.media_item_id == entry.media_item_id)
        .first()
    )
    if chapter is None:
        raise ChapterNotFoundError("Chapter not found")
    return entry, chapter


def _find_progress(db: Session, entry_id: int, chapter_id: int) -> ChapterProgress | None:
    return (
        db.query(ChapterProgress)
        .filter(
            ChapterProgress.library_entry_id == entry_id,
            ChapterProgress.chapter_id == chapter_id,
        )
        .first()
    )


def _is_duplicate_progress(exc: IntegrityError) -> bool:
    """True only when the error is the unique violation of uq_progress_entry_chapter.

    That is the one expected race: two requests create the progress row of the same chapter at
    the same moment. A foreign key, a check constraint or any other unique violation is a real
    error.
    """
    original = exc.orig
    diag = getattr(original, "diag", None)
    return (
        getattr(original, "pgcode", None) == UNIQUE_VIOLATION
        and getattr(diag, "constraint_name", None) == PROGRESS_UNIQUE_CONSTRAINT
    )


def _get_or_create_progress(
    db: Session, entry_pk: int, chapter_pk: int, media_item_id: int, rating: int | None = None
) -> tuple[ChapterProgress, bool]:
    """Return the progress row of the entry and chapter, and whether this call created it.

    The row is created by the first rating or the first playtime entry. The new row gets the
    given rating. An existing row is returned as it is.
    """
    progress = _find_progress(db, entry_pk, chapter_pk)
    if progress is not None:
        return progress, False

    try:
        # A savepoint: when the INSERT fails, only the INSERT is undone and the session
        # stays usable. The INSERT is sent when the block ends.
        with db.begin_nested():
            progress = ChapterProgress(
                library_entry_id=entry_pk,
                chapter_id=chapter_pk,
                media_item_id=media_item_id,
                rating=rating,
            )
            db.add(progress)
        return progress, True
    except IntegrityError as exc:
        if not _is_duplicate_progress(exc):
            db.rollback()
            raise  # a real database error, not the race. The cause stays visible.
        # Another request created the row at the same moment. It exists now, so use it.
        progress = _find_progress(db, entry_pk, chapter_pk)
        if progress is None:
            db.rollback()
            raise
        return progress, False


def _kind_label(chapter: Chapter) -> str:
    return "episode" if chapter.kind == ChapterKind.EPISODE else "chapter"


def rate_chapter(
    db: Session, user: User, entry_id: int, chapter_id: int, rating: int
) -> ChapterProgress:
    """Process 4.2: save the rating of a chapter. A new rating replaces the old one.

    A CHAPTER_RATED event is written only when the rating really changes, so sending the same
    rating again changes nothing and commits nothing (updated_at stays as it was).
    """
    entry, chapter = get_chapter_context(db, user, entry_id, chapter_id)

    # Plain values are kept here, because a rollback expires the loaded objects
    user_id = user.id
    media_item_id = entry.media_item_id
    event_text = f"Rated {_kind_label(chapter)} {chapter.number} as {rating}"

    progress, changed = _get_or_create_progress(
        db, entry.id, chapter.id, media_item_id, rating=rating
    )

    if not changed and progress.rating != rating:
        progress.rating = rating
        changed = True

    if not changed:
        return progress  # the same rating again: no event, no update, no commit

    record_event(db, user_id, DiaryAction.CHAPTER_RATED, media_item_id, event_text)
    db.commit()
    db.refresh(progress)
    return progress


def log_playtime(
    db: Session, user: User, entry_id: int, chapter_id: int, minutes: int
) -> tuple[PlaytimeLog, ChapterProgress]:
    """Process 4.3: add one playtime entry and add its minutes to the total of the chapter.

    The entry, the new total and the PLAYTIME_LOGGED event are saved in one transaction. The
    total is raised by the database itself (SET total = total + minutes), so two entries sent at
    the same moment are both counted.
    """
    entry, chapter = get_chapter_context(db, user, entry_id, chapter_id)

    user_id = user.id
    media_item_id = entry.media_item_id
    event_text = f"Logged {minutes} min on {_kind_label(chapter)} {chapter.number}"

    progress, _ = _get_or_create_progress(db, entry.id, chapter.id, media_item_id)

    if progress.playtime_minutes + minutes > MAX_TOTAL_PLAYTIME_MINUTES:
        raise PlaytimeLimitError("The total playtime of a chapter is too large")

    log = PlaytimeLog(chapter_progress_id=progress.id, minutes=minutes)
    db.add(log)
    db.query(ChapterProgress).filter(ChapterProgress.id == progress.id).update(
        {ChapterProgress.playtime_minutes: ChapterProgress.playtime_minutes + minutes},
        synchronize_session=False,
    )
    record_event(db, user_id, DiaryAction.PLAYTIME_LOGGED, media_item_id, event_text)
    db.commit()
    db.refresh(log)
    db.refresh(progress)
    return log, progress


def get_chapter_progress(
    db: Session, user: User, entry_id: int, chapter_id: int
) -> tuple[UserLibrary, Chapter, ChapterProgress | None]:
    """Process 4.5: what the user has recorded for a chapter. The progress is None when there is
    no data yet. Nothing is created or changed by reading."""
    entry, chapter = get_chapter_context(db, user, entry_id, chapter_id)
    return entry, chapter, _find_progress(db, entry.id, chapter.id)
