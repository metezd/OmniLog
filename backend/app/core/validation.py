"""Shared checks for the values that clients send (#302).

PostgreSQL cannot store a NUL byte in a text column, and the driver refuses it with an error that
became a 500. Every text that a client sends uses the `NoNulStr` type, so it gets a 422 instead.
"""
from typing import Annotated

from pydantic import AfterValidator, Field

# The largest value of a PostgreSQL `integer` column. A larger id would be refused by the database.
INT32_MAX = 2**31 - 1


def reject_nul(value: str) -> str:
    """Refuse a text with a NUL byte."""
    if "\x00" in value:
        raise ValueError("must not contain NUL characters")
    return value


NoNulStr = Annotated[str, AfterValidator(reject_nul)]

# An outside id (IGDB, TMDB, Steam, TVMaze, iTunes) that fits the `integer` column
ExternalId = Annotated[int, Field(ge=1, le=INT32_MAX)]
