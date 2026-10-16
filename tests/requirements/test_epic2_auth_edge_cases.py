"""Edge cases for registration and login (US-02, US-03).

These guard against inputs the user stories do not list explicitly but that
used to cause server errors (500): NUL bytes, the bcrypt 72-byte limit, and
the Turkish case rules for usernames.
"""
from helpers import HiddenPreCheck, new_credentials


def _suffix() -> str:
    """A unique, lowercase, ASCII-only tail for usernames in these tests."""
    return new_credentials()["username"].removeprefix("user_")


# ---------------------------------------------------------------- US-02: password and NUL checks
def test_us02_nul_byte_in_password_rejected(client):
    """US-02: a password containing a NUL byte returns 422, never 500."""
    creds = dict(new_credentials(), password="Strong\x00Pass1")

    response = client.post("/auth/register", json=creds)

    assert response.status_code == 422


def test_us02_nul_byte_in_username_rejected(client):
    """US-02: a username containing a NUL byte returns 422, never 500."""
    creds = dict(new_credentials(), username="bad\x00name")

    response = client.post("/auth/register", json=creds)

    assert response.status_code == 422


def test_us02_password_at_72_byte_limit_accepted(client):
    """US-02: 18 four-byte characters is exactly 72 bytes and is accepted."""
    creds = dict(new_credentials(), password="\U0001F600" * 18)

    response = client.post("/auth/register", json=creds)

    assert response.status_code == 201


def test_us02_password_over_72_bytes_rejected(client):
    """US-02: 19 four-byte characters is 76 bytes and returns 422."""
    creds = dict(new_credentials(), password="\U0001F600" * 19)

    response = client.post("/auth/register", json=creds)

    assert response.status_code == 422


# ---------------------------------------------------------------- US-03: login edge cases
def test_us03_nul_byte_in_password_returns_401(client, credentials):
    """US-03: a password with a NUL byte can never match, so it returns 401, not 500."""
    assert client.post("/auth/register", json=credentials).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": "a\x00b"},
    )

    assert response.status_code == 401


def test_us03_unknown_user_gets_same_response_as_wrong_password(client, credentials):
    """US-03: unknown usernames and wrong passwords return the same body (no user enumeration)."""
    assert client.post("/auth/register", json=credentials).status_code == 201

    unknown = client.post("/auth/login", json={"username": "no_such_user_xyz", "password": "whatever"})
    wrong = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": "wrong-password"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# ---------------------------------------------------------------- usernames: ASCII case
def test_us02_ascii_case_variants_are_the_same_account(client):
    """US-02: "Bob" and "bob" are one account, so the second registration returns 409."""
    name = new_credentials()["username"]
    first = client.post("/auth/register", json=dict(new_credentials(), username=name.upper()))
    assert first.status_code == 201
    assert first.json()["username"] == name

    second = client.post("/auth/register", json=dict(new_credentials(), username=name))

    assert second.status_code == 409


def test_us03_login_ignores_ascii_case(client):
    """US-03: logging in with a different letter case still finds the account."""
    creds = new_credentials()
    assert client.post("/auth/register", json=creds).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": creds["username"].upper(), "password": creds["password"]},
    )

    assert response.status_code == 200


# ---------------------------------------------------------------- usernames: Turkish case rules
def test_us02_dotted_capital_i_is_the_same_as_i(client):
    """US-02: "İ" and "i" are the same letter, so the second registration returns 409."""
    suffix = _suffix()
    first = client.post("/auth/register", json=dict(new_credentials(), username=f"\u0130stan_{suffix}"))
    assert first.status_code == 201
    assert first.json()["username"] == f"istan_{suffix}"

    second = client.post("/auth/register", json=dict(new_credentials(), username=f"istan_{suffix}"))

    assert second.status_code == 409


def test_us02_capital_i_is_the_same_as_dotless_i(client):
    """US-02: "I" and "ı" are the same letter, so the second registration returns 409."""
    suffix = _suffix()
    first = client.post("/auth/register", json=dict(new_credentials(), username=f"Irmak_{suffix}"))
    assert first.status_code == 201

    second = client.post("/auth/register", json=dict(new_credentials(), username=f"\u0131rmak_{suffix}"))

    assert second.status_code == 409


