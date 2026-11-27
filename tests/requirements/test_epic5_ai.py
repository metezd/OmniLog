"""Epic 5 - AI-Powered Cross-Media Engine and Review Moderation (US-13, US-14)."""
import pytest

from app.models.entities import Review
from helpers import add_to_library, create_media


# ---------------------------------------------------------------- US-13
def test_us13_cross_media_recommendations(client, auth_headers):
    """US-13: after completing a game, I get series I do not own yet."""
    game = create_media(client, auth_headers, media_type="GAME")
    add_to_library(client, auth_headers, game["id"], status="COMPLETED", rating=9)
    create_media(client, auth_headers, media_type="SERIES")  # candidate to recommend

    response = client.get(
        "/recommendations", params={"target": "SERIES"}, headers=auth_headers
    )
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) > 0
    assert all(item["media_type"] == "SERIES" for item in recommendations)

    library = client.get("/library", headers=auth_headers).json()
    owned_ids = {entry["media_item_id"] for entry in library}
    assert all(item["id"] not in owned_ids for item in recommendations)


def test_us13_recommendations_with_empty_library(client, auth_headers):
    """US-13: an empty library still returns 200 and a list."""
    response = client.get(
        "/recommendations", params={"target": "SERIES"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)



def test_us13_recommendations_falls_back_when_taste_embedding_query_fails(
    client, auth_headers, monkeypatch, db
):
    """US-13: taste embedding query failures should use popularity fallback."""
    from sqlalchemy import func

    from app.models.entities import MediaItem, MediaType, User, UserLibrary
    from app.services import recommendations_service
    from helpers import new_credentials

    candidate = create_media(client, auth_headers, media_type="SERIES")

    existing_popularity = (
        db.query(
            UserLibrary.media_item_id,
            func.count(UserLibrary.id).label("library_count"),
        )
        .join(MediaItem, MediaItem.id == UserLibrary.media_item_id)
        .filter(MediaItem.media_type == MediaType.SERIES)
        .group_by(UserLibrary.media_item_id)
        .subquery()
    )
    highest_count = db.query(
        func.coalesce(func.max(existing_popularity.c.library_count), 0)
    ).scalar()
    extra_users = []
    for _ in range(highest_count + 1):
        credentials = new_credentials()
        extra_users.append(
            User(
                username=credentials["username"],
                email=credentials["email"],
                hashed_password="test-only",
            )
        )
    db.add_all(extra_users)
    db.flush()
    db.add_all(
        UserLibrary(user_id=user.id, media_item_id=candidate["id"])
        for user in extra_users
    )
    db.commit()

    original_query = recommendations_service.Session.query

    def query_with_vector_failure(session, *entities, **kwargs):
        query = original_query(session, *entities, **kwargs)
        if any(
            getattr(entity, "key", None) == "embedding"
            for entity in entities
        ):
            raise RuntimeError("simulated vector query failure")
        return query

    monkeypatch.setattr(
        recommendations_service.Session,
        "query",
        query_with_vector_failure,
    )

    response = client.get(
        "/recommendations", params={"target": "SERIES"}, headers=auth_headers
    )

    assert response.status_code == 200
    recommendations = response.json()
    assert isinstance(recommendations, list)
    assert any(item["id"] == candidate["id"] for item in recommendations)


# ---------------------------------------------------------------- US-14
@pytest.fixture
def local_classifier(monkeypatch):
    """No OpenAI key: the local patterns decide."""
    from app.core import config

    monkeypatch.setattr(config, "OPENAI_API_KEY", "")


def test_us14_spoiler_detected(client, auth_headers, library_entry, local_classifier):
    """US-14: a review revealing a major plot event is flagged as a spoiler."""
    text = (
        "In the final chapter the main character dies and it turns out "
        "the narrator was the killer all along."
    )

    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": text},
        headers=auth_headers,
    )

    assert response.status_code in (200, 201)
    assert response.json()["contains_spoiler"] is True


def test_us14_non_spoiler_review_not_flagged(
    client, auth_headers, library_entry, local_classifier
):
    """US-14: a review without plot details is not flagged."""
    text = "Great atmosphere and a wonderful soundtrack. Highly recommended."

    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": text},
        headers=auth_headers,
    )

    assert response.status_code in (200, 201)
    assert response.json()["contains_spoiler"] is False
def test_us14_new_review_returns_201(client, auth_headers, library_entry):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "A great story with wonderful characters."},
        headers=auth_headers,
    )
    assert response.status_code == 201


def test_us14_updating_review_returns_200(client, auth_headers, library_entry):
    url = f"/library/{library_entry['id']}/review"

    first = client.post(
        url,
        json={"text": "A great story."},
        headers=auth_headers,
    )
    assert first.status_code == 201

    second = client.post(
        url,
        json={"text": "An even better story."},
        headers=auth_headers,
    )
    assert second.status_code == 200
    assert second.json()["text"] == "An even better story."
