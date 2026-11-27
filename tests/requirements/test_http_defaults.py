"""The HTTP defaults of the API (#394): caching, CORS and HSTS.

1. Answers with user data are never kept by a browser or a proxy: they get `Cache-Control:
   no-store`. The catalog keeps its own header (#250).
2. CORS runs without credentials, because the token is sent in the Authorization header and the
   API sets no cookie. Only the methods of the API and the headers Authorization and Content-Type
   are allowed.
3. The API sends Strict-Transport-Security when the request came over HTTPS, once, and never
   over plain HTTP. Caddy drops the one of the API and sends its own.
"""
import re
from pathlib import Path

import pytest

from app.core.config import CORS_ORIGINS
from app.core.security_headers import HSTS_VALUE

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_ORIGIN = CORS_ORIGINS[0]
UNKNOWN_ORIGIN = "https://attacker.example"


# ---------------------------------------------------------------- 1. Cache-Control
@pytest.mark.parametrize("path", ["/library", "/diary", "/stats", "/lists", "/auth/me"])
def test_user_data_is_never_cached(client, auth_headers, path):
    response = client.get(path, headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"


def test_a_written_entry_is_not_cached(client, auth_headers, media_item):
    response = client.post("/library", json={"media_item_id": media_item["id"]}, headers=auth_headers)

    assert response.status_code in (200, 201), response.text
    assert response.headers["cache-control"] == "no-store"


def test_an_error_is_not_cached(client):
    response = client.get("/library")

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_the_catalog_keeps_its_own_header(client, auth_headers, fake_external_apis):
    response = client.get("/catalog/search", params={"q": "Witcher", "type": "GAME"}, headers=auth_headers)

    assert response.status_code == 200
    # One header only, the one of the endpoint
    assert response.headers.get_list("cache-control") == ["private, max-age=300, stale-while-revalidate=600"]


# ---------------------------------------------------------------- 2. CORS
def _preflight(client, origin, method="DELETE", headers="authorization, content-type"):
    return client.options(
        "/library",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )


def test_preflight_of_the_allowed_origin(client):
    response = _preflight(client, ALLOWED_ORIGIN)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "access-control-allow-credentials" not in response.headers
    methods = {part.strip() for part in response.headers["access-control-allow-methods"].split(",")}
    assert methods <= {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
    assert {"GET", "POST", "PUT", "PATCH", "DELETE"} <= methods
    allowed = {part.strip().lower() for part in response.headers["access-control-allow-headers"].split(",")}
    assert {"authorization", "content-type"} <= allowed


def test_preflight_of_an_unknown_origin_gets_no_cors_answer(client):
    response = _preflight(client, UNKNOWN_ORIGIN)

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_preflight_with_an_unknown_header_is_refused(client):
    response = _preflight(client, ALLOWED_ORIGIN, headers="x-anything")

    assert response.status_code == 400
    assert "x-anything" not in response.headers.get("access-control-allow-headers", "").lower()


def test_preflight_with_an_unknown_method_is_refused(client):
    response = _preflight(client, ALLOWED_ORIGIN, method="QUERY")

    assert response.status_code == 400


def test_a_simple_call_has_no_credentials_header(client, auth_headers):
    response = client.get("/library", headers={**auth_headers, "Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "access-control-allow-credentials" not in response.headers


# ---------------------------------------------------------------- 3. HSTS
def test_hsts_when_the_proxy_says_https(client):
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})

    assert response.headers.get_list("strict-transport-security") == [HSTS_VALUE]


def test_hsts_on_a_direct_https_request():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, base_url="https://testserver") as https_client:
        response = https_client.get("/health")

    assert response.headers.get_list("strict-transport-security") == [HSTS_VALUE]


@pytest.mark.parametrize("proto", [None, "http", "http, https"])
def test_no_hsts_over_plain_http(client, proto):
    headers = {"X-Forwarded-Proto": proto} if proto else {}

    response = client.get("/health", headers=headers)

    assert "strict-transport-security" not in response.headers


def test_hsts_value_is_valid():
    assert re.fullmatch(r"max-age=\d{6,}", HSTS_VALUE)


def test_caddy_drops_the_hsts_of_the_api_so_it_is_not_sent_twice():
    caddyfile = (ROOT / "docker/Caddyfile").read_text(encoding="utf-8")
    api_site = caddyfile[caddyfile.index("{$API_DOMAIN}"):]

    assert re.search(r"reverse_proxy backend:8000\s*\{[^}]*header_down\s+-Strict-Transport-Security", api_site)
    # Caddy still sends its own
    assert "import security_headers" in api_site
