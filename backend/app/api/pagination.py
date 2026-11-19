"""Query parameters for the list endpoints (`limit` and `offset`).

The answer of a list endpoint stays a plain JSON list. The order is fixed by each endpoint, so
`offset` always means "skip this many rows of that order".
"""
from dataclasses import dataclass

from fastapi import Query

MAX_LIMIT = 500
DIARY_DEFAULT_LIMIT = 100
LIBRARY_DEFAULT_LIMIT = 200
LISTS_DEFAULT_LIMIT = 200


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def _limit_query(default: int):
    return Query(
        default,
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of rows to return (1 to {MAX_LIMIT}, default {default}).",
    )


_OFFSET_QUERY = Query(0, ge=0, description="Number of rows to skip (default 0).")


def diary_page(limit: int = _limit_query(DIARY_DEFAULT_LIMIT), offset: int = _OFFSET_QUERY) -> Page:
    return Page(limit=limit, offset=offset)


def library_page(
    limit: int = _limit_query(LIBRARY_DEFAULT_LIMIT), offset: int = _OFFSET_QUERY
) -> Page:
    return Page(limit=limit, offset=offset)


def lists_page(limit: int = _limit_query(LISTS_DEFAULT_LIMIT), offset: int = _OFFSET_QUERY) -> Page:
    return Page(limit=limit, offset=offset)
