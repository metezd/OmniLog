"""Content-based recommendations for US-13."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core import config
from app.models.entities import (
    MediaEmbedding,
    MediaItem,
    MediaType,
    UserLibrary,
    WatchStatus,
)

logger = logging.getLogger(__name__)


def get_recommendations(
    db: Session,
    user_id: int,
    target: MediaType,
    limit: int = 10,
) -> list[MediaItem]:
    """Recommend titles of the requested type without exposing other users' taste."""
    owned_ids = select(UserLibrary.media_item_id).where(
        UserLibrary.user_id == user_id
    )

    try:
        liked_rows = (
            db.query(MediaEmbedding.embedding)
            .join(
                UserLibrary,
                UserLibrary.media_item_id == MediaEmbedding.media_item_id,
            )
            .filter(
                UserLibrary.user_id == user_id,
                MediaEmbedding.model_name == config.EMBEDDING_MODEL,
                (
                    (UserLibrary.rating >= 7)
                    | (
                        UserLibrary.rating.is_(None)
                        & (UserLibrary.status == WatchStatus.COMPLETED)
                    )
                ),
            )
            .all()
        )
    except Exception:
        logger.exception("Could not load taste embeddings; using fallback")
        db.rollback()
        liked_rows = []

    taste_vector = None
    if liked_rows:
        vectors = [row[0] for row in liked_rows]
        taste_vector = [
            sum(float(vector[index]) for vector in vectors) / len(vectors)
            for index in range(len(vectors[0]))
        ]

    base_query = (
        db.query(MediaItem)
        .options(selectinload(MediaItem.genres))
        .filter(
            MediaItem.media_type == target,
            ~MediaItem.id.in_(owned_ids),
        )
    )

    if taste_vector is not None:
        try:
            scored_query = (
                db.query(
                    MediaItem,
                    MediaEmbedding.embedding.cosine_distance(taste_vector).label(
                        "distance"
                    ),
                )
                .join(
                    MediaEmbedding,
                    (MediaEmbedding.media_item_id == MediaItem.id)
                    & (MediaEmbedding.model_name == config.EMBEDDING_MODEL),
                )
                .options(selectinload(MediaItem.genres))
                .filter(
                    MediaItem.media_type == target,
                    ~MediaItem.id.in_(owned_ids),
                )
                .order_by("distance", MediaItem.id)
                .limit(limit)
            )
            scored_items = [row[0] for row in scored_query.all()]
            scored_ids = {item.id for item in scored_items}

            if len(scored_items) >= limit:
                return scored_items

            unembedded_items = (
                base_query
                .filter(
                    ~MediaItem.id.in_(scored_ids),
                    ~MediaItem.id.in_(
                        db.query(MediaEmbedding.media_item_id).filter(
                            MediaEmbedding.model_name == config.EMBEDDING_MODEL
                        )
                    ),
                )
                .order_by(MediaItem.id)
                .limit(limit - len(scored_items))
                .all()
            )
            return scored_items + unembedded_items
        except Exception:
            logger.exception("Vector recommendation query failed; using fallback")
            # PostgreSQL marks the current transaction failed after a SQL error. Clear it
            # before issuing the fallback query so a missing vector operator stays recoverable.
            db.rollback()

    # Fallback for users without usable taste vectors or when vector search is unavailable.
    # Prefer titles that appear most often in libraries, then use a stable ID tie-breaker.
    popularity = (
        db.query(
            UserLibrary.media_item_id.label("media_id"),
            func.count(UserLibrary.id).label("library_count"),
        )
        .group_by(UserLibrary.media_item_id)
        .subquery()
    )

    return (
        base_query
        .outerjoin(popularity, popularity.c.media_id == MediaItem.id)
        .order_by(func.coalesce(popularity.c.library_count, 0).desc(), MediaItem.id)
        .limit(limit)
        .all()
    )
