"""Backfill missing or stale media embeddings."""

import argparse
import hashlib
import sys

from app.core import config
from app.core.database import SessionLocal
from app.models.entities import MediaEmbedding, MediaItem
from app.services.embedding_service import (
    build_embedding_text,
    safely_update_embedding,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or update embeddings for media titles."
    )
    parser.parse_args()

    db = SessionLocal()
    created = updated = skipped = failed = 0

    try:
        items = db.query(MediaItem).order_by(MediaItem.id).all()

        for item in items:
            source_text = build_embedding_text(item)
            if source_text is None:
                skipped += 1
                continue

            source_hash = hashlib.sha256(
                source_text.encode("utf-8")
            ).hexdigest()

            existing = (
                db.query(MediaEmbedding)
                .filter_by(
                    media_item_id=item.id,
                    model_name=config.EMBEDDING_MODEL,
                )
                .one_or_none()
            )

            if existing is not None and existing.source_text_hash == source_hash:
                skipped += 1
                continue

            was_created = existing is None
            if safely_update_embedding(db, item):
                db.commit()
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                failed += 1

        print(f"Embeddings created: {created}")
        print(f"Embeddings updated: {updated}")
        print(f"Titles skipped: {skipped}")
        print(f"Failures: {failed}")
        return 1 if failed else 0
    except Exception as exc:
        print(
            f"Embedding backfill failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
