"""A fake of the Twitch, IGDB and TMDB web APIs, for the tests.

It replaces `requests.sessions.Session.request`, so the real client code runs in the tests:
sign-in, building the request, retries and reading the answer. Only the network is faked.

The fake checks each request the way the real services do (credentials, headers, the shape of the
IGDB query). A bug in the client therefore fails a test. A call to any other host fails too.

All titles and ids below are made-up test data.
"""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import requests


def _unix(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())


GAMES = [
    {"id": 90001, "name": "Life is Strange", "first_release_date": _unix(2015, 1, 30),
     "cover": {"id": 1, "image_id": "co1life"}},
    {"id": 90002, "name": "Life is Strange 2", "first_release_date": _unix(2018, 9, 27),
     "cover": {"id": 2, "image_id": "co2life"}},
    {"id": 90003, "name": "Life is Strange: Before the Storm", "first_release_date": _unix(2017, 8, 31)},
]

SERIES = [
    {"id": 70001, "name": "Breaking Bad", "poster_path": "/bb.jpg", "first_air_date": "2008-01-20"},
    {"id": 70002, "name": "Breaking Point", "poster_path": None, "first_air_date": ""},
]

MOVIES = [
    {"id": 80001, "title": "Blade Runner", "poster_path": "/br.jpg", "release_date": "1982-06-25"},
]

_IGDB_QUERY = re.compile(r'search "([^"]*)"; fields ([a-z_.,]+); limit (\d+);')


@dataclass
class Call:
    service: str  # "twitch", "igdb" or "tmdb"
    method: str
    url: str
    params: dict
    data: Any
    headers: dict

    @property
    def body(self) -> str:
        return self.data.decode("utf-8") if isinstance(self.data, bytes) else str(self.data or "")


def make_response(status: int = 200, body: Any = None, headers: Optional[dict] = None) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    response._content = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    response.encoding = "utf-8"
    response.url = "https://fake.invalid/"
    return response


class FakeExternalApis:
    def __init__(self) -> None:
        self.calls: list[Call] = []
        self._scripted: dict[str, list[list]] = {}  # service -> [[factory, times left or None]]
        self._issued_tokens = 0
        self._valid_tokens: set[str] = set()

    # ------------------------------------------------------------ what tests can ask
    def calls_to(self, service: str) -> list[Call]:
        return [call for call in self.calls if call.service == service]

    def count(self, service: Optional[str] = None) -> int:
        return len(self.calls if service is None else self.calls_to(service))

    # ------------------------------------------------------------ what tests can script
    def fail(self, service: str, *, status: Optional[int] = None,
             exception: Optional[Exception] = None, headers: Optional[dict] = None,
             times: Optional[int] = 1) -> None:
        """Make the next `times` calls to a service fail. times=None means always."""
        if exception is not None:
            def factory():
                raise exception
        else:
            def factory():
                return make_response(status or 500, {"message": "scripted failure"}, headers)
        self._scripted.setdefault(service, []).append([factory, times])

    def respond(self, service: str, body: Any, status: int = 200, times: Optional[int] = 1) -> None:
        """Answer the next `times` calls to a service with this body."""
        self._scripted.setdefault(service, []).append(
            [lambda: make_response(status, body), times]
        )

    def expire_tokens(self) -> None:
        """IGDB refuses every token issued so far, as if they had expired."""
        self._valid_tokens.clear()

    # ------------------------------------------------------------ the fake itself
    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        service = self._service_for(url)
        self.calls.append(
            Call(service, method, url, kwargs.get("params") or {}, kwargs.get("data"),
                 kwargs.get("headers") or {})
        )
        assert kwargs.get("timeout"), f"{service} call has no timeout"

        scripted = self._next_scripted(service)
        if scripted is not None:
            return scripted()
        return getattr(self, f"_{service}")(method, url, kwargs)

    @staticmethod
    def _service_for(url: str) -> str:
        host = urlparse(url).hostname
        services = {"id.twitch.tv": "twitch", "api.igdb.com": "igdb", "api.themoviedb.org": "tmdb"}
        assert host in services, f"Unexpected call to an outside host: {url}"
        return services[host]

    def _next_scripted(self, service: str):
        queue = self._scripted.get(service)
        if not queue:
            return None
        factory, times = queue[0]
        if times is not None:
            queue[0][1] = times - 1
            if queue[0][1] <= 0:
                queue.pop(0)
        return factory

    def _twitch(self, method: str, url: str, kwargs: dict) -> requests.Response:
        from app.core import config

        assert method == "POST"
        assert "client_secret" not in url and not kwargs.get("params"), "secret must not be in the URL"
        data = kwargs.get("data") or {}
        if (data.get("client_id") != config.IGDB_CLIENT_ID
                or data.get("client_secret") != config.IGDB_CLIENT_SECRET
                or data.get("grant_type") != "client_credentials"):
            return make_response(400, {"status": 400, "message": "invalid client"})
        self._issued_tokens += 1
        token = f"test-access-token-{self._issued_tokens}"
        self._valid_tokens.add(token)
        return make_response(200, {"access_token": token, "expires_in": 3600, "token_type": "bearer"})

    def _igdb(self, method: str, url: str, kwargs: dict) -> requests.Response:
        from app.core import config

        assert method == "POST" and url == "https://api.igdb.com/v4/games"
        headers = kwargs.get("headers") or {}
        token = headers.get("Authorization", "").removeprefix("Bearer ")
        if headers.get("Client-ID") != config.IGDB_CLIENT_ID or token not in self._valid_tokens:
            return make_response(401, {"message": "Authorization Failure"})

        body = kwargs["data"].decode("utf-8")
        parsed = _IGDB_QUERY.fullmatch(body)
        assert parsed, f"IGDB query has an unexpected shape: {body!r}"
        text, limit = parsed.group(1), int(parsed.group(3))
        matches = [g for g in GAMES if text.lower() in g["name"].lower()]
        return make_response(200, matches[:limit])

    def _tmdb(self, method: str, url: str, kwargs: dict) -> requests.Response:
        from app.core import config

        assert method == "GET"
        headers, params = kwargs.get("headers") or {}, kwargs.get("params") or {}
        key = config.TMDB_API_KEY
        if key.startswith("eyJ"):
            authorized = headers.get("Authorization") == f"Bearer {key}" and "api_key" not in params
        else:
            authorized = params.get("api_key") == key
        if not authorized:
            return make_response(401, {"status_code": 7, "status_message": "Invalid API key"})

        path = urlparse(url).path
        if path == "/3/search/tv":
            pool, field = SERIES, "name"
        elif path == "/3/search/movie":
            pool, field = MOVIES, "title"
        else:
            raise AssertionError(f"Unexpected TMDB path: {path}")
        matches = [item for item in pool if params["query"].lower() in item[field].lower()]
        return make_response(200, {"page": 1, "results": matches, "total_results": len(matches)})
