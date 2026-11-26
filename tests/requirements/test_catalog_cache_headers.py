"""NFR-01: the read-only catalog answers can be kept by the client for a short time (#250).

GET /catalog/search and GET /catalog/{id} answer with catalog data only, the same for every user,
so a client may reuse an answer for 5 minutes and show a stale one for 10 more while it asks
again. The answers need a token, so they are `private`: a shared cache (a CDN or a proxy) must not
keep them and give them to someone without a token. Errors and the other endpoints are not cached.
"""
import itertools

import pytest

from fake_external_apis import SERIES_DETAILS

CATALOG_CACHE = "private, max-age=300, stale-while-revalidate=600"

_outside_ids = itertools.count(880001)


def new_series(client, headers, fake):
    external_id = next(_outside_ids)
    fake.series[external_id] = dict(SERIES_DETAILS[70001])
    response = client.post(
        "/media",
        json={"title": f"cache-header series {external_id}", "media_type": "SERIES", "external_api_id": external_id},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_search_answer_may_be_kept_by_the_client(client, auth_headers, fake_external_apis):
    response = client.get("/catalog/search", params={"q": "Witcher", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["cache-control"] == CATALOG_CACHE


def test_details_answer_may_be_kept_by_the_client(client, auth_headers, fake_external_apis):
    media_id = new_series(client, auth_headers, fake_external_apis)

    response = client.get(f"/catalog/{media_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["cache-control"] == CATALOG_CACHE


def test_catalog_answers_are_never_public(client, auth_headers, fake_external_apis):
    response = client.get("/catalog/search", params={"q": "Witcher", "type": "GAME"}, headers=auth_headers)

    directives = [part.strip() for part in response.headers["cache-control"].split(",")]
    assert "private" in directives
    assert "public" not in directives


def test_a_missing_title_is_not_cached(client, auth_headers):
    response = client.get("/catalog/999999999", headers=auth_headers)

    assert response.status_code == 404
    assert "max-age" not in response.headers.get("cache-control", "")


def test_a_failed_search_is_not_cached(client, auth_headers, fake_external_apis):
    fake_external_apis.fail("igdb", status=500, times=None)

    response = client.get("/catalog/search", params={"q": "nothing saved zz", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 503
    assert "max-age" not in response.headers.get("cache-control", "")


def test_a_bad_query_is_not_cached(client, auth_headers):
    response = client.get("/catalog/search", params={"q": " ", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 422
    assert "max-age" not in response.headers.get("cache-control", "")


def test_without_a_token_nothing_is_cached(client):
    response = client.get("/catalog/search", params={"q": "Witcher", "type": "GAME"})

    assert response.status_code == 401
    assert "max-age" not in response.headers.get("cache-control", "")


@pytest.mark.parametrize("path", ["/library", "/stats", "/diary"])
def test_user_data_is_not_given_the_catalog_cache(client, auth_headers, path):
    # The answers of a user's own data change with every write, so they are not cached
    response = client.get(path, headers=auth_headers)

    assert response.status_code == 200
    assert "max-age" not in response.headers.get("cache-control", "")
