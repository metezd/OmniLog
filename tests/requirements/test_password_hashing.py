"""Password hashing with the bcrypt package (#222, NFR-03).

passlib was removed. The hashes that it stored are standard bcrypt hashes, so the users who
registered before must still be able to log in.
"""
from pathlib import Path

import bcrypt
import pytest

from app.core import security
from app.models.entities import User
from helpers import unique

# Made with passlib 1.7.4 (CryptContext(schemes=["bcrypt"])) and bcrypt 4.3, the setup before #222.
# The cost is the production cost (12).
PASSLIB_PASSWORD = "Passlib-Era-Password1!"
PASSLIB_HASH = "$2b$12$2yFTghZUBidJ0bUGUAv2MOX1bW2OxfWFMI6QTKqTA9PeyOJvO89xS"
# The same with the older $2a$ prefix and a password with non-ASCII letters
PASSLIB_2A_PASSWORD = "Ünïcode-Paßwort-9"
PASSLIB_2A_HASH = "$2a$12$/kSjyeGcU4NYAjmz6z6TBe9tbPr1auwZJRCHsRvgDUwK2Up0WgCKO"

BACKEND = Path(__file__).resolve().parents[2] / "backend"


# ---------------------------------------------------------------- old hashes
def test_a_hash_made_by_passlib_still_verifies():
    assert security.verify_password(PASSLIB_PASSWORD, PASSLIB_HASH) is True
    assert security.verify_password("Passlib-Era-Password2!", PASSLIB_HASH) is False


def test_a_2a_hash_made_by_passlib_still_verifies():
    assert security.verify_password(PASSLIB_2A_PASSWORD, PASSLIB_2A_HASH) is True
    assert security.verify_password("Unicode-Passwort-9", PASSLIB_2A_HASH) is False


def test_a_user_with_a_passlib_hash_can_log_in(client, db):
    username = unique()
    db.add(User(username=username, email=f"{username}@example.com", hashed_password=PASSLIB_HASH))
    db.commit()

    ok = client.post("/auth/login", json={"username": username, "password": PASSLIB_PASSWORD})
    wrong = client.post("/auth/login", json={"username": username, "password": "Not-The-Password1!"})

    assert ok.status_code == 200, ok.text
    assert wrong.status_code == 401


# ---------------------------------------------------------------- new hashes
def test_a_new_hash_is_a_standard_bcrypt_hash_with_the_configured_cost(monkeypatch):
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 5)

    hashed = security.hash_password("StrongPass123!")

    assert hashed.startswith("$2b$05$") and len(hashed) == 60
    assert bcrypt.checkpw(b"StrongPass123!", hashed.encode())  # any bcrypt library can read it
    assert security.verify_password("StrongPass123!", hashed)
    assert not security.verify_password("StrongPass123?", hashed)


def test_the_production_cost_is_12():
    """The tests lower the cost (conftest.py), so the default is read from the source."""
    source = (BACKEND / "app" / "core" / "security.py").read_text(encoding="utf-8")

    assert "\nBCRYPT_ROUNDS = 12\n" in source


def test_two_hashes_of_one_password_differ():
    """bcrypt adds a new salt to every hash, so the same password gives two different hashes."""
    first = security.hash_password("StrongPass123!")
    second = security.hash_password("StrongPass123!")

    assert first != second
    assert security.verify_password("StrongPass123!", first) and security.verify_password("StrongPass123!", second)


# ---------------------------------------------------------------- the 72 byte and NUL rules
def test_exactly_72_bytes_works_and_73_bytes_is_refused():
    longest = "é" * 36  # 72 bytes in UTF-8
    hashed = security.hash_password(longest)

    assert security.verify_password(longest, hashed)
    with pytest.raises(ValueError):
        security.hash_password(longest + "a")
    # bcrypt reads only 72 bytes. A longer password must not match, although its first 72 bytes do.
    assert security.verify_password(longest + "a", hashed) is False


def test_a_password_with_a_nul_byte_is_refused():
    with pytest.raises(ValueError):
        security.hash_password("Strong\x00Pass123!")
    assert security.verify_password("Strong\x00Pass123!", PASSLIB_HASH) is False


@pytest.mark.parametrize("stored", ["", "not-a-hash", "$2b$12$short", "$argon2id$v=19$m=65536,t=3,p=4$x$y", "hash-ü"])
def test_a_stored_value_that_is_not_a_bcrypt_hash_never_matches(stored):
    assert security.verify_password("StrongPass123!", stored) is False


# ---------------------------------------------------------------- timing
def test_an_unknown_user_is_checked_against_the_dummy_hash(client, monkeypatch):
    """The login of an unknown user runs bcrypt too, so the answer time does not show which users exist."""
    checked = []
    real_verify = security.verify_password

    def spy(password, hashed):
        checked.append(hashed)
        return real_verify(password, hashed)

    import app.services.auth_service as auth_service

    monkeypatch.setattr(auth_service, "verify_password", spy)

    response = client.post("/auth/login", json={"username": unique(), "password": "StrongPass123!"})

    assert response.status_code == 401
    assert checked == [security.DUMMY_HASH]
    assert security.DUMMY_HASH.startswith("$2b$12$")  # made at the production cost, at import


# ---------------------------------------------------------------- dependencies
def test_passlib_is_gone_and_bcrypt_is_not_held_below_5():
    requirements_in = (BACKEND / "requirements.in").read_text(encoding="utf-8").lower()
    lock = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "passlib" not in requirements_in and "passlib" not in lock
    assert "<5" not in requirements_in
    locked_bcrypt = next(line for line in lock.splitlines() if line.startswith("bcrypt=="))
    assert int(locked_bcrypt.split("==")[1].split(".")[0].split()[0]) >= 5


def test_every_package_in_the_lock_has_an_exact_version_and_hashes():
    lines = (BACKEND / "requirements.txt").read_text(encoding="utf-8").splitlines()
    packages = [line for line in lines if line and not line.startswith((" ", "#"))]

    assert packages, "the lock file is empty"
    for line in packages:
        assert "==" in line and line.rstrip().endswith("\\"), f"not pinned with hashes: {line}"
