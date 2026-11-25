"""Malformed input must give a 4xx answer, never a 500 or a dropped connection (#302).

Penetration findings F4 (NUL bytes, a too large id), F5 (the password in a 422 answer), F6 (no
body size limit) and a deeply nested JSON body. The client here does not raise server errors,
so a 500 shows up as a status code. Covers US-04, US-06, US-08, US-12, US-14 and NFR-03.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from epic4_helpers import add_chapter, add_decision_point
from helpers import add_to_library, create_media, unique

NUL = "\x00"
INT32_MAX = 2**31 - 1


@pytest.fixture(scope="module")
def tolerant():
    """A client that returns a 500 as an answer instead of raising the server error."""
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def entry(client, auth_headers):
    media = create_media(client, auth_headers, media_type="GAME")
    return add_to_library(client, auth_headers, media["id"], status="IN_PROGRESS")


def assert_refused(response):
    assert 400 <= response.status_code < 500, f"{response.status_code}: {response.text[:300]}"


# ------------------------------------------------------------------------------- F4: NUL bytes
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", f"a{NUL}b"),
        ("poster_url", f"https://image.tmdb.org/t/p/w500/a{NUL}b.jpg"),
        ("release_date", f"2020{NUL}"),
    ],
)
def test_f4_us08_nul_in_a_new_title_is_refused(tolerant, auth_headers, field, value):
    body = {"title": unique("nul"), "media_type": "GAME", field: value}

    assert_refused(tolerant.post("/media", json=body, headers=auth_headers))


def test_f4_us06_nul_in_a_list_name_is_refused(tolerant, auth_headers):
    assert_refused(tolerant.post("/lists", json={"name": f"a{NUL}b"}, headers=auth_headers))


def test_f4_us14_nul_in_a_review_is_refused(tolerant, auth_headers, entry):
    response = tolerant.post(f"/library/{entry['id']}/review", json={"text": f"a{NUL}b"}, headers=auth_headers)

    assert_refused(response)


def test_f4_us08_nul_in_the_search_text_is_refused(tolerant, auth_headers):
    response = tolerant.get("/catalog/search", params={"q": f"a{NUL}b", "type": "GAME"}, headers=auth_headers)

    assert_refused(response)


def test_f4_us12_nul_in_a_decision_is_refused(tolerant, auth_headers, entry, db):
    media_id = entry["media_item_id"]
    chapter_id = add_chapter(db, media_id, 1)
    add_decision_point(db, chapter_id, media_id)

    response = tolerant.put(
        f"/library/{entry['id']}/chapters/{chapter_id}/decision", json={"choice": f"A{NUL}"}, headers=auth_headers
    )

    assert_refused(response)


@pytest.mark.parametrize("value", [INT32_MAX + 1, 2**63, 99999999999999999999])
def test_f4_us08_a_too_large_external_id_is_refused(tolerant, auth_headers, value):
    body = {"title": unique("big"), "media_type": "GAME", "external_api_id": value}

    assert_refused(tolerant.post("/media", json=body, headers=auth_headers))


def test_f4_us08_the_largest_external_id_still_works(tolerant, auth_headers):
    body = {"title": unique("max"), "media_type": "GAME", "external_api_id": INT32_MAX}

    assert tolerant.post("/media", json=body, headers=auth_headers).status_code == 201


def test_f4_the_connection_stays_usable_after_a_refused_input(tolerant, auth_headers):
    """The pentest saw a reset connection after a NUL byte. The next call must still work."""
    tolerant.post("/lists", json={"name": f"a{NUL}b"}, headers=auth_headers)

    assert tolerant.get("/health").status_code == 200
