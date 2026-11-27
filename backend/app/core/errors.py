"""Global exception handlers."""
import logging
import math
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.integrations.common import ExternalServiceError

logger = logging.getLogger(__name__)


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


async def database_unavailable_exception_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    """The database could not be reached or dropped the connection (#411).

    This is a 503 and not a 500: the request was right, and the same request can work a moment
    later. The text of the database error can hold the host name, so it is only logged.
    """
    reason = type(getattr(exc, "orig", None) or exc).__name__
    logger.warning("The database is not available for %s %s (%s)", request.method, request.url.path, reason)
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is not available right now"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ExternalServiceError, external_service_exception_handler)
    app.add_exception_handler(OperationalError, database_unavailable_exception_handler)