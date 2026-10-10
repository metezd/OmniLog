"""Epic 2 - User Management and Social Journal (US-02 to US-07)."""
from helpers import (
    add_to_library,
    new_credentials,
    register_and_login,
)


# ---------------------------------------------------------------- US-02
def test_us02_register_user(client, credentials):
    """US-02: valid registration returns 201 and never leaks the password."""
    response = client.post("/auth/register", json=credentials)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == credentials["username"]
    assert body["email"] == credentials["email"]
    assert "password" not in body
    assert "hashed_password" not in body


def test_us02_register_duplicate_email_conflict(client, credentials):
    """US-02: registering the same email twice returns 409."""
    first = client.post("/auth/register", json=credentials)
    assert first.status_code == 201

    other = dict(credentials, username=credentials["username"] + "_2")
    second = client.post("/auth/register", json=other)

    assert second.status_code == 409


def test_us02_register_invalid_email_rejected(client, credentials):
    """US-02: an invalid email returns 422."""
    response = client.post("/auth/register", json=dict(credentials, email="not-an-email"))

    assert response.status_code == 422


# ---------------------------------------------------------------- US-03
def test_us03_login_returns_token(client, credentials):
    """US-03: correct credentials return 200 and a JWT access token."""
    assert client.post("/auth/register", json=credentials).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": credentials["password"]},
    )

    assert response.status_code == 200
    assert response.json().get("access_token")


def test_us03_login_wrong_password_rejected(client, credentials):
    """US-03: a wrong password returns 401 and no token."""
    assert client.post("/auth/register", json=credentials).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "access_token" not in response.json()


# ---------------------------------------------------------------- US-04
def test_us04_add_to_library(client, auth_headers, media_item):
    """US-04: adding a title creates an entry that appears in GET /library."""
    response = client.post(
        "/library",
        json={"media_item_id": media_item["id"], "status": "PLAN_TO_WATCH"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    library = client.get("/library", headers=auth_headers)
    assert library.status_code == 200
    ids = [entry["media_item_id"] for entry in library.json()]
    assert media_item["id"] in ids


def test_us04_add_duplicate_entry_conflict(client, auth_headers, media_item):
    """US-04: adding the same title twice returns 409."""
    add_to_library(client, auth_headers, media_item["id"])

    response = client.post(
        "/library",
        json={"media_item_id": media_item["id"], "status": "PLAN_TO_WATCH"},
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_us04_add_to_library_requires_authentication(client):
    """US-04: POST /library without a token returns 401."""
    response = client.post("/library", json={"media_item_id": 1, "status": "PLAN_TO_WATCH"})

    assert response.status_code == 401


# ---------------------------------------------------------------- US-05
def test_us05_rate_and_update_status(client, auth_headers, library_entry):
    """US-05: PATCH updates rating and status of my entry."""
    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 8, "status": "COMPLETED"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 8
    assert body["status"] == "COMPLETED"


def test_us05_rating_out_of_range_rejected(client, auth_headers, library_entry):
    """US-05: ratings below 1 or above 10 return 422."""
    for bad_rating in (0, 11):
        response = client.patch(
            f"/library/{library_entry['id']}",
            json={"rating": bad_rating},
            headers=auth_headers,
        )
        assert response.status_code == 422


def test_us05_cannot_update_other_users_entry(client, library_entry):
    """US-05: another user cannot modify my entry (403 or 404)."""
    other_headers = register_and_login(client, new_credentials())

    response = client.patch(
        f"/library/{library_entry['id']}",
        json={"rating": 1},
        headers=other_headers,
    )

    assert response.status_code in (403, 404)


# ---------------------------------------------------------------- US-06
def test_us06_create_custom_list(client, auth_headers):
    """US-06: POST /lists creates a list (201)."""
    response = client.post("/lists", json={"name": "Best narrative games"}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == "Best narrative games"


def test_us06_add_title_to_list(client, auth_headers, media_item):
    """US-06: a title added to a list appears in that list."""
    created = client.post("/lists", json={"name": "Favourites"}, headers=auth_headers)
    assert created.status_code == 201
    list_id = created.json()["id"]

    added = client.post(
        f"/lists/{list_id}/items",
        json={"media_item_id": media_item["id"]},
        headers=auth_headers,
    )
    assert added.status_code in (200, 201)

    detail = client.get(f"/lists/{list_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert any(item["media_item_id"] == media_item["id"] for item in detail.json()["items"])


def test_us06_empty_list_name_rejected(client, auth_headers):
    """US-06: an empty list name returns 422."""
    response = client.post("/lists", json={"name": ""}, headers=auth_headers)

    assert response.status_code == 422


# ---------------------------------------------------------------- US-07
def test_us07_activity_diary(client, auth_headers, media_item):
    """US-07: adding and rating a title produces two diary events."""
    entry = add_to_library(client, auth_headers, media_item["id"])
    rated = client.patch(f"/library/{entry['id']}", json={"rating": 9}, headers=auth_headers)
    assert rated.status_code == 200

    response = client.get("/diary", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_us07_empty_diary_for_new_user(client, auth_headers):
    """US-07: a user without activity gets an empty list (200)."""
    response = client.get("/diary", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
