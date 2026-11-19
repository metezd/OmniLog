"""Edge cases for reviews and recommendations (US-13, US-14, NFR-02).

Added in the testing phase after the coverage run showed that the "not found" paths of the review
endpoints and the genre ranking of the recommendations had no test. A review belongs to a library
entry, so the main risk is one user reading or writing the review of another user.
"""
import pytest

from app.models.entities import Genre, MediaItem
from helpers import add_to_library, create_media, new_credentials, register_and_login

SPOILER_TEXT = "In the final chapter the main character dies and the narrator was the killer."
CALM_TEXT = "Great atmosphere and a wonderful soundtrack."


@pytest.fixture
def other_headers(client):
    """A second user."""
    return register_and_login(client, new_credentials())


def give_genres(db, media_id, names):
    item = db.get(MediaItem, media_id)
    for name in names:
        genre = db.query(Genre).filter(Genre.name == name).one_or_none()
        item.genres.append(genre or Genre(name=name))
    db.commit()


# ---------------------------------------------------------------- US-14: reviews
def test_review_of_an_unknown_entry_answers_404(client, auth_headers):
    """US-14: posting a review for an entry that does not exist returns 404."""
    response = client.post("/library/999999/review", json={"text": CALM_TEXT}, headers=auth_headers)

    assert response.status_code == 404


def test_reading_the_review_of_an_unknown_entry_answers_404(client, auth_headers):
    """US-14: reading a review of an entry that does not exist returns 404."""
    assert client.get("/library/999999/review", headers=auth_headers).status_code == 404


def test_the_review_of_another_users_entry_cannot_be_written(
    client, auth_headers, other_headers, library_entry
):
    """US-14, NFR-02: another user's entry answers 404, so its existence is not revealed."""
    response = client.post(
        f"/library/{library_entry['id']}/review", json={"text": CALM_TEXT}, headers=other_headers
    )

    assert response.status_code == 404
    mine = client.get(f"/library/{library_entry['id']}/review", headers=auth_headers)
    assert mine.status_code == 200
    assert mine.json() is None  # nothing was stored on the entry of the owner


def test_the_review_of_another_users_entry_cannot_be_read(
    client, auth_headers, other_headers, library_entry
):
    """US-14, NFR-02: the owner's review text is not returned to another user."""
    client.post(
        f"/library/{library_entry['id']}/review", json={"text": CALM_TEXT}, headers=auth_headers
    )

    response = client.get(f"/library/{library_entry['id']}/review", headers=other_headers)

    assert response.status_code == 404
    assert CALM_TEXT not in response.text


def test_no_review_yet_answers_200_with_null(client, auth_headers, library_entry):
    """US-14: an entry without a review returns 200 and null, not an error."""
    response = client.get(f"/library/{library_entry['id']}/review", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() is None


def test_a_second_review_replaces_the_first_and_the_flag_follows_the_new_text(
    client, auth_headers, library_entry
):
    """US-14: one review per entry. Posting again replaces the text and recomputes the flag."""
    url = f"/library/{library_entry['id']}/review"
    first = client.post(url, json={"text": SPOILER_TEXT}, headers=auth_headers)
    assert first.json()["contains_spoiler"] is True

    second = client.post(url, json={"text": CALM_TEXT}, headers=auth_headers)

    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]  # same row, not a new one
    assert second.json()["contains_spoiler"] is False
    stored = client.get(url, headers=auth_headers).json()
    assert stored["text"] == CALM_TEXT


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_a_blank_review_is_rejected(client, auth_headers, library_entry, text):
    """US-14: empty or whitespace-only text returns 422."""
    response = client.post(
        f"/library/{library_entry['id']}/review", json={"text": text}, headers=auth_headers
    )

    assert response.status_code == 422


def test_a_review_longer_than_5000_characters_is_rejected(client, auth_headers, library_entry):
    """US-14: the text is limited to 5000 characters."""
    response = client.post(
        f"/library/{library_entry['id']}/review", json={"text": "a" * 5001}, headers=auth_headers
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- US-13: recommendations
def test_recommendations_rank_titles_with_the_liked_genres_first(client, auth_headers, db):
    """US-13: a series that shares a genre with a highly rated game comes before one that does not."""
    game = create_media(client, auth_headers, media_type="GAME")
    give_genres(db, game["id"], ["Adventure"])
    add_to_library(client, auth_headers, game["id"], status="COMPLETED", rating=10)
    unrelated = create_media(client, auth_headers, media_type="SERIES")  # created first
    give_genres(db, unrelated["id"], ["Sports"])
    related = create_media(client, auth_headers, media_type="SERIES")
    give_genres(db, related["id"], ["Adventure"])

    response = client.get("/recommendations", params={"target": "SERIES"}, headers=auth_headers)

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids.index(related["id"]) < ids.index(unrelated["id"])


def test_a_higher_rating_gives_its_genre_more_weight(client, auth_headers, db):
    """US-13: genres of a game rated 10 count more than genres of a game rated 2."""
    loved = create_media(client, auth_headers, media_type="GAME")
    give_genres(db, loved["id"], ["Mystery"])
    add_to_library(client, auth_headers, loved["id"], status="COMPLETED", rating=10)
    disliked = create_media(client, auth_headers, media_type="GAME")
    give_genres(db, disliked["id"], ["Racing"])
    add_to_library(client, auth_headers, disliked["id"], status="DROPPED", rating=2)
    racing = create_media(client, auth_headers, media_type="SERIES")
    give_genres(db, racing["id"], ["Racing"])
    mystery = create_media(client, auth_headers, media_type="SERIES")
    give_genres(db, mystery["id"], ["Mystery"])

    ids = [
        item["id"]
        for item in client.get(
            "/recommendations", params={"target": "SERIES"}, headers=auth_headers
        ).json()
    ]

    assert ids.index(mystery["id"]) < ids.index(racing["id"])


def test_recommendations_never_contain_a_title_of_the_library(client, auth_headers):
    """US-13: owned titles are excluded, whatever their status."""
    owned = create_media(client, auth_headers, media_type="SERIES")
    add_to_library(client, auth_headers, owned["id"], status="DROPPED")

    response = client.get("/recommendations", params={"target": "SERIES"}, headers=auth_headers)

    assert owned["id"] not in [item["id"] for item in response.json()]


def test_an_unknown_target_type_is_rejected(client, auth_headers):
    """US-13: only GAME and SERIES (the media types) are accepted as target."""
    response = client.get("/recommendations", params={"target": "BOOK"}, headers=auth_headers)

    assert response.status_code == 422
