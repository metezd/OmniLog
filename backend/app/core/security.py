"""Password hashing and JWT access tokens.

Passwords are hashed with the bcrypt package. Tokens are signed with
SECRET_KEY (HS256) using PyJWT and carry the user id in the `sub` claim.
A token without `exp`, `sub` or `jti` is rejected, so every token runs out and can be ended
by POST /auth/logout, which stores its `jti` until `exp` (#378).
"""
import secrets
from dataclasses import dataclass
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


# The longest jti that is accepted. It is the primary key of revoked_tokens.
JTI_MAX_LENGTH = 64


@dataclass(frozen=True)
class AccessToken:
    """The claims of a valid token that the API uses."""

    user_id: int
    jti: str
    # The token_version of the user when the token was made (#426). Tokens from before have none,
    # which counts as 0.
    version: int
    # UTC without a time zone, like the DateTime columns
    expires_at: datetime


def create_access_token(user_id: int, version: int = 0) -> str:
    """Create a signed JWT for the given user id, with a random id (jti) of its own and the
    token_version of the user (claim "ver", #426)."""
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "jti": secrets.token_urlsafe(16),
        "ver": int(version),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> Optional[AccessToken]:
    """Return the claims of a valid token, or None if it is invalid or expired.

    It does not look at revoked tokens. get_current_user does that with the database.
    """
    try:
        # PyJWT checks exp only when the token has it. Without "require" a token with no exp
        # would be accepted and never run out. A token without jti could not be revoked.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "jti"]},
        )
        jti = payload["jti"]
        if not isinstance(jti, str) or not 0 < len(jti) <= JTI_MAX_LENGTH:
            return None
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc).replace(tzinfo=None)
        version = payload.get("ver", 0)
        if isinstance(version, bool) or not isinstance(version, int) or version < 0:
            return None
        return AccessToken(user_id=int(payload["sub"]), jti=jti, expires_at=expires_at, version=version)
    except (jwt.PyJWTError, KeyError, ValueError, TypeError, OverflowError, OSError):
        return None


def decode_access_token(token: str) -> Optional[int]:
    """Return the user id in a valid token, or None if it is invalid or expired."""
    claims = read_access_token(token)
    return claims.user_id if claims else None
