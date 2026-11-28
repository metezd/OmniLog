"""Business logic for registration and login."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.passwords import weakness
from app.core.security import BCRYPT_MAX_BYTES, DUMMY_HASH, AccessToken, hash_password, verify_password
from app.models.entities import RevokedToken, User
from app.schemas.user import UserCreate


class AccountConflictError(Exception):
    """Raised when the username or email is already registered."""


def register_user(db: Session, data: UserCreate) -> User:
    """Create a user with a hashed password. Raises AccountConflictError on duplicates.

    The 409 for a taken name stays, because without email verification the user must be told
    (#395, docs/deployment.md, section 9.2). The password is hashed before the check, so a taken
    and a free name cost the same bcrypt time and the time does not add a second signal.
    """
    email = data.email.lower()
    hashed_password = hash_password(data.password)

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
        hashed_password=hashed_password,
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


def revoke_token(db: Session, token: AccessToken) -> None:
    """End a token before its own end (POST /auth/logout, #378).

    The row is kept until the token would expire. Rows of tokens that have expired are deleted
    here, so the table stays small without a scheduled job. Logging out twice is not an error.
    """
    now = utc_now()
    db.query(RevokedToken).filter(RevokedToken.expires_at <= now).delete(synchronize_session=False)
    if db.get(RevokedToken, token.jti) is None:
        db.add(RevokedToken(jti=token.jti, user_id=token.user_id, expires_at=token.expires_at))
    try:
        db.commit()
    except IntegrityError:
        # Two logouts of the same token at the same time: the other one stored it
        db.rollback()


def is_revoked(db: Session, jti: str) -> bool:
    return db.get(RevokedToken, jti) is not None


# ---------------------------------------------------------------- account management (#426)
class WrongPasswordError(Exception):
    """The current password does not match."""


class WeakPasswordError(Exception):
    """The new password breaks a rule of BR-20, or it is the current password."""


def _check_password(user: User, password: str) -> None:
    if "\x00" in password or len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise WrongPasswordError("The password is not correct")
    if not verify_password(password, user.hashed_password):
        raise WrongPasswordError("The password is not correct")


def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    """Set a new password and end every session of the user (#426).

    The token version goes up, so every token issued before is refused, also the one of this
    request. The caller gives back a new token for this session.
    """
    _check_password(user, current_password)
    reason = weakness(new_password, user.username, user.email)
    if reason:
        raise WeakPasswordError(reason)
    if verify_password(new_password, user.hashed_password):
        raise WeakPasswordError("the new password must not be the current password")
    user.hashed_password = hash_password(new_password)
    user.token_version = User.token_version + 1
    db.commit()
    db.refresh(user)
    return user


def end_all_sessions(db: Session, user: User) -> None:
    """Log out on all devices: every token of the user is refused from now on (#426)."""
    user.token_version = User.token_version + 1
    db.commit()


def delete_account(db: Session, user: User, password: str) -> None:
    """Delete the user and all their data (#426). The database deletes the library, the lists, the
    diary, the progress and the reviews with it (BR-17)."""
    _check_password(user, password)
    db.delete(user)
    db.commit()

