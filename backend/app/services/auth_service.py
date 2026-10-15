"""Business logic for registration and login."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import DUMMY_HASH, hash_password, verify_password
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


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Return the user when the credentials are correct, otherwise None."""
    if "\x00" in password:
        # bcrypt cannot process NUL bytes, and no registered password contains one
        return None

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        # Hash anyway so the response time does not reveal which usernames exist
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
