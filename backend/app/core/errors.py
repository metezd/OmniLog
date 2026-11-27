"""Global exception handlers."""
import math
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.integrations.common import ExternalServiceError


# Only these keys of a validation error go to the client. `input` (the rejected value) and `ctx`
# (which can hold it again) are left out: they could repeat a password (penetration finding F5),
# send a huge value back (F6), or hold a value nested thousands of levels deep (#302).
_ERROR_KEYS = ("type", "loc", "msg")


def _safe_text(value: Any) -> Any:
    """A loc part or a message as plain text or a number. NaN and Infinity are not valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = [
        {
            key: [_safe_text(part) for part in error[key]] if key == "loc" else _safe_text(error[key])
            for key in _ERROR_KEYS
            if key in error
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


async def external_service_exception_handler(
    request: Request, exc: ExternalServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "External service is unavailable"},
    )


# The database is busy or does not answer: try again after a short time (#392)
_DATABASE_RETRY_AFTER = "5"


async def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """503 instead of 500 when no pool connection is free in DB_POOL_TIMEOUT seconds, when a
    statement takes longer than DB_STATEMENT_TIMEOUT_MS, or when the database cannot be reached.
    The text of the error is not sent, it can hold the address of the database."""
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is busy or unavailable. Please try again."},
        headers={"Retry-After": _DATABASE_RETRY_AFTER},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ExternalServiceError, external_service_exception_handler)
    app.add_exception_handler(PoolTimeoutError, database_unavailable_handler)
    app.add_exception_handler(OperationalError, database_unavailable_handler)
