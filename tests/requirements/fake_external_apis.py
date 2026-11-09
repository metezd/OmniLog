"""A fake of the Twitch, IGDB and TMDB web APIs, for the tests.

It replaces `requests.sessions.Session.request`, so the real client code runs in the tests:
sign-in, building the request, retries and reading the answer. Only the network is faked.

The fake checks each request the way the real services do (credentials, headers, the shape of the
IGDB query). A bug in the client therefore fails a test. A call to any other host fails too.

All titles and ids below are made-up test data.
"""
import copy
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
     "cover": {"id": 1, "image_id": "co1life"},
     "summary": "A student discovers that she can rewind time.",
     "genres": [{"id": 31, "name": "Adventure"}, {"id": 32, "name": "Indie"}]},
    {"id": 90002, "name": "Life is Strange 2", "first_release_date": _unix(2018, 9, 27),
     "cover": {"id": 2, "image_id": "co2life"}},
    {"id": 90003, "name": "Life is Strange: Before the Storm", "first_release_date": _unix(2017, 8, 31)},
]

SERIES = [
    {"id": 70001, "name": "Breaking Bad", "poster_path": "/bb.jpg", "first_air_date": "2008-01-20",
     "overview": "A teacher turns to crime.", "genre_ids": [18, 80]},
    {"id": 70002, "name": "Breaking Point", "poster_path": None, "first_air_date": ""},
]

MOVIES = [
    {"id": 80001, "title": "Blade Runner", "poster_path": "/br.jpg", "release_date": "1982-06-25",
     "overview": "A blade runner hunts replicants.", "genre_ids": [878, 53]},
]

