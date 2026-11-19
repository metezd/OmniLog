"""The current time for the database columns.

The DateTime columns have no time zone and hold UTC. ``datetime.utcnow()`` gave exactly that, but it
is deprecated since Python 3.12. ``utc_now()`` gives the same value: the time in UTC without a
``tzinfo``, so the stored values and the answers of the API do not change.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime, like the old ``datetime.utcnow()``."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