def test_us14_get_review_returns_404_when_missing(client, auth_headers, library_entry):
    response = client.get(
        f"/library/{library_entry['id']}/review",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_us14_get_review_returns_200_when_exists(client, auth_headers, library_entry):
    url = f"/library/{library_entry['id']}/review"
    client.post(
        url,
        json={"text": "A great story."},
        headers=auth_headers,
    )

    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["text"] == "A great story."
def test_us14_review_creates_review_posted_diary_event(
    client, auth_headers, library_entry, media_item
):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "A great story with wonderful characters."},
        headers=auth_headers,
    )
    assert response.status_code == 201

    events = client.get("/diary", headers=auth_headers).json()
    review_events = [event for event in events if event["action"] == "REVIEW_POSTED"]

    assert len(review_events) == 1
    assert review_events[0]["media_item_id"] == media_item["id"]
def test_us14_review_is_deleted_when_library_entry_is_deleted(
    client, auth_headers, library_entry, db
):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "A great story."},
        headers=auth_headers,
    )
    assert response.status_code == 201

    review = db.query(Review).filter(
        Review.library_entry_id == library_entry["id"]
    ).one()
    review_id = review.id

    delete_response = client.delete(
        f"/library/{library_entry['id']}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    db.expire_all()
    assert db.query(Review).filter(Review.id == review_id).first() is None
def test_us14_blank_review_returns_422(client, auth_headers, library_entry):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "   "},
        headers=auth_headers,
    )
    assert response.status_code == 422
def test_us14_review_over_5000_characters_returns_422(
    client, auth_headers, library_entry
):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "a" * 5001},
        headers=auth_headers,
    )
    assert response.status_code == 422
def test_us14_other_user_cannot_post_review(
    client, auth_headers, library_entry
):
    from helpers import new_credentials, register_and_login

    other_headers = register_and_login(client, new_credentials())

    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "This is someone else's library entry."},
        headers=other_headers,
    )

    assert response.status_code == 404
def test_us14_unauthenticated_post_review_returns_401(client, library_entry):
    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": "A review without authentication."},
    )

    assert response.status_code == 401


# ---------------------------------------------------------------- US-14: save first, check later
SPOILER_TEXT = "In the final chapter the main character dies."


def _post_review(client, headers, entry, text=SPOILER_TEXT):
    return client.post(
        f"/library/{entry['id']}/review", json={"text": text}, headers=headers
    )


def _break_openai(monkeypatch):
    """OpenAI is configured, but every call fails (NFR-04)."""
    import httpx
    from openai import APIConnectionError
    from types import SimpleNamespace

    from app.core import config
    from app.integrations import openai_client

    def broken(*args, **kwargs):
        raise APIConnectionError(
            request=httpx.Request("POST", "https://api.openai.com/v1/test")
        )

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        openai_client,
        "_client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=broken))),
    )


def test_us14_failing_openai_saves_review_with_null_spoiler_fields(
    client, auth_headers, library_entry, db, monkeypatch
):
    """The review is saved and answered with 201. The three spoiler fields stay NULL."""
    _break_openai(monkeypatch)

    response = _post_review(client, auth_headers, library_entry)

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == SPOILER_TEXT
    assert body["contains_spoiler"] is None
    assert body["spoiler_score"] is None
    assert body["spoiler_model_version"] is None

    review = db.query(Review).filter(Review.library_entry_id == library_entry["id"]).one()
    assert review.text == SPOILER_TEXT
    assert review.contains_spoiler is None
    assert review.spoiler_score is None
    assert review.spoiler_model_version is None


def test_us14_failing_openai_on_update_resets_old_result(
    client, auth_headers, library_entry, monkeypatch
):
    """A new text must not keep the result of the old text."""
    from app.core import config

    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    first = _post_review(client, auth_headers, library_entry)
    assert first.json()["contains_spoiler"] is True

    _break_openai(monkeypatch)
    second = _post_review(client, auth_headers, library_entry, text="Edited, now unchecked.")

    assert second.status_code == 200
    assert second.json()["text"] == "Edited, now unchecked."
    assert second.json()["contains_spoiler"] is None
    assert second.json()["spoiler_score"] is None
    assert second.json()["spoiler_model_version"] is None


def test_us14_no_connection_is_checked_out_during_the_openai_call(
    client, auth_headers, library_entry, monkeypatch
):
    """The spoiler check runs after the answer and without an open transaction (#382).

    The fake OpenAI waits until the answer is back. Then no pool connection may be held: the
    request has ended, and the background job opens its transaction only after the call.
    """
    import threading
    from types import SimpleNamespace

    from app.core import background, config
    from app.core.database import engine
    from app.integrations import openai_client
    from tests.requirements.fake_openai import FakeOpenAI

    fake = FakeOpenAI()
    answered = threading.Event()
    checked_out = []

    def create(**kwargs):
        assert answered.wait(timeout=10), "the request waited for OpenAI"
        checked_out.append(engine.pool.checkedout())
        return fake._create_completion(**kwargs)

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        openai_client,
        "_client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )

    response = _post_review(client, auth_headers, library_entry)
    answered.set()

    assert response.status_code == 201
    assert response.json()["contains_spoiler"] is None, "the answer must not wait for the check"
    assert background.wait_idle(timeout=10)
    assert checked_out == [0], "a database connection was held during the OpenAI call"

    review = client.get(f"/library/{library_entry['id']}/review", headers=auth_headers).json()
    assert review["contains_spoiler"] is True
    assert review["spoiler_model_version"] == config.SPOILER_MODEL


