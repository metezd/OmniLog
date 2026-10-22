"""Business logic for registration and login."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import BCRYPT_MAX_BYTES, DUMMY_HASH, hash_password, verify_password
from app.models.entities import User
from app.schemas.user import UserCreate


class AccountConflictError(Exception):
    """Raised when the username or email is already registered."""


def register_user(db: Session, data: UserCreate) -> User:
    """Create a user with a hashed password. Raises AccountConflictError on duplicates."""
    email = data.email.lower()

    taken = (
        db.query(User)
        .filter(or_(User.username == data.username, User.email == email))
        .first()
    )
    if taken is not None:
        raise AccountConflictError("Username or email is already registered")

    user = User(
        username=data.username,
        email=email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Another request registered the same name between the check and the insert
        db.rollback()
        raise AccountConflictError("Username or email is already registered")
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """Return the user when the credentials are correct, otherwise None.

    The identifier is a username or an email. A username never has an @ (BR-18), so a value with
    @ is an email. The schema has already normalized the identifier.
    """
    if "\x00" in password or len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        # bcrypt rejects NUL bytes and truncates longer input, so such a password is
        # never sent to bcrypt. No registered password can match it, so the answer is 401.
        return None

    column = User.email if "@" in identifier else User.username
    user = db.query(User).filter(column == identifier).first()
    if user is None:
        # Hash anyway so the response time does not reveal which usernames or emails exist
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
