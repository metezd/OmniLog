"""Smoke tests against the real IGDB and TMDB. They are skipped unless you ask for them:

    RUN_LIVE_API_TESTS=1 python -m pytest tests/requirements/test_epic3_catalog_live.py -v

Put real keys in backend/.env first (IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, TMDB_API_KEY). The other
catalog tests use a fake, so only these show that the real services still answer as expected.
"""
import pytest

from app.core import config

pytestmark = pytest.mark.live


def _search(client, headers, q, type_):
    return client.get("/catalog/search", params={"q": q, "type": type_}, headers=headers)


def test_live_igdb_finds_life_is_strange(client, auth_headers):
    if config.IGDB_CLIENT_ID.startswith("test-"):
        pytest.skip("real IGDB keys are not set")

    response = _search(client, auth_headers, "Life is Strange", "GAME")

    assert response.status_code == 200, response.text
    assert any(item["title"] == "Life is Strange" for item in response.json())
    assert all("poster_url" in item and "release_date" in item for item in response.json())


def test_live_tmdb_finds_a_series_and_a_movie(client, auth_headers):
    if config.TMDB_API_KEY.startswith("test-"):
        pytest.skip("a real TMDB key is not set")

    series = _search(client, auth_headers, "Breaking Bad", "SERIES")
    movie = _search(client, auth_headers, "Blade Runner", "MOVIE")

    assert series.status_code == movie.status_code == 200
    assert any(item["title"] == "Breaking Bad" for item in series.json())
    assert any(item["title"] == "Blade Runner" for item in movie.json())


def test_live_tmdb_series_details_have_seasons_and_episodes(client, auth_headers):
    """US-09: the real TMDB answers the season calls (including append_to_response) as expected."""
    if config.TMDB_API_KEY.startswith("test-"):
        pytest.skip("a real TMDB key is not set")
    found = _search(client, auth_headers, "Breaking Bad", "SERIES")
    series = next(item for item in found.json() if item["title"] == "Breaking Bad")

    response = client.get(f"/catalog/{series['id']}", headers=auth_headers)

    assert response.status_code == 200, response.text
    seasons = {s["season_number"]: s for s in response.json()["seasons"]}
    assert {1, 2, 3, 4, 5} <= set(seasons)
    assert len(seasons[1]["episodes"]) == 7
    assert seasons[1]["episodes"][0]["title"]
