"""Registration, login and the current user (US-02, US-03)."""
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_token, get_current_user, limit_per_client
from app.core import config, rate_limit
from app.core.database import get_db
from app.core.security import AccessToken, create_access_token
from app.models.entities import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
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
    dependencies=[Depends(limit_per_client("register"))],
)
def register(data: UserCreate, db: Session = Depends(get_db)):
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
    return Token(access_token=create_access_token(user.id))


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
