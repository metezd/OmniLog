"""Epic 4 - Granular Episodic and Decision Logging (US-10 to US-12)."""
import pytest

from app.models.entities import Chapter, ChapterKind
from epic4_helpers import add_decision_point
from helpers import add_to_library, create_media


@pytest.fixture
def chapter_context(client, auth_headers, db):
    """A library entry for an episodic game plus the id of its first chapter.

    No endpoint creates the chapters of a game or their decision points yet (open point 3 in
    docs/analysis/data/domain-model.md), so the chapter and one decision point with the options
    A and B are saved in the database directly.
    The Epic 3 edge case tests do the same. The chapter is then read from GET /catalog/{id},
    as a client would do.
    """
    media = create_media(client, auth_headers, media_type="GAME")
    entry = add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")

    chapter = Chapter(media_item_id=media["id"], number=1, kind=ChapterKind.CHAPTER, title="Chapter 1")
    db.add(chapter)
    db.commit()
    add_decision_point(db, chapter.id, media["id"])

    detail = client.get(f"/catalog/{media['id']}", headers=auth_headers)
    assert detail.status_code == 200, f"catalog detail failed: {detail.status_code}"
    chapters = detail.json().get("chapters") or []
    assert chapters, "the title has no chapters"

    base = f"/library/{entry['id']}/chapters/{chapters[0]['id']}"
    return {"base": base, "headers": auth_headers}


# ---------------------------------------------------------------- US-10
def test_us10_rate_chapter(client, chapter_context):
    """US-10: a chapter can be rated 1 to 5 stars."""
    response = client.put(
        f"{chapter_context['base']}/rating",
        json={"rating": 4},
        headers=chapter_context["headers"],
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 4


def test_us10_chapter_rating_out_of_range_rejected(client, chapter_context):
    """US-10: ratings of 0 and 6 return 422."""
    for bad_rating in (0, 6):
        response = client.put(
            f"{chapter_context['base']}/rating",
            json={"rating": bad_rating},
            headers=chapter_context["headers"],
        )
        assert response.status_code == 422


# ---------------------------------------------------------------- US-11
def test_us11_log_playtime(client, chapter_context):
    """US-11: playtime entries of 90 and 30 minutes add up to 120."""
    headers = chapter_context["headers"]
    for minutes in (90, 30):
        response = client.post(
            f"{chapter_context['base']}/playtime",
            json={"minutes": minutes},
            headers=headers,
        )
        assert response.status_code in (200, 201)

    chapter = client.get(chapter_context["base"], headers=headers)
    assert chapter.status_code == 200
    assert chapter.json()["playtime_minutes"] == 120


def test_us11_negative_playtime_rejected(client, chapter_context):
    """US-11: a negative playtime returns 422."""
    response = client.post(
        f"{chapter_context['base']}/playtime",
        json={"minutes": -5},
        headers=chapter_context["headers"],
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- US-12
def test_us12_record_decision(client, chapter_context):
    """US-12: choosing option A at a decision point is stored."""
    response = client.put(
        f"{chapter_context['base']}/decision",
        json={"choice": "A"},
        headers=chapter_context["headers"],
    )

    assert response.status_code == 200
    assert response.json()["choice"] == "A"


def test_us12_invalid_decision_rejected(client, chapter_context):
    """US-12: a choice that is not an allowed option returns 422."""
    response = client.put(
        f"{chapter_context['base']}/decision",
        json={"choice": "Z"},
        headers=chapter_context["headers"],
    )

    assert response.status_code == 422


def test_us12_decision_can_be_changed(client, chapter_context):
    """US-12: recording option B after A keeps only the latest choice."""
    headers = chapter_context["headers"]
    first = client.put(f"{chapter_context['base']}/decision", json={"choice": "A"}, headers=headers)
    assert first.status_code == 200

    second = client.put(f"{chapter_context['base']}/decision", json={"choice": "B"}, headers=headers)
    assert second.status_code == 200

    chapter = client.get(chapter_context["base"], headers=headers)
    assert chapter.json()["choice"] == "B"