def test_us14_local_classifier_uses_the_threshold_setting(
    client, auth_headers, library_entry, local_classifier, monkeypatch
):
    """The local patterns read config.SPOILER_THRESHOLD, not a constant of the service."""
    from app.core import config
    from app.services import review_service

    assert not hasattr(review_service, "SPOILER_THRESHOLD")

    # "dies" alone scores 0.55
    text = "The hero dies."
    monkeypatch.setattr(config, "SPOILER_THRESHOLD", 0.5)
    assert _post_review(client, auth_headers, library_entry, text).json()["contains_spoiler"] is True

    monkeypatch.setattr(config, "SPOILER_THRESHOLD", 0.9)
    response = _post_review(client, auth_headers, library_entry, text)
    assert response.json()["contains_spoiler"] is False
    assert response.json()["spoiler_score"] == 0.55
    assert response.json()["spoiler_model_version"] == "omnilog-nlp-spoiler-v1"


# Additional US-13 endpoint validation tests
def test_us13_recommendations_requires_authentication(client):
    response = client.get("/recommendations", params={"target": "SERIES"})
    assert response.status_code == 401


def test_us13_recommendations_requires_target(client, auth_headers):
    response = client.get("/recommendations", headers=auth_headers)
    assert response.status_code == 422


def test_us13_recommendations_rejects_invalid_target(client, auth_headers):
    response = client.get(
        "/recommendations",
        params={"target": "INVALID"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_us13_recommendations_accepts_max_limit(client, auth_headers):
    response = client.get(
        "/recommendations",
        params={"target": "SERIES", "limit": 50},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.parametrize("limit", [0, 51])
def test_us13_recommendations_rejects_out_of_range_limit(
    client, auth_headers, limit
):
    response = client.get(
        "/recommendations",
        params={"target": "SERIES", "limit": limit},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_us13_ranks_candidates_by_the_current_users_taste_only(
    client, auth_headers, db
):
    """Known vectors rank the closest unowned candidate; another user's taste is ignored."""
    from app.core import config
    from app.models.entities import MediaEmbedding
    from helpers import new_credentials, register_and_login

    own_source = create_media(client, auth_headers, media_type="GAME")
    closest = create_media(client, auth_headers, media_type="SERIES")
    distant = create_media(client, auth_headers, media_type="SERIES")
    owned_series = create_media(client, auth_headers, media_type="SERIES")
    add_to_library(client, auth_headers, own_source["id"], status="COMPLETED")
    add_to_library(client, auth_headers, owned_series["id"], rating=10)

    other_headers = register_and_login(client, new_credentials())
    other_sources = [
        create_media(client, other_headers, media_type="MOVIE") for _ in range(4)
    ]
    for source in other_sources:
        add_to_library(client, other_headers, source["id"], rating=10)

    vector = lambda x, y: [float(x), float(y)] + [0.0] * 1534
    for item_id, embedding in (
        (own_source["id"], vector(1, 0)),
        (closest["id"], vector(1, 0.1)),
        (distant["id"], vector(0, 1)),
        (owned_series["id"], vector(1, 0)),
        *((source["id"], vector(0, 1)) for source in other_sources),
    ):
        db.add(
            MediaEmbedding(
                media_item_id=item_id,
                model_name=config.EMBEDDING_MODEL,
                embedding=embedding,
                dimension=1536,
                source_text_hash="test",
            )
        )
    db.commit()

    response = client.get(
        "/recommendations", params={"target": "SERIES", "limit": 10}, headers=auth_headers
    )
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids.index(closest["id"]) < ids.index(distant["id"])
    assert owned_series["id"] not in ids


def test_us13_large_catalog_has_bounded_queries_and_response(
    client, auth_headers, db
):
    """A 5,000-title catalog still returns a small page without per-title queries."""
    from sqlalchemy import event
    from app.models.entities import MediaItem, MediaType

    db.add_all(
        MediaItem(title=f"Catalog item {index}", media_type=MediaType.SERIES)
        for index in range(5000)
    )
    db.commit()

    statements = []
    from app.core.database import engine

    def count_select(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", count_select)
    try:
        response = client.get(
            "/recommendations", params={"target": "SERIES", "limit": 10}, headers=auth_headers
        )
    finally:
        event.remove(engine, "before_cursor_execute", count_select)

    assert response.status_code == 200
    assert len(response.json()) == 10
    assert len(response.content) < 20_000
    assert len(statements) <= 5
