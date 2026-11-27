"""The embedding of a title is saved once, and later opens do not call OpenAI again (#390).

Before #382, GET /catalog/{id} made the embedding inside the request and only flushed it, so the
closed session rolled it back: three opens gave three paid OpenAI calls and no row.
"""
from app.core import background, config
from app.models.entities import MediaEmbedding
from app.services import embedding_service


def test_three_opens_make_one_call_and_one_row(client, auth_headers, fake_external_apis, db, monkeypatch):
    calls = []

    def fake_embed(texts):
        calls.append(len(texts))
        return [[0.1] * config.EMBEDDING_DIMENSIONS for _ in texts]

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(embedding_service, "embed_texts", fake_embed)
    found = client.get("/catalog/search", params={"q": "Life is Strange", "type": "GAME"}, headers=auth_headers).json()
    game = next(g for g in found if g["external_api_id"] == 90001)

    for _ in range(3):
        assert client.get(f"/catalog/{game['id']}", headers=auth_headers).status_code == 200
        assert background.wait_idle(timeout=10)

    db.expire_all()
    assert calls == [1]
    assert db.query(MediaEmbedding).filter_by(media_item_id=game["id"]).count() == 1