# What TMDB says about a movie or a series on its own page, by TMDB id (made-up test data)
MOVIE_DETAILS = {
    80001: {"title": "Blade Runner", "overview": "A blade runner hunts replicants.",
            "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 53, "name": "Thriller"}]},
}
SERIES_INFO = {
    70001: {"overview": "A teacher turns to crime.",
            "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}]},
}



def _episode(number: int, name: str, air_date, runtime, episode_id: int) -> dict:
    return {"id": episode_id, "episode_number": number, "name": name,
            "air_date": air_date, "runtime": runtime}


def _season(number: int, name: str, air_date, episodes: list) -> dict:
    return {"season_number": number, "name": name, "air_date": air_date, "episodes": episodes}


# Seasons of the series above, by TMDB id. Series 70003 has many seasons, to test that they are
# asked for in groups. A series that is not in this table is unknown to TMDB (404).
SERIES_DETAILS = {
    70001: {"name": "Breaking Bad", "seasons": [
        _season(0, "Specials", None, [
            _episode(1, "Making of the pilot", None, None, 5001),
        ]),
        _season(1, "Season 1", "2008-01-20", [
            _episode(1, "Pilot", "2008-01-20", 58, 5101),
            _episode(2, "Cat's in the Bag...", "2008-01-27", 48, 5102),
            _episode(3, "...And the Bag's in the River", "2008-02-10", None, 5103),
        ]),
        _season(2, "Season 2", "2009-03-08", [
            _episode(1, "Seven Thirty-Seven", "2009-03-08", 47, 5201),
            _episode(2, "Grilled", "2009-03-15", 47, 5202),
        ]),
    ]},
    70002: {"name": "Breaking Point", "seasons": []},
    70003: {"name": "Endless Show", "seasons": [
        _season(n, f"Season {n}", f"{1980 + n}-01-01", [
            _episode(1, f"S{n} first", f"{1980 + n}-01-01", 30, 6000 + n * 10 + 1),
            _episode(2, f"S{n} second", f"{1980 + n}-01-08", 30, 6000 + n * 10 + 2),
        ])
        for n in range(1, 46)
    ]},
}

# TMDB answers at most 20 appended sub-requests in one call
_TMDB_MAX_APPENDED = 20

_IGDB_SEARCH = re.compile(r'search "([^"]*)"; fields ([a-z_.,]+); limit (\d+);')
_IGDB_BY_ID = re.compile(r'fields ([a-z_.,]+); where id = (\d+); limit (\d+);')


def _project(game: dict, fields: str) -> dict:
    """Keep the fields that were asked for, as IGDB does. The id is always there. A field such as
    genres.name asks for the name of each entry of genres."""
    result = {"id": game["id"]}
    for field in fields.split(","):
        top, _, sub = field.partition(".")
        if top not in game:
            continue
        value = game[top]
        if sub and isinstance(value, dict):
            result.setdefault(top, {"id": value["id"]})[sub] = value[sub]
        elif sub and isinstance(value, list):
            entries = result.setdefault(top, [{"id": entry["id"]} for entry in value])
            for entry, source in zip(entries, value):
                entry[sub] = source[sub]
        elif not sub:
            result[top] = value
    return result


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
        # TMDB series by id. Every test gets its own copy, so it can change what TMDB "knows".
        self.series: dict[int, dict] = copy.deepcopy(SERIES_DETAILS)
        # What TMDB says about a series (description and genres) and a movie, and what IGDB says
        # about a game. Tests can change them, like `series`.
        self.series_info: dict[int, dict] = copy.deepcopy(SERIES_INFO)
        self.movies: dict[int, dict] = copy.deepcopy(MOVIE_DETAILS)
        self.games: list[dict] = copy.deepcopy(GAMES)

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
        by_id = _IGDB_BY_ID.fullmatch(body)
        if by_id:
            fields, game_id, limit = by_id.group(1), int(by_id.group(2)), int(by_id.group(3))
            matches = [g for g in self.games if g["id"] == game_id]
        else:
            parsed = _IGDB_SEARCH.fullmatch(body)
            assert parsed, f"IGDB query has an unexpected shape: {body!r}"
            text, fields, limit = parsed.group(1), parsed.group(2), int(parsed.group(3))
            matches = [g for g in self.games if text.lower() in g["name"].lower()]
        return make_response(200, [_project(g, fields) for g in matches[:limit]])

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
        series_path = re.fullmatch(r"/3/tv/(\d+)", path)
        if series_path:
            return self._tmdb_series(int(series_path.group(1)), params)
        movie_path = re.fullmatch(r"/3/movie/(\d+)", path)
        if movie_path:
            movie = self.movies.get(int(movie_path.group(1)))
            if movie is None:
                return make_response(404, {"success": False, "status_code": 34,
                                           "status_message": "The resource you requested could not be found."})
            return make_response(200, {"id": int(movie_path.group(1)), **movie})
        if path == "/3/search/tv":
            pool, field = SERIES, "name"
        elif path == "/3/search/movie":
            pool, field = MOVIES, "title"
        else:
            raise AssertionError(f"Unexpected TMDB path: {path}")
        matches = [item for item in pool if params["query"].lower() in item[field].lower()]
        return make_response(200, {"page": 1, "results": matches, "total_results": len(matches)})

    def _tmdb_series(self, series_id: int, params: dict) -> requests.Response:
        """GET /tv/{id}: the series with its season list, plus the seasons asked for."""
        show = self.series.get(series_id)
        if show is None:
            return make_response(404, {"success": False, "status_code": 34,
                                       "status_message": "The resource you requested could not be found."})

        body = {
            "id": series_id,
            "name": show["name"],
            **self.series_info.get(series_id, {}),
            "seasons": [
                {"season_number": season["season_number"], "name": season["name"],
                 "air_date": season["air_date"], "episode_count": len(season["episodes"])}
                for season in show["seasons"]
            ],
        }

        appended = [part for part in params.get("append_to_response", "").split(",") if part]
        assert len(appended) <= _TMDB_MAX_APPENDED, f"TMDB allows {_TMDB_MAX_APPENDED} appended requests"
        for part in appended:
            asked = re.fullmatch(r"season/(\d+)", part)
            assert asked, f"Unexpected append_to_response value: {part!r}"
            number = int(asked.group(1))
            season = next((s for s in show["seasons"] if s["season_number"] == number), None)
            if season is not None:  # TMDB leaves out a season it does not have
                body[part] = season
        return make_response(200, body)
