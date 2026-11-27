"""The strength rules of a new password (BR-20, #384).

Registration refuses a password that an attacker would try first:
- a common password, also with digits or symbols at the end ("monkey123", "Password1!"),
- a password that contains the username or the part of the email before the @,
- one character repeated ("aaaaaaaa"),
- a simple sequence or a keyboard row ("12345678", "abcdefgh", "qwertyui").

The list of common passwords is a small file next to this module, so the check makes no network
call. Only registration uses these rules: existing accounts and the login are not affected.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

_COMMON_FILE = Path(__file__).with_name("common_passwords.txt")

# Rows of the usual keyboards (QWERTY, QWERTZ, AZERTY) and the digit row
_KEYBOARD_ROWS = ("1234567890", "qwertyuiop", "qwertzuiop", "azertyuiop", "asdfghjkl", "yxcvbnm", "zxcvbnm")

# A part of the email shorter than this is not checked, so "ab@x.com" does not refuse every
# password with "ab" in it. Usernames are at least 3 characters long.
_MIN_NAME_LENGTH = 3

TOO_COMMON = "this password is too common, choose one that is harder to guess"
HAS_USERNAME = "the password must not contain your username"
HAS_EMAIL_NAME = "the password must not contain the name of your email address"
ONE_CHARACTER = "the password must not be one character repeated"
SEQUENCE = "the password must not be a simple sequence such as 12345678 or qwertyui"


@lru_cache(maxsize=1)
def common_passwords() -> frozenset[str]:
    lines = _COMMON_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip() and not line.startswith("#"))


def _without_suffix(value: str) -> str:
    """The password without the digits and symbols at its end: "monkey123!" -> "monkey"."""
    end = len(value)
    while end > 0 and not value[end - 1].isalpha():
        end -= 1
    return value[:end]


def _is_sequence(value: str) -> bool:
    """True for "12345678", "abcdefgh", "87654321" and a part of a keyboard row."""
    steps = {ord(b) - ord(a) for a, b in zip(value, value[1:])}
    if steps in ({1}, {-1}):
        return True
    return any(value in row or value in row[::-1] for row in _KEYBOARD_ROWS)


def weakness(password: str, username: Optional[str] = None, email: Optional[str] = None) -> Optional[str]:
    """The reason why the password is refused, or None when it is good enough."""
    lowered = password.casefold()

    if len(set(lowered)) == 1:
        return ONE_CHARACTER
    if _is_sequence(lowered):
        return SEQUENCE

    common = common_passwords()
    if lowered in common or _without_suffix(lowered) in common:
        return TOO_COMMON

    if username and len(username) >= _MIN_NAME_LENGTH and username.casefold() in lowered:
        return HAS_USERNAME
    name = (email or "").partition("@")[0].casefold()
    if len(name) >= _MIN_NAME_LENGTH and name in lowered:
        return HAS_EMAIL_NAME
    return None
