"""Epic 3 - Multi-Media Aggregation and Cataloging (US-08, US-09).

Note: the caching criterion of US-08 (a repeated search must not call the
external API again) is measured by NFR-01 in test_nfr.py.

The outside services are faked (see fake_external_apis.py). More cases for US-09 are in
test_epic3_title_details_edge_cases.py, including the chapters of a game, which no endpoint can
create yet and which that file therefore puts in the database directly.
"""


# ---------------------------------------------------------------- US-08
def test_us08_search_catalog(client, auth_headers):
    """US-08: searching a known game returns results with the required fields."""
    response = client.get(
        "/catalog/search",
        params={"q": "Life is Strange", "type": "GAME"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    for item in results:
        assert item["title"]
        assert "poster_url" in item
        assert "release_date" in item


def test_us08_search_no_results_returns_empty_list(client, auth_headers):
    """US-08: a query that matches nothing returns [] with status 200."""
    response = client.get(
        "/catalog/search",
        params={"q": "zzzzqqqqxxxxnonexistenttitle", "type": "GAME"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------- US-09
def test_us09_title_details_with_chapters(client, auth_headers, media_item):
    """US-09: title details include seasons (series) or chapters (games)."""
    response = client.get(f"/catalog/{media_item['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == media_item["id"]
    assert "seasons" in body or "chapters" in body


def test_us09_series_details_include_seasons_and_episodes(client, auth_headers):
    """US-09: a series from the catalog has its seasons, and each season has its episodes."""
    found = client.get(
        "/catalog/search",
        params={"q": "Breaking Bad", "type": "SERIES"},
        headers=auth_headers,
    )
    series = next(item for item in found.json() if item["title"] == "Breaking Bad")

    response = client.get(f"/catalog/{series['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == series["id"]
    assert body["title"] == "Breaking Bad"
    assert [season["season_number"] for season in body["seasons"]] == [0, 1, 2]
    season_one = body["seasons"][1]
    assert [episode["number"] for episode in season_one["episodes"]] == [1, 2, 3]
    assert season_one["episodes"][0]["title"] == "Pilot"


def test_us09_unknown_title_returns_404(client, auth_headers):
    """US-09: an unknown id returns 404."""
    response = client.get("/catalog/99999999", headers=auth_headers)

    assert response.status_code == 404
