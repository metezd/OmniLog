"""Epic 5 - AI-Powered Cross-Media Engine and Review Moderation (US-13, US-14)."""
from helpers import add_to_library, create_media, not_built


# ---------------------------------------------------------------- US-13
# @not_built("US-13")
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


# @not_built("US-13")
def test_us13_recommendations_with_empty_library(client, auth_headers):
    """US-13: an empty library still returns 200 and a list."""
    response = client.get(
        "/recommendations", params={"target": "SERIES"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------- US-14
@not_built("US-14")
def test_us14_spoiler_detected(client, auth_headers, library_entry):
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


@not_built("US-14")
def test_us14_non_spoiler_review_not_flagged(client, auth_headers, library_entry):
    """US-14: a review without plot details is not flagged."""
    text = "Great atmosphere and a wonderful soundtrack. Highly recommended."

    response = client.post(
        f"/library/{library_entry['id']}/review",
        json={"text": text},
        headers=auth_headers,
    )

    assert response.status_code in (200, 201)
    assert response.json()["contains_spoiler"] is False
