"""FastAPI dependencies shared by protected endpoints."""
import ipaddress
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import config, rate_limit
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


def client_address(request: Request) -> str:
    """The address of the client that a per-client rate limit counts (#217, #251).

    With FORWARDED_TRUSTED_HOPS = n > 0, the address is the n-th one from the right end of
    X-Forwarded-For. Each trusted proxy adds one address at the right end, so these are written by
    the proxies. The left end is written by the client and is never used, because a client could
    send a new fake address with every call. When the header is shorter than n or the address is
    not valid, the address that uvicorn gives is used.

    With 0 (default), uvicorn gives the address. Behind the Docker proxy it reads X-Forwarded-For
    only from the addresses in FORWARDED_ALLOW_IPS (see docs/deployment.md).
    """
    fallback = request.client.host if request.client else "unknown"
    hops = config.FORWARDED_TRUSTED_HOPS
    if hops <= 0:
        return fallback
    # Several X-Forwarded-For headers count as one list, in order
    header = ",".join(request.headers.getlist("x-forwarded-for"))
    addresses = [part.strip() for part in header.split(",") if part.strip()]
    if len(addresses) < hops:
        return fallback
    try:
        return str(ipaddress.ip_address(addresses[-hops]))
    except ValueError:
        return fallback


def limit_per_client(name: str) -> Callable[[Request], None]:
    """A dependency that applies the rate limit `name` to the address of the client (#217).

    See client_address for which address is counted.
    """

    def dependency(request: Request) -> None:
        rate_limit.check(name, client_address(request))

    return dependency


def limit_per_user(name: str) -> Callable[[User], None]:
    """A dependency that applies the rate limit `name` to the logged in user (#217).

    get_current_user runs first, so a call without a valid token gets 401 and is not counted.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        rate_limit.check(name, f"user:{current_user.id}")

    return dependency
