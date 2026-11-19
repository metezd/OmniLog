"""FastAPI dependencies shared by protected endpoints."""
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import User

# auto_error=False lets us return 401 ourselves instead of FastAPI's 403
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the logged in user, or raise 401 when the token is missing or invalid."""

    def unauthorized() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials is None:
        raise unauthorized()

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized()

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized()
    return user


def limit_per_client(name: str) -> Callable[[Request], None]:
    """A dependency that applies the rate limit `name` to the address of the client (#217).

    Behind the proxy, uvicorn takes the address from X-Forwarded-For, but only when the call comes
    from an address in FORWARDED_ALLOW_IPS (see docs/deployment.md).
    """

    def dependency(request: Request) -> None:
        rate_limit.check(name, request.client.host if request.client else "unknown")

    return dependency


def limit_per_user(name: str) -> Callable[[User], None]:
    """A dependency that applies the rate limit `name` to the logged in user (#217).

    get_current_user runs first, so a call without a valid token gets 401 and is not counted.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        rate_limit.check(name, f"user:{current_user.id}")

    return dependency
