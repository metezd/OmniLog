"""A user can change the password, log out on all devices and delete the account (US-02, US-03,
NFR-02, #426).

Before, the backend had only register, login, logout and /auth/me: a leaked password could not be
changed, a stolen token on another device stayed valid for 90 minutes, and only an operator could
delete the data of a user.
"""
import jwt
import pytest

from app.core import config
from app.core.security import JWT_ALGORITHM
from app.models.entities import CustomList, DiaryEntry, User, UserLibrary
from helpers import add_to_library, create_media, new_credentials

NEW_PASSWORD = "Fresh-Harbor-2026!"


def register(client, credentials=None):
    credentials = credentials or new_credentials()
    assert client.post("/auth/register", json=credentials).status_code == 201
    return credentials


def login(client, credentials, password=None):
    response = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": password or credentials["password"]},
    )
    return response


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def session(client, credentials):
    response = login(client, credentials)
    assert response.status_code == 200, response.text
    return bearer(response.json()["access_token"])


# ---------------------------------------------------------------- change the password
def test_a_new_password_works_and_the_old_one_does_not(client):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.put(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": NEW_PASSWORD},
        headers=headers,
    )

    assert response.status_code == 200
    assert client.get("/auth/me", headers=bearer(response.json()["access_token"])).status_code == 200
    assert login(client, credentials).status_code == 401
    assert login(client, credentials, NEW_PASSWORD).status_code == 200


def test_a_new_password_ends_every_other_session(client):
    credentials = register(client)
    laptop = session(client, credentials)
    phone = session(client, credentials)

    client.put(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": NEW_PASSWORD},
        headers=laptop,
    )

    assert client.get("/auth/me", headers=phone).status_code == 401
    assert client.get("/auth/me", headers=laptop).status_code == 401  # the answer has a new token


def test_a_wrong_current_password_is_403_and_changes_nothing(client):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.put(
        "/auth/password",
        json={"current_password": "Not-The-Password1!", "new_password": NEW_PASSWORD},
        headers=headers,
    )

    assert response.status_code == 403
    assert client.get("/auth/me", headers=headers).status_code == 200
    assert login(client, credentials).status_code == 200


@pytest.mark.parametrize("new_password", ["password", "12345678", "short"])
def test_a_weak_new_password_is_422(client, new_password):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.put(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": new_password},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "new_password"


def test_the_new_password_must_not_hold_the_username(client):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.put(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": f"{credentials['username']}-Key-9"},
        headers=headers,
    )

    assert response.status_code == 422
    assert "username" in response.json()["detail"][0]["msg"]


def test_the_new_password_must_differ_from_the_current_one(client):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.put(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": credentials["password"]},
        headers=headers,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- log out on all devices
def test_logout_all_ends_every_session_and_a_new_login_works(client):
    credentials = register(client)
    laptop = session(client, credentials)
    phone = session(client, credentials)

    assert client.post("/auth/logout-all", headers=laptop).status_code == 204

    assert client.get("/auth/me", headers=laptop).status_code == 401
    assert client.get("/auth/me", headers=phone).status_code == 401
    assert client.get("/auth/me", headers=session(client, credentials)).status_code == 200


def test_logout_all_of_one_user_does_not_touch_another(client):
    first, second = register(client), register(client)
    other = session(client, second)

    client.post("/auth/logout-all", headers=session(client, first))

    assert client.get("/auth/me", headers=other).status_code == 200


def test_a_token_from_before_this_change_has_version_0(client):
    """Tokens without the claim "ver" keep working until the first logout-all."""
    credentials = register(client)
    claims = jwt.decode(login(client, credentials).json()["access_token"], options={"verify_signature": False})
    del claims["ver"]
    old_style = bearer(jwt.encode(claims, config.SECRET_KEY, algorithm=JWT_ALGORITHM))

    assert client.get("/auth/me", headers=old_style).status_code == 200
    client.post("/auth/logout-all", headers=old_style)
    assert client.get("/auth/me", headers=old_style).status_code == 401


@pytest.mark.parametrize("version", [-1, "1", True])
def test_a_token_with_a_wrong_version_claim_is_refused(client, version):
    credentials = register(client)
    claims = jwt.decode(login(client, credentials).json()["access_token"], options={"verify_signature": False})
    forged = bearer(jwt.encode(claims | {"ver": version}, config.SECRET_KEY, algorithm=JWT_ALGORITHM))

    assert client.get("/auth/me", headers=forged).status_code == 401


# ---------------------------------------------------------------- delete the account
def test_delete_account_removes_the_user_and_the_data(client, db):
    credentials = register(client)
    headers = session(client, credentials)
    user_id = client.get("/auth/me", headers=headers).json()["id"]
    media = create_media(client, headers)
    add_to_library(client, headers, media["id"])
    client.post("/lists", json={"name": "to go"}, headers=headers)

    response = client.request("DELETE", "/auth/me", json={"password": credentials["password"]}, headers=headers)

    assert response.status_code == 204
    db.expire_all()
    assert db.get(User, user_id) is None
    for model in (UserLibrary, CustomList, DiaryEntry):
        assert db.query(model).filter(model.user_id == user_id).count() == 0
    assert login(client, credentials).status_code == 401
    assert client.get(f"/media/{media['id']}", headers=session(client, register(client))).status_code == 200


def test_delete_account_with_a_wrong_password_is_403(client, db):
    credentials = register(client)
    headers = session(client, credentials)

    response = client.request("DELETE", "/auth/me", json={"password": "Not-The-Password1!"}, headers=headers)

    assert response.status_code == 403
    assert client.get("/auth/me", headers=headers).status_code == 200


# ---------------------------------------------------------------- access
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("PUT", "/auth/password", {"current_password": "x", "new_password": NEW_PASSWORD}),
        ("POST", "/auth/logout-all", None),
        ("DELETE", "/auth/me", {"password": "x"}),
    ],
)
def test_every_account_route_needs_a_login(client, method, path, body):
    assert client.request(method, path, json=body).status_code == 401
