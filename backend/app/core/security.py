"""Password hashing and JWT access tokens.

Passwords are hashed with the bcrypt package. Tokens are signed with
SECRET_KEY (HS256) using PyJWT and carry the user id in the `sub` claim.
A token without `exp` or `sub` is rejected, so every token runs out.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

JWT_ALGORITHM = "HS256"

# bcrypt only uses the first 72 bytes of a password and silently ignores the rest.
# Registration rejects longer passwords, so a longer login password can never match.
BCRYPT_MAX_BYTES = 72

# The cost of a new hash (2 to the power of this number rounds). 12 is the value that passlib
# used, so new hashes cost the same as the old ones. The tests lower it to save time.
BCRYPT_ROUNDS = 12


def _password_bytes(password: str) -> bytes:
    """The password as bcrypt reads it. Raises ValueError for a password bcrypt cannot hash."""
    encoded = password.encode("utf-8")
    if b"\x00" in encoded or len(encoded) > BCRYPT_MAX_BYTES:
        raise ValueError("bcrypt cannot hash a password with NUL bytes or more than 72 bytes")
    return encoded


def hash_password(password: str) -> str:
    """Return a bcrypt hash ($2b$) of a plain text password."""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain text password against a stored hash.

    Hashes made by passlib are standard bcrypt hashes ($2b$, also $2a$ and $2y$), so they verify
    here too. A password that bcrypt cannot hash, or a hash that is not a bcrypt hash, never matches.
    """
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        return False


# A valid hash of a throwaway value. Login checks against it when the username
# does not exist, so unknown and known usernames take about the same time.
DUMMY_HASH = hash_password("dummy-password-for-timing-only")


def create_access_token(user_id: int) -> str:
    """Create a signed JWT for the given user id."""
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "iat": issued_at, "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """Return the user id in a valid token, or None if it is invalid or expired."""
    try:
        # PyJWT checks exp only when the token has it. Without "require" a token with no exp
        # would be accepted and never run out.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
