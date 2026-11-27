"""Registration, login and the current user (US-02, US-03)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_token, get_current_user, limit_per_client
from app.core.database import get_db
from app.core.security import AccessToken, create_access_token
from app.models.entities import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services import auth_service
from app.services.auth_service import AccountConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


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
    """Log in with a username or an email in the field `username`."""
    user = auth_service.authenticate_user(db, data.username, data.password)
    if user is None:
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
