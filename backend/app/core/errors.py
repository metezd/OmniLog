"""Global exception handlers."""
import math
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _replace_non_finite(value: Any) -> Any:
    """Turn NaN and Infinity into strings. They are not valid JSON and would break the response."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _replace_non_finite(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_replace_non_finite(item) for item in value]
    return value


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI echoes the rejected input in the error body. A NaN value there makes the
    # default JSON rendering fail with a 500, so the input is sanitized first.
    content = {"detail": jsonable_encoder(_replace_non_finite(exc.errors()))}
    return JSONResponse(status_code=422, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
