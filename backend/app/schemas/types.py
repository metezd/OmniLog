"""Types shared by the response schemas."""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer, WithJsonSchema


def utc_iso(value: datetime) -> str:
    """A time as ISO 8601 in UTC with a Z, for example 2026-11-26T19:34:34.794654Z (#383).

    The DateTime columns have no time zone and hold UTC (app.core.clock). Without the Z, a client
    reads the time as its own local time: JavaScript does that, and the diary was 3 hours off in
    Turkey. A time with a time zone is changed to UTC first.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# A time in an answer of the API. It is read like a datetime and sent with "Z".
UtcDateTime = Annotated[
    datetime,
    PlainSerializer(utc_iso, return_type=str, when_used="json"),
    WithJsonSchema(
        {"type": "string", "format": "date-time", "description": "UTC, always with Z", "example": "2026-11-26T19:34:34.794654Z"},
        mode="serialization",
    ),
]
