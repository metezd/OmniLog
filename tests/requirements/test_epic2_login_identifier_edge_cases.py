"""Edge cases for login with a username or an email, the @ rule and GET /auth/me
(US-02, US-03, BR-18, NFR-02)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.entities import User
from helpers import new_credentials, unique


# ---------------------------------------------------------------- helpers
def register(client, credentials=None):
    credentials = credentials or new_credentials()
    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 201, response.text
    return credentials


def login(client, identifier, password="StrongPass123!"):
    return client.post("/auth/login", json={"username": identifier, "password": password})


def bearer(response):
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ---------------------------------------------------------------- login with the email
def test_login_with_the_email_returns_a_token(client):
    credentials = register(client)

    response = login(client, credentials["email"])

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_the_token_of_an_email_login_is_the_token_of_the_same_user(client):
    credentials = register(client)

    by_email = client.get("/auth/me", headers=bearer(login(client, credentials["email"])))
    by_name = client.get("/auth/me", headers=bearer(login(client, credentials["username"])))

    assert by_email.json() == by_name.json()


def test_the_email_is_not_case_sensitive_and_spaces_are_ignored(client):
    credentials = register(client)

    for identifier in (credentials["email"].upper(), f"  {credentials['email']}  "):
        assert login(client, identifier).status_code == 200, identifier


def test_a_capital_i_in_the_email_is_not_changed_by_the_turkish_username_rule(client):
    """Usernames use Turkish letter rules (I becomes a dotless i). An email must not, or INFO@...
    would never match info@..."""
    name = unique()
    credentials = register(client, {"username": name, "email": f"info.{name}@example.com", "password": "StrongPass123!"})

    response = login(client, credentials["email"].upper())

    assert response.status_code == 200


def test_login_with_the_username_still_works(client):
    credentials = register(client)

    for identifier in (credentials["username"], credentials["username"].upper()):
        assert login(client, identifier).status_code == 200, identifier


# ---------------------------------------------------------------- wrong data
def test_wrong_password_and_unknown_account_look_the_same(client):
    """No answer shows whether an account exists, for usernames and for emails."""
    credentials = register(client)
    ghost = new_credentials()

    answers = [
        login(client, credentials["username"], "WrongPass123!"),
        login(client, credentials["email"], "WrongPass123!"),
        login(client, ghost["username"]),
        login(client, ghost["email"]),
    ]

    assert [a.status_code for a in answers] == [401, 401, 401, 401]
    assert len({a.text for a in answers}) == 1


def test_the_email_of_another_user_does_not_work_with_my_password(client):
    mine = register(client)
    other = new_credentials()
    other["password"] = "AnotherPass456!"
    register(client, other)

    assert login(client, other["email"], mine["password"]).status_code == 401
    assert login(client, other["email"], other["password"]).status_code == 200


@pytest.mark.parametrize("identifier", ["a@b", "@", "@@", "nobody@", "@example.com"])
def test_values_with_an_at_sign_that_are_not_accounts_return_401(client, identifier):
    assert login(client, identifier).status_code == 401


def test_the_length_of_the_login_value_is_limited_to_the_email_column(client):
    assert login(client, "a" * 100).status_code == 401
    assert login(client, "a" * 101).status_code == 422
    assert login(client, "").status_code == 422
    assert login(client, "   ").status_code == 422


@pytest.mark.parametrize("value", [123, None, ["a@b.com"], {"email": "a@b.com"}, True])
def test_a_login_value_that_is_not_text_returns_422(client, value):
    response = client.post("/auth/login", json={"username": value, "password": "StrongPass123!"})

    assert response.status_code == 422


# ---------------------------------------------------------------- the @ rule (BR-18)
@pytest.mark.parametrize("username", ["ali@x", "@ali", "ali@", "@@@", "ali@example.com"])
def test_a_username_with_an_at_sign_is_rejected(client, username):
    credentials = new_credentials()
    credentials["username"] = username

    response = client.post("/auth/register", json=credentials)

    assert response.status_code == 422
    assert "must not contain @" in response.text
    # nothing was created
    assert login(client, credentials["email"], credentials["password"]).status_code == 401


def test_usernames_with_other_symbols_are_still_allowed(client):
    credentials = new_credentials()
    credentials["username"] = f"ali.veli_{unique()[:6]}-x"

    assert client.post("/auth/register", json=credentials).status_code == 201


def test_the_database_rejects_a_username_with_an_at_sign(client, db):
    """BR-18 is also a check constraint, so no code path can save such a username."""
    db.add(User(username=f"{unique()}@x", email=f"{unique()}@example.com", hashed_password="x"))

    with pytest.raises(IntegrityError) as error:
        db.commit()
    db.rollback()

    assert "chk_username_no_at" in str(error.value)


# ---------------------------------------------------------------- GET /auth/me
def test_me_returns_the_logged_in_user(client):
    credentials = register(client)

    response = client.get("/auth/me", headers=bearer(login(client, credentials["username"])))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "username", "created_at"}
    assert (body["username"], body["email"]) == (credentials["username"], credentials["email"].lower())


def test_me_never_shows_the_password(client):
    credentials = register(client)

    response = client.get("/auth/me", headers=bearer(login(client, credentials["username"])))

    assert "password" not in response.text.lower()


def test_two_users_get_their_own_data(client):
    first, second = register(client), register(client)

    one = client.get("/auth/me", headers=bearer(login(client, first["username"]))).json()
    two = client.get("/auth/me", headers=bearer(login(client, second["username"]))).json()

    assert (one["username"], two["username"]) == (first["username"], second["username"])


def test_me_needs_a_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_the_token_of_a_deleted_user_is_rejected(client, db):
    credentials = register(client)
    headers = bearer(login(client, credentials["username"]))
    assert client.get("/auth/me", headers=headers).status_code == 200

    db.query(User).filter(User.username == credentials["username"]).delete()
    db.commit()

    assert client.get("/auth/me", headers=headers).status_code == 401