def test_us02_dotted_and_dotless_i_are_different_letters(client):
    """US-02: "i" and "ı" are different letters in Turkish, so both accounts are created."""
    suffix = _suffix()
    dotted = client.post("/auth/register", json=dict(new_credentials(), username=f"ilk_{suffix}"))
    dotless = client.post("/auth/register", json=dict(new_credentials(), username=f"\u0131lk_{suffix}"))

    assert dotted.status_code == 201
    assert dotless.status_code == 201
    assert dotted.json()["id"] != dotless.json()["id"]


def test_us03_login_uses_turkish_case_rules(client):
    """US-03: logging in with "ilkay" finds the account registered as "İlkay"."""
    suffix = _suffix()
    creds = dict(new_credentials(), username=f"\u0130lkay_{suffix}")
    assert client.post("/auth/register", json=creds).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": f"ilkay_{suffix}", "password": creds["password"]},
    )

    assert response.status_code == 200


def test_us02_composed_and_decomposed_text_is_the_same_username(client):
    """US-02: "ş" written as one character or as "s" plus a combining cedilla is the same username."""
    suffix = _suffix()
    composed = client.post("/auth/register", json=dict(new_credentials(), username=f"\u015fen_{suffix}"))
    assert composed.status_code == 201

    decomposed = client.post(
        "/auth/register",
        json=dict(new_credentials(), username=f"s\u0327en_{suffix}"),
    )

    assert decomposed.status_code == 409


def test_us02_username_over_50_characters_after_normalization_rejected(client):
    """US-02: 51 dotted capital I characters normalize to 51 characters, so they return 422."""
    creds = dict(new_credentials(), username="\u0130" * 51)

    response = client.post("/auth/register", json=creds)

    assert response.status_code == 422


# ---------------------------------------------------------------- bcrypt truncation
def test_us03_overlong_login_password_cannot_match_by_truncation(client):
    """US-03: bcrypt ignores bytes after 72, so "a"*72 + "extra" must not log in as "a"*72."""
    creds = dict(new_credentials(), password="a" * 72)
    assert client.post("/auth/register", json=creds).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": creds["username"], "password": "a" * 72 + "extra"},
    )

    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_us03_exact_72_byte_password_still_logs_in(client):
    """US-03: a password of exactly 72 bytes registers and logs in normally."""
    creds = dict(new_credentials(), password="a" * 72)
    assert client.post("/auth/register", json=creds).status_code == 201

    response = client.post("/auth/login", json={"username": creds["username"], "password": creds["password"]})

    assert response.status_code == 200


def test_us03_overlong_password_for_unknown_user_returns_401(client):
    """US-03: an overlong password for a missing user returns 401, not 500."""
    response = client.post("/auth/login", json={"username": "no_such_user_xyz", "password": "b" * 100})

    assert response.status_code == 401


# ---------------------------------------------------------------- tokens: invalid or orphaned
def test_invalid_token_returns_401(client):
    """NFR-02: a token that is not a valid JWT returns 401, not 500."""
    response = client.get("/library", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_token_signed_with_other_key_returns_401(client):
    """NFR-02: a token signed with a different key is rejected."""
    from jose import jwt

    forged = jwt.encode({"sub": "1"}, "x" * 32 + "-attacker-key", algorithm="HS256")
    response = client.get("/library", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_token_with_non_numeric_subject_returns_401(client):
    """NFR-02: a correctly signed token whose subject is not a user id returns 401."""
    from jose import jwt
    from app.core.config import SECRET_KEY

    token = jwt.encode({"sub": "admin"}, SECRET_KEY, algorithm="HS256")
    response = client.get("/library", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_token_for_unknown_user_returns_401(client):
    """NFR-02: a valid token for a user that no longer exists returns 401."""
    from app.core.security import create_access_token

    token = create_access_token(99999999)
    response = client.get("/library", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


# ---------------------------------------------------------------- US-02: registration race
def test_us02_duplicate_registration_race_is_caught_by_the_constraint(client):
    """US-02: when two registrations pass the duplicate check together, the second gets 409."""
    import pytest
    from app.core.database import SessionLocal
    from app.schemas.user import UserCreate
    from app.services import auth_service

    credentials = new_credentials()
    assert client.post("/auth/register", json=credentials).status_code == 201

    db = SessionLocal()
    try:
        with pytest.raises(auth_service.AccountConflictError):
            auth_service.register_user(HiddenPreCheck(db, hide_call=1), UserCreate(**credentials))
    finally:
        db.close()
