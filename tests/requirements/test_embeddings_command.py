"""The embeddings command `python -m app.embeddings` (US-13, #297).

It fills or refreshes the embedding of every title that has a description or genres. OpenAI is
replaced by a fake, so the command runs without a key.
"""
import re

import pytest

from app import embeddings
from app.core import config
from app.models.entities import MediaEmbedding, MediaItem, MediaType
from app.services import embedding_service
from helpers import unique


def counts(output: str) -> dict[str, int]:
    return {name: int(value) for name, value in re.findall(r"^(.+): (\d+)$", output, re.MULTILINE)}


@pytest.fixture
def command(monkeypatch, capsys):
    """Run the command with a fake OpenAI. Returns (exit code, counts, stderr)."""
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[0.2] * config.EMBEDDING_DIMENSIONS for _ in texts]

    monkeypatch.setattr(embedding_service, "embed_texts", fake_embed_texts)
    monkeypatch.setattr("sys.argv", ["embeddings"])

    def run():
        code = embeddings.main()
        out = capsys.readouterr()
        return code, counts(out.out), out.err

    run.calls = calls
    return run


@pytest.fixture
def title(db):
    item = MediaItem(title=unique("embedded"), media_type=MediaType.GAME, description="A long quest.")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def embedding_of(db, item):
    db.expire_all()
    return db.query(MediaEmbedding).filter_by(media_item_id=item.id, model_name=config.EMBEDDING_MODEL).one_or_none()


def test_us13_command_creates_then_skips_an_unchanged_embedding(db, title, command):
    code, first, _ = command()

    assert code == 0
    assert first["Embeddings created"] >= 1
    assert first["Failures"] == 0
    assert embedding_of(db, title) is not None

    code, second, _ = command()

    assert code == 0
    assert second["Embeddings created"] == 0
    assert second["Embeddings updated"] == 0
    assert second["Titles skipped"] >= 1


def test_us13_command_updates_a_changed_title(db, title, command):
    command()
    old_hash = embedding_of(db, title).source_text_hash
    title.description = "A different quest."
    db.commit()

    code, result, _ = command()

    assert code == 0
    assert result["Embeddings updated"] >= 1
    assert embedding_of(db, title).source_text_hash != old_hash


def test_us13_command_skips_a_title_without_text(db, command):
    item = MediaItem(title=unique("bare"), media_type=MediaType.MOVIE)
    db.add(item)
    db.commit()

    code, result, _ = command()

    assert code == 0
    assert result["Titles skipped"] >= 1
    assert embedding_of(db, item) is None


def test_us13_command_counts_a_failed_title_and_exits_with_1(db, title, command, monkeypatch):
    def broken(texts):
        raise RuntimeError("OpenAI is down")

    monkeypatch.setattr(embedding_service, "embed_texts", broken)

    code, result, _ = command()

    assert code == 1
    assert result["Failures"] >= 1
    assert embedding_of(db, title) is None


def test_us13_command_reports_a_database_error_and_exits_with_1(command, monkeypatch):
    class BrokenSession:
        def query(self, *args):
            raise RuntimeError("database is gone")

        def close(self):
            pass

    monkeypatch.setattr(embeddings, "SessionLocal", BrokenSession)

    code, _, err = command()

    assert code == 1
    assert "Embedding backfill failed: RuntimeError: database is gone" in err
