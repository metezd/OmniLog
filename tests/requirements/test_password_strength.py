"""Registration refuses weak passwords (US-02, BR-20, #384).

Refused with 422 and a message on the password field: a common password (also with digits or
symbols at the end), a password with the username or the part of the email before the @, one
character repeated, and a simple sequence or keyboard row. A good password still gives 201, and
accounts that already exist can still log in with their old password.
"""
import pytest

from app.core import passwords
from app.core.security import hash_password
from app.models.entities import User
from helpers import unique


def register(client, password, name=None):
    name = name or unique("pw")
    return client.post(
        "/auth/register",
        json={"username": name, "email": f"{name}@example.com", "password": password},
    )


def password_error(response):
    assert response.status_code == 422, response.text
    errors = [e for e in response.json()["detail"] if e["loc"][-1] == "password"]
    assert len(errors) == 1, response.json()
    return errors[0]["msg"].removeprefix("Value error, ")


# ---------------------------------------------------------------- the cases of the issue
@pytest.mark.parametrize(
    ("password", "reason"),
    [
        ("12345678", passwords.SEQUENCE),
        ("password", passwords.TOO_COMMON),
        ("aaaaaaaa", passwords.ONE_CHARACTER),
        ("qwertyui", passwords.SEQUENCE),
    ],
)
def test_the_passwords_of_the_issue_are_refused(client, password, reason):
    assert password_error(register(client, password)) == reason


def test_the_username_followed_by_99_is_refused(client):
    name = unique("pw")

    response = register(client, f"{name}99", name=name)

    assert password_error(response) == passwords.HAS_USERNAME


# ---------------------------------------------------------------- common passwords
@pytest.mark.parametrize("password", ["Password", "PASSWORD1!", "monkey123", "Passw0rd!", "iloveyou2026", "letmein!!"])
def test_a_common_password_is_refused_in_any_case_and_with_an_ending(client, password):
    assert password_error(register(client, password)) == passwords.TOO_COMMON


def test_the_list_is_read_from_the_file_in_lower_case():
    common = passwords.common_passwords()

    assert {"password", "qwerty", "iloveyou"} <= common
    assert all(entry == entry.casefold() and not entry.startswith("#") for entry in common)


# ---------------------------------------------------------------- the name of the user
def test_a_password_with_the_username_inside_is_refused_in_any_case(client):
    name = unique("pw")

    response = register(client, f"My-{name.upper()}-key", name=name)

    assert password_error(response) == passwords.HAS_USERNAME


def test_a_password_with_the_name_of_the_email_is_refused(client):
    name = unique("pw")
    response = client.post(
        "/auth/register",
        json={"username": name, "email": "sunflower.k@example.com", "password": "Sunflower.K-2026"},
    )

    assert password_error(response) == passwords.HAS_EMAIL_NAME


def test_a_very_short_email_name_is_not_compared():
    assert passwords.weakness("Ab-Strong-Key-9", username=None, email="ab@example.com") is None


# ---------------------------------------------------------------- sequences and repeats
@pytest.mark.parametrize("password", ["87654321", "abcdefgh", "HGFEDCBA", "asdfghjk", "poiuytre", "1234567890"])
def test_a_sequence_or_a_keyboard_row_is_refused(client, password):
    assert password_error(register(client, password)) == passwords.SEQUENCE


@pytest.mark.parametrize("password", ["11111111", "ZZZZZZZZZZ"])
def test_one_repeated_character_is_refused(client, password):
    assert password_error(register(client, password)) == passwords.ONE_CHARACTER


# ---------------------------------------------------------------- good passwords
@pytest.mark.parametrize("password", ["StrongPass123!", "correct horse battery", "Dragon-Fly-2026!", "Ünïcode-Paßwort-9"])
def test_a_good_password_is_accepted(client, password):
    assert register(client, password).status_code == 201


def test_the_other_rules_of_the_password_come_first(client):
    # Too short is still the message of a short password, not of a common one
    response = register(client, "pass")

    assert response.status_code == 422
    assert "at least 8" in response.json()["detail"][0]["msg"]


def test_the_rule_does_not_repeat_the_refused_password(client):
    response = register(client, "monkey123")

    assert "monkey123" not in response.text


# ---------------------------------------------------------------- existing accounts
def test_an_existing_account_with_a_weak_password_can_still_log_in(client, db):
    name = unique("old")
    db.add(User(username=name, email=f"{name}@example.com", hashed_password=hash_password("password")))
    db.commit()

    response = client.post("/auth/login", json={"username": name, "password": "password"})

    assert response.status_code == 200
