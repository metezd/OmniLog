"""Registration, login and the current user (US-02, US-03)."""
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_token, get_current_user, limit_per_client
from app.core import config, rate_limit
from app.core.database import get_db
from app.core.security import AccessToken, create_access_token
from app.models.entities import User
from app.schemas.user import AccountDelete, PasswordChange, Token, UserCreate, UserLogin, UserResponse
from app.services import auth_service
from app.services.auth_service import AccountConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


def account_key(identifier: str) -> str:
    """The key of an account for the limit of failed logins: a hash of the normalized username or
    email, so no username or email address is written to Redis (#391)."""
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_per_client("register")), Depends(limit_per_client("register_day"))],
)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Create an account. A taken username or email answers 409 (US-02).

    The 409 shows that an email has an account. The project accepts this, because there is no
    email verification that could tell the user instead. The limits per hour and per day keep a
    search for addresses slow (#395, docs/deployment.md, section 9.2).
    """
    try:
        return auth_service.register_user(db, data)
    except AccountConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=Token, dependencies=[Depends(limit_per_client("login"))])
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Log in with a username or an email in the field `username`.

    Besides the limit per address, the failed logins of one account are limited from any address
    (RATE_LIMIT_LOGIN_ACCOUNT, #391). Over the limit, the password is not checked at all, so a
    guess cannot succeed either. Unknown accounts are counted the same way, so the answer does not
    show which accounts exist.
    """
    account = account_key(data.username)
    rate_limit.check_failures("login_account", account)
    user = auth_service.authenticate_user(db, data.username, data.password)
    if user is None:
        if config.RATE_LIMIT_ENABLED:
            rate_limit.record_failure("login_account", account)
        # Same message for unknown accounts and wrong passwords
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id, user.token_version))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: AccessToken = Depends(get_current_token), db: Session = Depends(get_db)):
    """End the token of this request (#378). Other tokens of the same user keep working.

    A token that is already logged out, expired or invalid gets 401, like on every protected
    endpoint.
    """
    auth_service.revoke_token(db, token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """The logged in user. The token holds only the id, so clients call this to show who is logged in."""
    return current_user


# ---------------------------------------------------------------- account management (#426)
# A wrong password answers 403, not 401: the frontend reads 401 as "the session has ended" and
# would log the user out. The limit per address of the login also counts these tries.
def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.put("/password", response_model=Token, dependencies=[Depends(limit_per_client("login"))])
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the password. Every session ends, also on other devices, and the answer holds a new
    token for this one. 403 for a wrong current password, 422 for a new password that breaks a rule
    of BR-20 or is the current one."""
    try:
        user = auth_service.change_password(db, current_user, data.current_password, data.new_password)
    except auth_service.WrongPasswordError as exc:
        raise _forbidden(exc)
    except auth_service.WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[{"type": "value_error", "loc": ["body", "new_password"], "msg": f"Value error, {exc}"}],
        )
    return Token(access_token=create_access_token(user.id, user.token_version))


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Log out on all devices: every token of the user stops working, also the one of this
    request."""
    auth_service.end_all_sessions(db, current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(limit_per_client("login"))])
def delete_account(
    data: AccountDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the account with all its data: the library, the lists, the diary, the progress and
    the reviews (BR-17). The titles of the catalog stay. 403 for a wrong password."""
    try:
        auth_service.delete_account(db, current_user, data.password)
    except auth_service.WrongPasswordError as exc:
        raise _forbidden(exc)

