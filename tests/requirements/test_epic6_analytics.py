"""Epic 6 - Analytics Dashboard (US-15)."""
from helpers import add_to_library, create_media


def test_us15_personal_statistics(client, auth_headers):
    """US-15: media split and rating distribution reflect my library."""
    # 3 games rated 8, 8, 6 and 1 unrated series -> 75% games, 25% series
    for rating in (8, 8, 6):
        game = create_media(client, auth_headers, media_type="GAME")
        add_to_library(client, auth_headers, game["id"], status="COMPLETED", rating=rating)
    series = create_media(client, auth_headers, media_type="SERIES")
    add_to_library(client, auth_headers, series["id"])

    response = client.get("/stats", headers=auth_headers)

    assert response.status_code == 200
    stats = response.json()
    assert stats["media_split"]["GAME"] == 75
    assert stats["media_split"]["SERIES"] == 25
    assert stats["rating_distribution"]["8"] == 2
    assert stats["rating_distribution"]["6"] == 1


def test_us15_statistics_for_empty_library(client, auth_headers):
    """US-15: an empty library returns zero counts with status 200."""
    response = client.get("/stats", headers=auth_headers)

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_items"] == 0
    assert all(value == 0 for value in stats["media_split"].values())
