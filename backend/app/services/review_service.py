"""Review submission and NLP spoiler detection (US-14, DFD 5.4 and 5.5)."""
import logging
import re
from typing import Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import config
from app.core.clock import utc_now
from app.models.entities import Review, User, UserLibrary
from app.schemas.review import ReviewCreate
from app.services.diary_service import DiaryAction, record_event
from app.services.library_service import LibraryEntryNotFoundError
from app.integrations.common import ExternalServiceError
from app.integrations.openai_client import classify_spoiler

logger = logging.getLogger(__name__)

SPOILER_MODEL_VERSION = "omnilog-nlp-spoiler-v1"

# Weighted plot-revelation patterns used by the local NLP spoiler classifier when an external
# LLM/transformer endpoint is not configured.
_SPOILER_PATTERNS: list[Tuple[re.Pattern[str], float]] = [
    (re.compile(r"\b(dies|died|death\s+of)\b", re.I), 0.55),
    (re.compile(r"\b(gets\s+killed|is\s+killed|murdered)\b", re.I), 0.55),
    (re.compile(r"\b(sacrifices\s+himself|sacrifices\s+herself)\b", re.I), 0.55),
    (re.compile(r"\b(turns\s+out|all\s+along|was\s+the\s+killer)\b", re.I), 0.55),
    (re.compile(r"\b(is\s+the\s+killer|is\s+the\s+traitor)\b", re.I), 0.55),
    (re.compile(r"\b(betrays|secretly\s+alive)\b", re.I), 0.55),
    (re.compile(r"\b(in\s+the\s+(final|last)\s+(chapter|episode|act|scene))\b", re.I), 0.45),
    (re.compile(r"\b(at\s+the\s+end\s+of\s+the\s+(game|series|season|story))\b", re.I), 0.45),
    (re.compile(r"\b(plot\s+twist|ending\s+reveal|spoiler\s*alert)\b", re.I), 0.70),
    (re.compile(r"(\[spoiler\]|\bmajor\s+spoiler\b)", re.I), 0.70),
    (re.compile(r"\b(main\s+character|protagonist|narrator|villain)\s+(dies|is\s+dead|was\s+dead|is\s+the)\b", re.I), 0.60),
]


# (contains_spoiler, score, model_version). All three are None when the review was not checked.
SpoilerResult = Tuple[Optional[bool], Optional[float], Optional[str]]


def detect_spoilers(text: str) -> SpoilerResult:
    """Classify review text. Never raises for an outside failure.

    With OPENAI_API_KEY set, OpenAI decides. When it fails, the review is "not checked" and the
    result is (None, None, None). Without a key, the local patterns decide (US-14).
    This function must be called without an open database transaction: the OpenAI call can wait
    up to OPENAI_TIMEOUT_SECONDS for each of its tries.
    """
    if config.OPENAI_API_KEY:
        try:
            contains_spoiler, score = classify_spoiler(text)
        except ExternalServiceError:
            logger.warning("OpenAI spoiler check failed, the review stays unchecked")
            return None, None, None
        except Exception:  # noqa: BLE001 - a failed check must never fail the saved review
            logger.exception("Unexpected error in the spoiler check, the review stays unchecked")
            return None, None, None
        return contains_spoiler, score, config.SPOILER_MODEL

    score = 0.0
    for pattern, weight in _SPOILER_PATTERNS:
        if pattern.search(text):
            score += weight

    clamped_score = round(min(score, 1.0), 4)
    return clamped_score >= config.SPOILER_THRESHOLD, clamped_score, SPOILER_MODEL_VERSION


def upsert_review(
    db: Session,
    current_user: User,
    entry_id: int,
    payload: ReviewCreate,
) -> tuple[Review, bool]:
    """Create or replace the user's review for a library entry and run spoiler detection (US-14).

    Three steps, so no database connection is held while OpenAI answers:
    1. Save the review with the spoiler fields NULL ("not checked") and commit.
    2. Run the spoiler check. No transaction is open here.
    3. Write the result in a second short transaction.
    A failed check leaves the fields NULL. The review is never lost because of it.
    """
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise LibraryEntryNotFoundError("Library entry not found")

    # Read what is needed later now: after the commit, the objects are expired and reading
    # them would open a new transaction.
    text = payload.text
    user_id = current_user.id
    media_item_id = entry.media_item_id

    # Step 1: save first. A changed text invalidates an older result, so the fields are reset.
    review = db.query(Review).filter(Review.library_entry_id == entry.id).first()
    is_new = review is None
    if review is None:
        review = Review(library_entry_id=entry.id, text=text)
        db.add(review)
    else:
        review.text = text
        review.contains_spoiler = None
        review.spoiler_score = None
        review.spoiler_model_version = None
        review.updated_at = utc_now()

    record_event(
        db,
        user_id=user_id,
        action=DiaryAction.REVIEW_POSTED,
        media_item_id=media_item_id,
        details="Review posted",
    )
    db.flush()  # gives a new review its id
    review_id = review.id
    db.commit()  # ends the transaction and returns the connection to the pool

    # Step 2: the check, without an open transaction.
    contains_spoiler, spoiler_score, model_version = detect_spoilers(text)

    # Step 3: write the result.
    if model_version is not None:
        _store_spoiler_result(
            db, review_id, text, contains_spoiler, spoiler_score, model_version
        )

    review = db.get(Review, review_id)
    return review, is_new


def _store_spoiler_result(
    db: Session,
    review_id: int,
    text: str,
    contains_spoiler: Optional[bool],
    spoiler_score: Optional[float],
    model_version: str,
) -> None:
    """Write the check result. A failure here is logged and leaves the review unchecked."""
    try:
        # One UPDATE with the text in the WHERE: when the review was deleted or edited while
        # the check ran, the result belongs to an old text and nothing is written.
        # updated_at is set to itself, so the result does not count as an edit of the review.
        db.query(Review).filter(Review.id == review_id, Review.text == text).update(
            {
                Review.contains_spoiler: contains_spoiler,
                Review.spoiler_score: spoiler_score,
                Review.spoiler_model_version: model_version,
                Review.updated_at: Review.updated_at,
            },
            synchronize_session=False,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not store the spoiler result of review %s", review_id)


def get_review(db: Session, current_user: User, entry_id: int) -> Review | None:
    """Return the review for a library entry owned by the current user, or None if not written yet."""
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise LibraryEntryNotFoundError("Library entry not found")

    return db.query(Review).filter(Review.library_entry_id == entry.id).first()
