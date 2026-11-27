"""Every time in an answer of the API is UTC and says so with a Z (#383).

The database keeps UTC without a time zone. Before, the API sent "2026-11-26T19:34:34.794654", and
JavaScript read it as local time, so the diary in Turkey was 3 hours off.
"""
import re
from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.schemas.types import utc_iso
from helpers import add_to_library, create_media, new_credentials

UTC_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
TIME_FIELDS = {"created_at", "updated_at", "added_at", "logged_at", "decided_at"}


def _times(value, found=None):
    """All values of the time fields anywhere in a JSON answer."""
    found = [] if found is None else found
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TIME_FIELDS and item is not None:
                found.append((key, item))
            else:
                _times(item, found)
    elif isinstance(value, list):
        for item in value:
            _times(item, found)
    return found


def _assert_utc(body):
    times = _times(body)
    assert times, f"no time field in {body}"
    for key, text in times:
        assert UTC_ISO.match(text), f"{key} = {text!r} has no Z"
    return times


# ---------------------------------------------------------------- the serializer
@pytest.mark.parametrize(
    ("value", "text"),
    [
        (datetime(2026, 11, 26, 19, 34, 34, 794654), "2026-11-26T19:34:34.794654Z"),
        (datetime(2026, 11, 26, 19, 34, 34), "2026-11-26T19:34:34Z"),
        (datetime(2026, 11, 26, 19, 34, 34, tzinfo=timezone.utc), "2026-11-26T19:34:34Z"),
        # A time with another zone is changed to UTC first
        (datetime(2026, 11, 26, 22, 34, 34, tzinfo=timezone(timedelta(hours=3))), "2026-11-26T19:34:34Z"),
    ],
)
def test_utc_iso(value, text):
    assert utc_iso(value) == text


def test_the_text_is_read_back_as_the_same_utc_time():
    stored = datetime(2026, 11, 26, 19, 34, 34, 794654)

    assert datetime.fromisoformat(utc_iso(stored)) == stored.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------- the answers of the issue
def test_register_sends_created_at_with_z(client):
    response = client.post("/auth/register", json=new_credentials())

    assert response.status_code == 201
    _assert_utc(response.json())


def test_the_time_is_the_current_utc_time(client, auth_headers):
    before = datetime.now(timezone.utc)
    response = client.post("/lists", json={"name": "Times"}, headers=auth_headers)
    after = datetime.now(timezone.utc)

    created = datetime.fromisoformat(response.json()["created_at"])
    assert before - timedelta(seconds=1) <= created <= after + timedelta(seconds=1)


def test_lists_diary_library_and_reviews_send_times_with_z(client, auth_headers):
    media = create_media(client, auth_headers)
    entry = add_to_library(client, auth_headers, media["id"])
    custom_list = client.post("/lists", json={"name": "UTC"}, headers=auth_headers).json()
    client.post(f"/lists/{custom_list['id']}/items", json={"media_item_id": media["id"]}, headers=auth_headers)
    client.post(f"/library/{entry['id']}/review", json={"text": "Good."}, headers=auth_headers)

    for path in ("/auth/me", "/lists", f"/lists/{custom_list['id']}", "/diary", "/library", f"/library/{entry['id']}/review"):
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 200, (path, response.text)
        _assert_utc(response.json())


# ---------------------------------------------------------------- the OpenAPI schema
def test_the_openapi_schema_says_utc():
    schema = app.openapi()["components"]["schemas"]

    for name in ("UserResponse", "DiaryEntryResponse"):
        field = schema[name]["properties"]["created_at"]
        assert field["format"] == "date-time"
        assert "UTC" in field["description"]
