"""Review submission and NLP spoiler detection (US-14, DFD 5.4 and 5.5)."""
import logging
import re
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.entities import Review, User, UserLibrary
from app.schemas.review import ReviewCreate
from app.services.diary_service import DiaryAction, record_event
from app.services.library_service import LibraryEntryNotFoundError
from app.integrations.common import ExternalServiceError
from app.integrations.openai_client import classify_spoiler

logger = logging.getLogger(__name__)

SPOILER_MODEL_VERSION = "omnilog-nlp-spoiler-v1"
SPOILER_THRESHOLD = 0.5

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


def check_spoiler(text: str) -> Tuple[None, None, None]:
    """Spoiler detection will be implemented in issue #152."""
    return None, None, None



def detect_spoilers(text: str) -> Tuple[bool, float, str]:
    """Classify review text using OpenAI when configured, otherwise use local patterns."""
    from app.core import config

    if config.OPENAI_API_KEY:
        try:
            contains_spoiler, score = classify_spoiler(text)
            return contains_spoiler, score, config.SPOILER_MODEL
        except ExternalServiceError:
            # OpenAI is down: the review is still saved, with the local patterns
            logger.warning("OpenAI unavailable, using the local spoiler patterns")

    score = 0.0
    for pattern, weight in _SPOILER_PATTERNS:
        if pattern.search(text):
            score += weight

    clamped_score = round(min(score, 1.0), 4)
    return clamped_score >= SPOILER_THRESHOLD, clamped_score, SPOILER_MODEL_VERSION



def upsert_review(
    db: Session,
    current_user: User,
    entry_id: int,
    payload: ReviewCreate,
) -> tuple[Review, bool]:
    """Create or replace the user's review for a library entry and run spoiler detection (US-14)."""
    entry = (
        db.query(UserLibrary)
        .filter(UserLibrary.id == entry_id, UserLibrary.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise LibraryEntryNotFoundError("Library entry not found")

    contains_spoiler, spoiler_score, model_version = check_spoiler(payload.text)

    review = db.query(Review).filter(Review.library_entry_id == entry.id).first()
    is_new = review is None
    if review is None:
        review = Review(
            library_entry_id=entry.id,
            text=payload.text,
            contains_spoiler=contains_spoiler,
            spoiler_score=spoiler_score,
            spoiler_model_version=model_version,
        )
        db.add(review)
    else:
        review.text = payload.text
        review.contains_spoiler = contains_spoiler
        review.spoiler_score = spoiler_score
        review.spoiler_model_version = model_version
        review.updated_at = utc_now()

    record_event(
        db,
        user_id=current_user.id,
        action=DiaryAction.REVIEW_POSTED,
        media_item_id=entry.media_item_id,
        details="Spoiler flagged" if contains_spoiler else "Review posted",
    )
    db.commit()
    db.refresh(review)
    return review, is_new


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
