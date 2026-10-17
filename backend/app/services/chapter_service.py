"""Business logic for the personal record of a chapter or episode (US-10).

Process 4.1 (validate chapter access) and process 4.2 (rate chapter) in
docs/analysis/behavior/dfd-epic4-episodic.md.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Chapter, ChapterKind, ChapterProgress, User, UserLibrary
from app.services.diary_service import DiaryAction, record_event
from app.services.library_service import LibraryEntryNotFoundError


class ChapterNotFoundError(Exception):
    """The chapter does not exist, or it does not belong to the title of the library entry.

    Both cases raise the same error, so a user cannot probe the chapters of other titles.
    """


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


def rate_chapter(
    db: Session, user: User, entry_id: int, chapter_id: int, rating: int
) -> ChapterProgress:
    """Process 4.2: save the rating of a chapter. A new rating replaces the old one.

    The progress row is created by the first rating. A CHAPTER_RATED event is written only when
    the rating really changes, so sending the same rating again adds nothing to the diary.
    """
    entry, chapter = get_chapter_context(db, user, entry_id, chapter_id)

    # Plain values are kept here, because a rollback below expires the loaded objects
    user_id = user.id
    media_item_id = entry.media_item_id
    entry_pk = entry.id
    chapter_pk = chapter.id
    kind = "episode" if chapter.kind == ChapterKind.EPISODE else "chapter"
    event_text = f"Rated {kind} {chapter.number} as {rating}"

    progress = _find_progress(db, entry_pk, chapter_pk)
    changed = False

    if progress is None:
        progress = ChapterProgress(
            library_entry_id=entry_pk, chapter_id=chapter_pk, rating=rating
        )
        db.add(progress)
        try:
            db.flush()  # sends the INSERT now, so a duplicate is caught before the event is written
            changed = True
        except IntegrityError:
            # Another request created the row at the same moment. It exists now, so use it.
            db.rollback()
            progress = _find_progress(db, entry_pk, chapter_pk)
            if progress is None:
                raise

    if not changed and progress.rating != rating:
        progress.rating = rating
        changed = True

    if changed:
        record_event(db, user_id, DiaryAction.CHAPTER_RATED, media_item_id, event_text)

    db.commit()
    db.refresh(progress)
    return progress
