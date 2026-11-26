"""NFR-01: large JSON answers are compressed, and library answers run a fixed number of queries (#250).

GZipMiddleware compresses answers of at least 1000 bytes when the client sends
`Accept-Encoding: gzip`. Smaller answers stay plain. The library endpoints load the media item and
its genres together with the entry, so the number of queries does not grow with the data.
"""
from sqlalchemy import event

from app.core.database import engine
from helpers import add_to_library, create_media, new_credentials, register_and_login


def _count_queries(call) -> tuple[object, int]:
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        response = call()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return response, len(statements)


# ---------------------------------------------------------------- compression
def test_large_library_answer_is_gzip_compressed(client):
    """NFR-01: a library answer over 1000 bytes comes back gzip compressed and still reads as JSON."""
    headers = register_and_login(client, new_credentials())
    for _ in range(10):
        add_to_library(client, headers, create_media(client, headers)["id"])

    response = client.get("/library", headers={**headers, "Accept-Encoding": "gzip"})

    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"
    assert "accept-encoding" in response.headers.get("vary", "").lower()
    # The test client decompresses the body, so the JSON must read as before
    assert len(response.json()) == 10


def test_small_answer_is_not_compressed(client):
    """NFR-01: an answer under 1000 bytes stays plain, because compressing it saves nothing."""
    response = client.get("/health", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == 200
    assert "content-encoding" not in response.headers


def test_answer_is_plain_without_accept_encoding(client):
    """NFR-01: a client that does not accept gzip gets a plain answer, also for a large one."""
    headers = register_and_login(client, new_credentials())
    for _ in range(10):
        add_to_library(client, headers, create_media(client, headers)["id"])

    response = client.get("/library", headers={**headers, "Accept-Encoding": "identity"})

    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert len(response.json()) == 10


def test_compressed_answer_keeps_the_security_headers(client):
    """NFR-02: compression does not drop the security headers of an answer."""
    headers = register_and_login(client, new_credentials())
    for _ in range(10):
        add_to_library(client, headers, create_media(client, headers)["id"])

    response = client.get("/library", headers={**headers, "Accept-Encoding": "gzip"})

    assert response.headers.get("content-encoding") == "gzip"
    assert response.headers.get("x-content-type-options") == "nosniff"


# ---------------------------------------------------------------- queries
def test_add_and_update_load_the_media_item_with_the_entry(client):
    """US-04, US-05: POST and PATCH /library answer with the media item without extra lazy loads.

    The answer of a new entry and of an updated entry hold the media item and its genres. They are
    loaded with the entry, so PATCH runs the same number of queries for any title.
    """
    headers = register_and_login(client, new_credentials())
    first = add_to_library(client, headers, create_media(client, headers)["id"])
    second = add_to_library(client, headers, create_media(client, headers)["id"])

    response_one, queries_one = _count_queries(
        lambda: client.patch(f"/library/{first['id']}", json={"rating": 7}, headers=headers)
    )
    response_two, queries_two = _count_queries(
        lambda: client.patch(f"/library/{second['id']}", json={"rating": 8}, headers=headers)
    )

    assert response_one.status_code == 200
    assert response_one.json()["media_item"]["id"] == first["media_item_id"]
    assert response_two.json()["rating"] == 8
    assert queries_one == queries_two
    assert first["media_item"]["id"] == first["media_item_id"]
