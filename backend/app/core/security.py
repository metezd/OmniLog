"""Password hashing and JWT access tokens.

Passwords are hashed with bcrypt through passlib. Tokens are signed with
SECRET_KEY (HS256) using PyJWT and carry the user id in the `sub` claim.
A token without `exp` or `sub` is rejected, so every token runs out.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

JWT_ALGORITHM = "HS256"

# bcrypt only uses the first 72 bytes of a password and silently ignores the rest.
# Registration rejects longer passwords, so a longer login password can never match.
BCRYPT_MAX_BYTES = 72

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain text password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


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
