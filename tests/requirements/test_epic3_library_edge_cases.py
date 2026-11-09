"""Edge cases for the catalog entries and the library (US-04, US-05).

These cover behaviour the user stories imply but do not list one by one:
ownership, partial updates, null handling and invalid ratings.
"""

from sqlalchemy import event

from app.core.database import engine
from helpers import add_to_library, create_media, new_credentials, register_and_login


# ---------------------------------------------------------------- catalog entries
def test_media_creation_requires_authentication(client):
    """Catalog: POST /media without a token returns 401."""
    response = client.post("/media", json={"title": "x", "media_type": "GAME"})

    assert response.status_code == 401


def test_media_creation_rejects_empty_title(client, auth_headers):
    """Catalog: a title cannot be empty, so the request returns 422."""
    response = client.post(
        "/media",
        json={"title": "", "media_type": "GAME"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_add_unknown_media_item_returns_404(client, auth_headers):
    """US-04: adding a title that does not exist returns 404."""
    response = client.post(
        "/library",
        json={"media_item_id": 99999999, "status": "PLAN_TO_WATCH"},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------- ownership
def test_library_lists_only_my_entries(client, auth_headers, media_item):
    """US-04: GET /library never shows another user's entries."""
    other_headers = register_and_login(client, new_credentials())
    other_media = create_media(client, other_headers)
    other_entry = add_to_library(client, other_headers, other_media["id"])

    my_entries = client.get("/library", headers=auth_headers).json()

    assert other_entry["id"] not in [entry["id"] for entry in my_entries]


def test_update_other_users_entry_returns_404(client, auth_headers, library_entry):
    """US-05: PATCH on another user's entry returns 404 and changes nothing."""
    other_headers = register_and_login(client, new_credentials())

    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 1, "status": "DROPPED"},
        headers=other_headers,
    )

    assert response.status_code == 404

    my_entries = client.get("/library", headers=auth_headers).json()
    mine = next(entry for entry in my_entries if entry["id"] == library_entry["id"])

    assert mine["rating"] == library_entry["rating"]
    assert mine["status"] == library_entry["status"]


def test_listing_does_not_run_one_query_per_entry(client):
    """NFR: GET /library loads the media details in one query (joinedload), not N+1."""
    headers = register_and_login(client, new_credentials())

    def count_queries() -> int:
        statements = []

        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", record)
        try:
            response = client.get("/library", headers=headers)
        finally:
            event.remove(engine, "before_cursor_execute", record)

        assert response.status_code == 200
        return len(statements)

    add_to_library(client, headers, create_media(client, headers)["id"])
    queries_with_one_entry = count_queries()

    for _ in range(4):
        add_to_library(client, headers, create_media(client, headers)["id"])

    queries_with_five_entries = count_queries()

    assert queries_with_five_entries == queries_with_one_entry


def test_library_entry_contains_the_media_details(
    client,
    auth_headers,
    library_entry,
    media_item,
):
    """US-04: each entry includes the title it refers to, so the library can show it."""
    entries = client.get("/library", headers=auth_headers).json()
    entry = next(e for e in entries if e["id"] == library_entry["id"])

    assert entry["media_item"]["title"] == media_item["title"]


def test_library_requires_authentication(client):
    """US-04: GET /library without a token returns 401."""
    response = client.get("/library")

    assert response.status_code == 401


def test_update_requires_authentication(client, library_entry):
    """US-05: PATCH without a token returns 401."""
    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 5},
    )

    assert response.status_code == 401


def test_update_unknown_entry_returns_404(client, auth_headers):
    """US-05: an entry id that does not exist returns 404."""
    response = client.patch(
        "/library/99999999",
        json={"rating": 5},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------- partial updates and nulls
def test_empty_update_changes_nothing(client, auth_headers, library_entry):
    """US-05: a PATCH with an empty body returns the entry unchanged."""
    response = client.patch(
        f"/library/{library_entry['id']}",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == library_entry["status"]
    assert response.json()["rating"] == library_entry["rating"]


def test_null_status_is_rejected(client, auth_headers, library_entry):
    """US-05: status cannot be cleared, so an explicit null returns 422."""
    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"status": None},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_null_rating_clears_the_rating(client, auth_headers, library_entry):
    """US-05: an explicit null rating removes the rating."""
    client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 7},
        headers=auth_headers,
    )

    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": None},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["rating"] is None


def test_rating_boundaries_1_and_10_are_accepted(
    client,
    auth_headers,
    library_entry,
):
    """US-05: 1 and 10 are the lowest and highest valid ratings."""
    for rating in (1, 10):
        response = client.patch(
            f"/library/{library_entry['id']}",
            json={"rating": rating},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["rating"] == rating


def test_fractional_rating_is_rejected_on_update(
    client,
    auth_headers,
    library_entry,
):
    """US-05 / BR-04: fractional ratings are not accepted when updating."""
    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 7.5},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_fractional_rating_is_rejected_on_add(
    client,
    auth_headers,
    media_item,
):
    """US-04 / BR-04: fractional ratings are not accepted when adding."""
    response = client.post(
        "/library",
        json={
            "media_item_id": media_item["id"],
            "rating": 7.5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_nan_rating_is_rejected(client, auth_headers, library_entry):
    """US-05: NaN is not a number on the 1 to 10 scale, so it returns 422."""
    # httpx refuses to encode NaN as JSON, so send the raw token that a client could send
    response = client.patch(
        f"/library/{library_entry['id']}",
        content=b'{"rating": NaN}',
        headers={
            **auth_headers,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 422


def test_get_media_returns_the_item(client, auth_headers, media_item):
    """US-09 groundwork: GET /media/{id} returns the stored title."""
    response = client.get(f"/media/{media_item['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == media_item["id"]
    assert response.json()["title"] == media_item["title"]


def test_get_unknown_media_returns_404(client):
    """US-09 groundwork: an unknown media id returns 404."""
    assert client.get("/media/99999999").status_code == 404


def test_us05_rejected_rating_leaves_the_entry_unchanged(
    client,
    auth_headers,
    library_entry,
):
    """US-05: invalid ratings return 422 and the entry remains unchanged."""
    url = f"/library/{library_entry['id']}"

    assert client.patch(
        url,
        json={"rating": 8},
        headers=auth_headers,
    ).status_code == 200

    for body in (
        {"rating": 0},
        {"rating": 11},
        {"rating": 11, "status": "DROPPED"},
    ):
        assert client.patch(
            url,
            json=body,
            headers=auth_headers,
        ).status_code == 422

    entry = next(
        entry
        for entry in client.get(
            "/library",
            headers=auth_headers,
        ).json()
        if entry["id"] == library_entry["id"]
    )

    assert entry["rating"] == 8
    assert entry["status"] == library_entry["status"]


def test_us05_rating_must_be_a_json_number(
    client,
    auth_headers,
    library_entry,
):
    """US-05 / BR-04: booleans and numeric strings are not ratings."""
    url = f"/library/{library_entry['id']}"

    for bad in (True, False, "9"):
        response = client.patch(
            url,
            json={"rating": bad},
            headers=auth_headers,
        )

        assert response.status_code == 422


def test_us04_rating_on_add_must_be_a_json_number(
    client,
    auth_headers,
    media_item,
):
    """US-04 / BR-04: booleans are not ratings when adding a title."""
    response = client.post(
        "/library",
        json={
            "media_item_id": media_item["id"],
            "rating": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
