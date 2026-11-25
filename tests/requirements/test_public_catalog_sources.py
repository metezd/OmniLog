"""The keyless catalog sources (US-08, US-09, #297).

With `IGDB_CLIENT_ID=public` games come from the Steam Store, and with `TMDB_API_KEY=public`
series come from TVMaze and movies from iTunes (see docs/deployment.md). These paths need no keys,
so they are tested here with fake answers. The calls go through `request_with_retry`, which is
replaced per module, so the parsing code runs as it does in production.
"""
import pytest

from app.core import config
from app.integrations import igdb, tmdb
from app.integrations.common import ExternalServiceError
from app.models.entities import MediaType
from fake_external_apis import make_response


class Router:
    """Answers each URL with a scripted (status, body) and records the calls."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def __call__(self, session, method, url, *, source, **kwargs):
        self.calls.append((method, url, kwargs.get("params")))
        status, body = self.answers[url]
        return make_response(status, body)


@pytest.fixture
def public_keys(monkeypatch):
    monkeypatch.setattr(config, "IGDB_CLIENT_ID", "public")
    monkeypatch.setattr(config, "TMDB_API_KEY", "public")


def route(monkeypatch, module, answers):
    router = Router(answers)
    monkeypatch.setattr(module, "request_with_retry", router)
    return router


TVMAZE_SEARCH = "https://api.tvmaze.com/search/shows"
ITUNES_SEARCH = "https://itunes.apple.com/search"
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"
STEAM_DETAILS = "https://store.steampowered.com/api/appdetails"


# ------------------------------------------------------------------------- series (TVMaze)
def test_us08_public_series_search_reads_tvmaze(public_keys, monkeypatch):
    router = route(monkeypatch, tmdb, {TVMAZE_SEARCH: (200, [
        {"show": {"id": 169, "name": "Breaking Bad", "premiered": "2008-01-20",
                  "image": {"original": "https://static.tvmaze.com/b.jpg"}}},
        {"show": {"id": 170, "name": "Medium only", "image": {"medium": "https://static.tvmaze.com/m.jpg"}}},
        {"show": {"id": 169, "name": "Breaking Bad"}},  # the same id again: removed
        {"show": {"name": "No id"}},
        {"show": "not an object"},
        "not an entry",
    ])})

    titles = tmdb.search(MediaType.SERIES, "breaking", 10)

    assert [(t.external_id, t.title) for t in titles] == [(169, "Breaking Bad"), (170, "Medium only")]
    assert titles[0].poster_url == "https://static.tvmaze.com/b.jpg"
    assert titles[0].release_date == "2008-01-20"
    assert titles[1].poster_url == "https://static.tvmaze.com/m.jpg"
    assert router.calls[0][2] == {"q": "breaking"}


def test_us08_public_series_search_respects_the_limit(public_keys, monkeypatch):
    shows = [{"show": {"id": n, "name": f"Show {n}"}} for n in range(1, 6)]
    route(monkeypatch, tmdb, {TVMAZE_SEARCH: (200, shows)})

    assert len(tmdb.search(MediaType.SERIES, "show", 2)) == 2


def test_us08_public_series_search_with_an_unexpected_body_is_empty(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {TVMAZE_SEARCH: (200, {"not": "a list"})})

    assert tmdb.search(MediaType.SERIES, "x", 5) == []


def test_us08_public_series_search_error_is_a_service_error(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {TVMAZE_SEARCH: (503, {})})

    with pytest.raises(ExternalServiceError, match="TVMaze answered 503"):
        tmdb.search(MediaType.SERIES, "x", 5)


def tvmaze_show(show_id=169):
    return f"https://api.tvmaze.com/shows/{show_id}"


def test_us09_public_series_details_with_seasons_and_episodes(public_keys, monkeypatch):
    router = route(monkeypatch, tmdb, {tvmaze_show(): (200, {
        "summary": "<p>A <b>chemistry</b> teacher.</p>",
        "genres": ["Drama", "Crime", 7],
        "_embedded": {
            "seasons": [
                {"number": 2, "name": "", "premiereDate": "2009-03-08"},
                {"number": 1, "name": "Season One", "premiereDate": "2008-01-20"},
                {"number": 1, "name": "Duplicate"},  # the same number again: ignored
                {"number": None},
                "not a season",
            ],
            "episodes": [
                {"id": 11, "season": 1, "number": 2, "name": "Cat's in the Bag", "airdate": "2008-01-27", "runtime": 48},
                {"id": 10, "season": 1, "number": 1, "name": "Pilot", "airdate": "2008-01-20", "runtime": 58},
                {"id": 12, "season": 1, "number": 1, "name": "Pilot again"},  # duplicate number: ignored
                {"id": 20, "season": 2, "number": 1, "name": "Seven Thirty-Seven", "airdate": "bad date"},
                {"season": None, "number": 1},
                "not an episode",
            ],
        },
    })})

    series = tmdb.fetch_series(169)

    assert series.details.description == "A chemistry teacher."
    assert set(series.details.genres) >= {"Drama", "Crime"}
    assert [(s.season_number, s.title, s.air_date) for s in series.seasons] == [
        (1, "Season One", "2008-01-20"),
        (2, "Season 2", "2009-03-08"),
    ]
    first = series.seasons[0].episodes
    assert [(e.number, e.title, e.runtime_minutes, e.external_id) for e in first] == [
        (1, "Pilot", 58, 10),
        (2, "Cat's in the Bag", 48, 11),
    ]
    assert series.seasons[1].episodes[0].release_date is None
    assert ("embed[]", "seasons") in router.calls[0][2]
    assert tmdb.fetch_series_seasons(169) == series.seasons


def test_us09_public_series_unknown_is_none(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {tvmaze_show(5): (404, {})})

    assert tmdb.fetch_series(5) is None


@pytest.mark.parametrize(("status", "body"), [(200, ["not", "an object"])])
def test_us09_public_series_with_an_unexpected_body_is_none(public_keys, monkeypatch, status, body):
    route(monkeypatch, tmdb, {tvmaze_show(6): (status, body)})

    assert tmdb.fetch_series(6) is None


def test_us09_public_series_without_embedded_data_has_no_seasons(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {tvmaze_show(7): (200, {"summary": None, "genres": "Drama"})})

    series = tmdb.fetch_series(7)

    assert series.seasons == []
    assert series.details.description is None
    assert series.details.genres == ()


def test_us09_public_series_error_is_a_service_error(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {tvmaze_show(8): (500, {})})

    with pytest.raises(ExternalServiceError, match="TVMaze answered 500"):
        tmdb.fetch_series(8)


# --------------------------------------------------------------------------- movies (iTunes)
def test_us08_public_movie_search_reads_itunes(public_keys, monkeypatch):
    router = route(monkeypatch, tmdb, {ITUNES_SEARCH: (200, {"results": [
        {"trackId": 1, "trackName": "Inception", "releaseDate": "2010-07-16T07:00:00Z",
         "artworkUrl100": "https://is1.mzstatic.com/a/100x100bb.jpg"},
        {"trackId": 2, "trackName": "No art", "releaseDate": 2010},
        {"trackName": "No id"},
        "not an item",
    ]})})

    titles = tmdb.search(MediaType.MOVIE, "inception", 10)

    assert [(t.external_id, t.title) for t in titles] == [(1, "Inception"), (2, "No art")]
    assert titles[0].poster_url == "https://is1.mzstatic.com/a/600x600bb.jpg"
    assert titles[0].release_date == "2010-07-16"
    assert titles[1].poster_url is None and titles[1].release_date is None
    assert router.calls[0][2] == {"term": "inception", "entity": "movie", "limit": 10}


def test_us08_public_movie_search_with_an_unexpected_body_is_empty(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {ITUNES_SEARCH: (200, {"results": "none"})})

    assert tmdb.search(MediaType.MOVIE, "x", 5) == []


def test_us08_public_movie_search_error_is_a_service_error(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {ITUNES_SEARCH: (429, {})})

    with pytest.raises(ExternalServiceError, match="iTunes answered 429"):
        tmdb.search(MediaType.MOVIE, "x", 5)


def test_us09_public_movie_details_read_the_long_description(public_keys, monkeypatch):
    router = route(monkeypatch, tmdb, {ITUNES_LOOKUP: (200, {"results": [
        {"longDescription": "A thief who steals secrets.", "shortDescription": "Short.",
         "primaryGenreName": "Sci-Fi & Fantasy"},
    ]})})

    details = tmdb.fetch_movie_details(1)

    assert details.description == "A thief who steals secrets."
    assert len(details.genres) >= 1
    assert router.calls[0][2] == {"id": 1, "entity": "movie"}


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (500, {}),
        (200, {"results": []}),
        (200, {"results": "none"}),
        (200, {"results": ["not an object"]}),
        (200, ["not an object"]),
    ],
)
def test_us09_public_movie_details_missing_are_none(public_keys, monkeypatch, status, body):
    route(monkeypatch, tmdb, {ITUNES_LOOKUP: (status, body)})

    assert tmdb.fetch_movie_details(1) is None


def test_us09_public_movie_details_fall_back_to_the_short_description(public_keys, monkeypatch):
    route(monkeypatch, tmdb, {ITUNES_LOOKUP: (200, {"results": [{"shortDescription": "Short."}]})})

    details = tmdb.fetch_movie_details(1)

    assert details.description == "Short."
    assert details.genres == ()


# ---------------------------------------------------------------------------- games (Steam)
def test_us08_public_game_search_reads_the_steam_store(public_keys, monkeypatch):
    router = route(monkeypatch, igdb, {STEAM_SEARCH: (200, {"items": [
        {"id": 1091500, "name": "Cyberpunk 2077"},
        {"id": 1091500, "name": "Cyberpunk 2077"},  # duplicate: removed
        {"name": "No id"},
        "not an item",
    ]})})

    titles = igdb.search_games("cyber", 10)

    assert [(t.external_id, t.title, t.release_date) for t in titles] == [(1091500, "Cyberpunk 2077", None)]
    assert titles[0].poster_url.endswith("/apps/1091500/library_600x900.jpg")
    assert router.calls[0][2]["term"] == "cyber"


def test_us08_public_game_search_with_an_unexpected_body_is_empty(public_keys, monkeypatch):
    route(monkeypatch, igdb, {STEAM_SEARCH: (200, {"items": None})})

    assert igdb.search_games("x", 5) == []


def test_us08_public_game_search_error_is_a_service_error(public_keys, monkeypatch):
    route(monkeypatch, igdb, {STEAM_SEARCH: (502, {})})

    with pytest.raises(ExternalServiceError, match="Steam Store answered 502"):
        igdb.search_games("x", 5)


def test_us09_public_game_details_read_description_and_genres(public_keys, monkeypatch):
    route(monkeypatch, igdb, {STEAM_DETAILS: (200, {"1091500": {"success": True, "data": {
        "short_description": "An open world RPG.",
        "genres": [{"description": "RPG"}, "not an object"],
    }}})})

    details = igdb.fetch_game_details(1091500)

    assert details.description == "An open world RPG."
    assert len(details.genres) == 1


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (500, {}),
        (200, {"1091500": {"success": False}}),
        (200, {"1091500": {"success": True, "data": "none"}}),
        (200, {"other": {}}),
        (200, ["not an object"]),
    ],
)
def test_us09_public_game_details_missing_are_none(public_keys, monkeypatch, status, body):
    route(monkeypatch, igdb, {STEAM_DETAILS: (status, body)})

    assert igdb.fetch_game_details(1091500) is None


def test_us09_public_game_details_without_genres(public_keys, monkeypatch):
    route(monkeypatch, igdb, {STEAM_DETAILS: (200, {"7": {"success": True, "data": {"genres": None}}})})

    details = igdb.fetch_game_details(7)

    assert details.description is None
    assert details.genres == ()
