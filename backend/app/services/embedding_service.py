"""Create and maintain vector embeddings for media titles (issue #151)."""

from __future__ import annotations

import hashlib
import logging

from sqlalchemy.orm import Session

from app.core import background, config
from app.core.database import SessionLocal
from app.integrations.openai_client import embed_texts
from app.models.entities import MediaEmbedding, MediaItem

logger = logging.getLogger(__name__)


def build_embedding_text(item: MediaItem) -> str | None:
    """Build stable text for embedding; skip titles without genres or description."""
    genres = sorted(
        genre.name.strip()
        for genre in item.genres
        if genre.name and genre.name.strip()
    )
    description = (item.description or "").strip()

    if not genres and not description:
        return None

    media_type = getattr(item.media_type, "value", item.media_type)
    parts = [
        f"Title: {item.title.strip()}",
        f"Media type: {media_type}",
    ]
    if genres:
        parts.append(f"Genres: {', '.join(genres)}")
    if description:
        parts.append(f"Description: {description}")

    return "\n".join(parts)


def _source_hash(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def _stored(db: Session, item: MediaItem) -> MediaEmbedding | None:
    return (
        db.query(MediaEmbedding)
        .filter_by(media_item_id=item.id, model_name=config.EMBEDDING_MODEL)
        .one_or_none()
    )


def needs_embedding(db: Session, item: MediaItem) -> bool:
    """True when the title has text for an embedding and no stored one for that text."""
    source_text = build_embedding_text(item)
    if source_text is None:
        return False
    existing = _stored(db, item)
    return existing is None or existing.source_text_hash != _source_hash(source_text)


def update_embedding(db: Session, item: MediaItem) -> bool:
    """Create or update an embedding in a savepoint; do not commit the caller's session."""
    source_text = build_embedding_text(item)
    if source_text is None:
        return False

    source_hash = _source_hash(source_text)
    model_name = config.EMBEDDING_MODEL

    existing = _stored(db, item)
    if existing is not None and existing.source_text_hash == source_hash:
        return False

    vectors = embed_texts([source_text])
    if len(vectors) != 1:
        raise ValueError("Expected exactly one embedding vector")

    vector = vectors[0]
    if len(vector) != config.EMBEDDING_DIMENSIONS:
        raise ValueError("Embedding dimension does not match configuration")

    with db.begin_nested():
        if existing is None:
            db.add(
                MediaEmbedding(
                    media_item_id=item.id,
                    model_name=model_name,
                    embedding=vector,
                    dimension=len(vector),
                    source_text_hash=source_hash,
                )
            )
        else:
            existing.embedding = vector
            existing.dimension = len(vector)
            existing.source_text_hash = source_hash

        db.flush()

    return True


def safely_update_embedding(db: Session, item: MediaItem) -> bool:
    """Log embedding failures without rolling back the caller's whole transaction."""
    try:
        return update_embedding(db, item)
    except Exception:
        logger.exception("Could not update embedding for media item %s", item.id)
        return False


def schedule_embedding(db: Session, item: MediaItem) -> bool:
    """Make the embedding of a title after the answer, when it needs one (#382).

    The title details (GET /catalog/{id}) call this instead of waiting for OpenAI. Without
    OPENAI_API_KEY nothing is scheduled. True when a job was added.
    """
    if not config.OPENAI_API_KEY or not needs_embedding(db, item):
        return False
    return background.submit_once(f"embedding:{item.id}", _embed_in_background, item.id)


def _embed_in_background(media_item_id: int) -> None:
    db = SessionLocal()
    try:
        item = db.get(MediaItem, media_item_id)
        if item is not None and safely_update_embedding(db, item):
            db.commit()
    finally:
        db.close()
