"""Tests for media title embeddings (issue #151)."""

import hashlib

from app.core import config
from app.models.entities import Genre, MediaEmbedding, MediaItem, MediaType
from app.services import embedding_service


def genre(db, name):
    """The genre with this name. Other tests can have made it already, and names are unique."""
    return db.query(Genre).filter_by(name=name).one_or_none() or Genre(name=name)


def make_media(db, *, description=None, genres=None):
    item = MediaItem(
        title="Test Title",
        media_type=MediaType.GAME,
        description=description,
        genres=genres or [],
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_build_embedding_text_includes_title_type_genres_and_description(db):
    item = make_media(
        db,
        description="A story about space.",
        genres=[genre(db, "Sci-Fi"), genre(db, "Adventure")],
    )

    text = embedding_service.build_embedding_text(item)

    assert "Title: Test Title" in text
    assert "Media type: GAME" in text
    assert "Genres: Adventure, Sci-Fi" in text
    assert "Description: A story about space." in text


def test_build_embedding_text_skips_items_without_genres_or_description(db):
    item = make_media(db)

    assert embedding_service.build_embedding_text(item) is None


def test_update_embedding_creates_record_and_hashes_source(db, monkeypatch):
    item = make_media(db, description="A space adventure.")
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[0.1] * config.EMBEDDING_DIMENSIONS]

    monkeypatch.setattr(embedding_service, "embed_texts", fake_embed_texts)

    assert embedding_service.update_embedding(db, item) is True

    record = (
        db.query(MediaEmbedding)
        .filter_by(
            media_item_id=item.id,
            model_name=config.EMBEDDING_MODEL,
        )
        .one()
    )
    source = embedding_service.build_embedding_text(item)

    assert record.dimension == config.EMBEDDING_DIMENSIONS
    assert record.source_text_hash == hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()
    assert len(calls) == 1


def test_update_embedding_does_not_call_client_when_text_is_unchanged(
    db, monkeypatch
):
    item = make_media(db, description="A space adventure.")
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[0.1] * config.EMBEDDING_DIMENSIONS]

    monkeypatch.setattr(embedding_service, "embed_texts", fake_embed_texts)

    assert embedding_service.update_embedding(db, item) is True
    assert embedding_service.update_embedding(db, item) is False
    assert len(calls) == 1


def test_update_embedding_refreshes_record_when_text_changes(db, monkeypatch):
    item = make_media(db, description="The first description.")
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[float(len(calls)) / 10] * config.EMBEDDING_DIMENSIONS]

    monkeypatch.setattr(embedding_service, "embed_texts", fake_embed_texts)

    assert embedding_service.update_embedding(db, item) is True
    first_hash = (
        db.query(MediaEmbedding)
        .filter_by(
            media_item_id=item.id,
            model_name=config.EMBEDDING_MODEL,
        )
        .one()
        .source_text_hash
    )

    item.description = "A changed description."
    db.commit()

    assert embedding_service.update_embedding(db, item) is True

    record = (
        db.query(MediaEmbedding)
        .filter_by(
            media_item_id=item.id,
            model_name=config.EMBEDDING_MODEL,
        )
        .one()
    )
    assert record.source_text_hash != first_hash
    assert len(calls) == 2


def test_safely_update_embedding_handles_client_errors(db, monkeypatch):
    item = make_media(db, description="A space adventure.")

    def failing_embed_texts(texts):
        raise RuntimeError("simulated embedding failure")

    monkeypatch.setattr(
        embedding_service, "embed_texts", failing_embed_texts
    )

    assert embedding_service.safely_update_embedding(db, item) is False
    assert (
        db.query(MediaEmbedding)
        .filter_by(
            media_item_id=item.id,
            model_name=config.EMBEDDING_MODEL,
        )
        .one_or_none()
        is None
    )
