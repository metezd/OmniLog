"""Description and genres of titles (US-09, US-15).

They are loaded when the details of a title are opened: from IGDB for a game, and from TMDB for a
movie and for a series (cache first). The genre names of both services are made the same before
they are saved, and the genres are rows of their own (tables `genres` and `media_item_genres`).
"""
import copy
import itertools

import pytest
from sqlalchemy import event, func
from sqlalchemy.exc import IntegrityError

from app.core import cache
from app.core.database import engine
from app.integrations import genres as genre_rules
from app.integrations.common import MAX_DESCRIPTION_LENGTH, clean_text
from app.models.entities import Genre, MediaItem, media_item_genres
from app.services import catalog_service
from fake_external_apis import SERIES_DETAILS
from helpers import add_to_library, create_media, unique

# The tests share one database, so every test that loads a series gets an outside id of its own
_outside_ids = itertools.count(3_000_000)


def open_title(client, headers, media_id):
    return client.get(f"/catalog/{media_id}", headers=headers)


def find(client, headers, query, media_type):
    """Search the catalog, which saves the result so it has an id."""
    response = client.get("/catalog/search", params={"q": query, "type": media_type}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def life_is_strange(client, headers):
    return next(i for i in find(client, headers, "Life is Strange", "GAME") if i["title"] == "Life is Strange")


def blade_runner(client, headers):
    return find(client, headers, "Blade Runner", "MOVIE")[0]


def new_series(client, headers, fake, *, overview="An overview.", genres=("Drama",)):
    """A series with its own outside id. Returns the JSON of the catalog item with `fake_key`."""
    external_id = next(_outside_ids)
    fake.series[external_id] = copy.deepcopy(SERIES_DETAILS[70001])
    fake.series_info[external_id] = {"overview": overview, "genres": [{"id": n, "name": g} for n, g in enumerate(genres)]}
    response = client.post(
        "/media",
        json={"title": unique("series"), "media_type": "SERIES", "external_api_id": external_id},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return {**response.json(), "fake_key": external_id}


def give_genres(db, media_id, names):
    """Link a title to genres directly in the database."""
    item = db.get(MediaItem, media_id)
    for name in names:
        genre = db.query(Genre).filter(func.lower(Genre.name) == name.lower()).one_or_none()
        item.genres.append(genre or Genre(name=name))
    db.commit()


def tmdb_paths(fake):
    from urllib.parse import urlparse

    return [urlparse(call.url).path for call in fake.calls_to("tmdb")]


# ---------------------------------------------------------------- the rules for genre names
def test_genre_names_stay_as_the_source_wrote_them():
    names = ["Role-playing (RPG)", "Hack and slash/Beat 'em up", "Adventure"]

    assert genre_rules.normalize_genres(names) == tuple(names)


@pytest.mark.parametrize(
    "source, expected",
    [
        ("Action & Adventure", ("Action", "Adventure")),
        ("action & ADVENTURE", ("Action", "Adventure")),
        ("Sci-Fi & Fantasy", ("Science Fiction", "Fantasy")),
        ("War & Politics", ("War", "Politics")),
    ],
)
def test_the_joined_genres_of_tmdb_are_split_into_the_plain_names(source, expected):
    assert genre_rules.normalize_genres([source]) == expected


def test_a_genre_is_listed_once_in_the_order_of_the_source():
    names = ["Adventure", "Action & Adventure", "adventure", "Drama", "  Drama  "]

    assert genre_rules.normalize_genres(names) == ("Adventure", "Action", "Drama")


def test_wrong_genre_data_is_dropped():
    names = ["Drama", "", "   ", None, 7, "x" * 51, "Cr\x00ime", {"name": "Comedy"}]

    assert genre_rules.normalize_genres(names) == ("Drama", "Cr ime")


def test_at_most_ten_genres_are_kept():
    names = [f"Genre {n}" for n in range(30)]

    assert genre_rules.normalize_genres(names) == tuple(names[:10])


@pytest.mark.parametrize("entries", [None, "Drama", {"name": "Drama"}, 5, [None, 3, "x"], []])
def test_a_genre_list_in_an_unexpected_form_gives_no_genres(entries):
    assert genre_rules.genres_from_entries(entries) == ()


def test_genres_are_read_from_the_name_of_each_entry():
    entries = [{"id": 1, "name": "Adventure"}, {"id": 2}, {"id": 3, "name": "Indie"}]

    assert genre_rules.genres_from_entries(entries) == ("Adventure", "Indie")


def test_a_description_is_cleaned():
    assert clean_text("  Line one\r\nLine two\rLine three\x00\x07  ") == "Line one\nLine two\nLine three"
    assert clean_text("x" * (MAX_DESCRIPTION_LENGTH + 100)) == "x" * MAX_DESCRIPTION_LENGTH
    assert clean_text("") is None and clean_text("  \n ") is None and clean_text(None) is None
    assert clean_text(["not text"]) is None


# ---------------------------------------------------------------- the details of a title
def test_game_details_have_the_description_and_the_genres_of_igdb(client, auth_headers, fake_external_apis):
    game = life_is_strange(client, auth_headers)
    assert game["genres"] == []  # a search result does not carry them

    body = open_title(client, auth_headers, game["id"]).json()

    assert body["description"] == "A student discovers that she can rewind time."
    assert body["genres"] == ["Adventure", "Indie"]


def test_the_genres_show_in_search_results_after_the_details_were_opened(client, auth_headers, fake_external_apis):
    game = life_is_strange(client, auth_headers)
    open_title(client, auth_headers, game["id"])

    again = next(i for i in find(client, auth_headers, "Life is Strange", "GAME") if i["id"] == game["id"])

    assert again["genres"] == ["Adventure", "Indie"]
    assert "description" not in again  # a synopsis can be long, so lists do not carry it


def test_movie_details_have_the_description_and_the_genres_of_tmdb(client, auth_headers, fake_external_apis):
    movie = blade_runner(client, auth_headers)

    body = open_title(client, auth_headers, movie["id"]).json()

    assert body["description"] == "A blade runner hunts replicants."
    assert body["genres"] == ["Science Fiction", "Thriller"]
    assert tmdb_paths(fake_external_apis)[-1] == "/3/movie/80001"


def test_series_details_get_them_from_the_call_that_gives_the_seasons(client, auth_headers, fake_external_apis):
    series = new_series(client, auth_headers, fake_external_apis, overview="A teacher turns to crime.",
                        genres=("Drama", "Crime"))

    body = open_title(client, auth_headers, series["id"]).json()

    assert body["description"] == "A teacher turns to crime."
    assert body["genres"] == ["Crime", "Drama"]  # sorted by name
    assert {path.split("/")[2] for path in tmdb_paths(fake_external_apis)} == {"tv"}  # no extra call


def test_the_joined_names_of_a_series_become_plain_genres(client, auth_headers, fake_external_apis):
    series = new_series(client, auth_headers, fake_external_apis,
                        genres=("Action & Adventure", "Sci-Fi & Fantasy", "Drama"))

    body = open_title(client, auth_headers, series["id"]).json()

    assert body["genres"] == ["Action", "Adventure", "Drama", "Fantasy", "Science Fiction"]


def test_a_second_visit_comes_from_the_cache(client, auth_headers, fake_external_apis):
    game = life_is_strange(client, auth_headers)
    open_title(client, auth_headers, game["id"])
    calls = fake_external_apis.count()

    body = open_title(client, auth_headers, game["id"]).json()

    assert fake_external_apis.count() == calls
    assert body["genres"] == ["Adventure", "Indie"]


def test_a_title_with_a_different_source_has_a_cache_of_its_own(client, auth_headers, fake_external_apis):
    """A game and a movie can have the same outside id, because IGDB and TMDB number differently."""
    game = life_is_strange(client, auth_headers)
    open_title(client, auth_headers, game["id"])

    assert cache.get_json("omni:catalog:igdb:90001")["found"] is True
    assert cache.get_json("omni:catalog:tmdb_movie:90001") is None


def test_a_title_that_the_service_does_not_know_is_shown_without_them(client, auth_headers, fake_external_apis):
    movie = client.post("/media", json={"title": unique("movie"), "media_type": "MOVIE",
                                        "external_api_id": next(_outside_ids)}, headers=auth_headers).json()

    response = open_title(client, auth_headers, movie["id"])

    assert response.status_code == 200
    assert (response.json()["description"], response.json()["genres"]) == (None, [])


@pytest.mark.parametrize("service, media_type", [("igdb", "GAME"), ("tmdb", "MOVIE")])
def test_a_new_game_or_movie_is_still_shown_when_its_service_is_down(client, auth_headers, fake_external_apis, service, media_type):
    """NFR-04: these fields are a bonus. A failure must not take the title away."""
    title = client.post("/media", json={"title": unique("t"), "media_type": media_type,
                                        "external_api_id": next(_outside_ids)}, headers=auth_headers).json()
    fake_external_apis.fail(service, status=503, times=None)

    response = open_title(client, auth_headers, title["id"])

    assert response.status_code == 200
    assert (response.json()["description"], response.json()["genres"]) == (None, [])


@pytest.mark.parametrize("service, finder", [("igdb", life_is_strange), ("tmdb", blade_runner)])
def test_the_saved_copy_is_kept_when_the_service_goes_down(client, auth_headers, fake_external_apis, service, finder):
    title = finder(client, auth_headers)
    saved = open_title(client, auth_headers, title["id"]).json()
    assert saved["genres"]
    cache.clear_prefix("omni:catalog:")  # the cached copy has expired
    fake_external_apis.fail(service, status=503, times=None)

    response = open_title(client, auth_headers, title["id"])

    assert response.status_code == 200
    assert (response.json()["description"], response.json()["genres"]) == (saved["description"], saved["genres"])


def test_the_details_are_loaded_later_when_the_service_comes_back(client, auth_headers, fake_external_apis):
    external_id = next(_outside_ids)
    fake_external_apis.games.append({"id": external_id, "name": "Comes Back", "summary": "Back again.",
                                    "genres": [{"id": 5, "name": "Puzzle"}]})
    game = client.post("/media", json={"title": unique("t"), "media_type": "GAME",
                                       "external_api_id": external_id}, headers=auth_headers).json()
    fake_external_apis.fail("igdb", status=503, times=None)
    assert open_title(client, auth_headers, game["id"]).json()["genres"] == []
    fake_external_apis._scripted.clear()  # IGDB is back

    body = open_title(client, auth_headers, game["id"]).json()

    assert (body["description"], body["genres"]) == ("Back again.", ["Puzzle"])


def test_nothing_is_asked_when_the_service_is_not_set_up(client, auth_headers, fake_external_apis, monkeypatch):
    game = life_is_strange(client, auth_headers)
    calls = fake_external_apis.count()
    monkeypatch.setattr(catalog_service.igdb, "is_configured", lambda: False)

    assert open_title(client, auth_headers, game["id"]).status_code == 200
    assert fake_external_apis.count() == calls


# ---------------------------------------------------------------- what is saved
def test_an_empty_answer_never_erases_what_is_saved(client, auth_headers, fake_external_apis):
    game = life_is_strange(client, auth_headers)
    open_title(client, auth_headers, game["id"])
    fake_external_apis.games[0].pop("summary")
    fake_external_apis.games[0]["genres"] = []
    cache.clear_prefix("omni:catalog:")  # the cached copy has expired

    body = open_title(client, auth_headers, game["id"]).json()

    assert fake_external_apis.calls_to("igdb")[-1].body.startswith("fields summary,genres.name")
    assert body["description"] == "A student discovers that she can rewind time."
    assert body["genres"] == ["Adventure", "Indie"]


def test_a_changed_answer_replaces_the_description_and_the_genres(client, auth_headers, fake_external_apis, db):
    game = life_is_strange(client, auth_headers)
    open_title(client, auth_headers, game["id"])
    fake_external_apis.games[0]["summary"] = "A new synopsis."
    fake_external_apis.games[0]["genres"] = [{"id": 31, "name": "Adventure"}, {"id": 33, "name": "Puzzle"}]
    cache.clear_prefix("omni:catalog:")

    body = open_title(client, auth_headers, game["id"]).json()

    assert (body["description"], body["genres"]) == ("A new synopsis.", ["Adventure", "Puzzle"])
    assert db.query(Genre).filter(Genre.name == "Indie").count() == 1  # the genre stays, unlinked


def test_the_title_keeps_its_own_metadata(client, auth_headers, fake_external_apis, db):
    """Opening the details writes the description and genres, and nothing else about the title."""
    game = life_is_strange(client, auth_headers)

    body = open_title(client, auth_headers, game["id"]).json()

    for field in ("title", "poster_url", "release_date", "external_api_id"):
        assert body[field] == game[field]


def test_titles_share_one_row_for_a_genre_whatever_its_case(client, auth_headers, fake_external_apis, db):
    first = new_series(client, auth_headers, fake_external_apis, genres=("Mystery",))
    second = new_series(client, auth_headers, fake_external_apis, genres=("MYSTERY",))

    open_title(client, auth_headers, first["id"])
    assert open_title(client, auth_headers, second["id"]).json()["genres"] == ["Mystery"]

    assert db.query(Genre).filter(func.lower(Genre.name) == "mystery").count() == 1


def test_a_cache_entry_from_before_the_details_existed_is_loaded_again(client, auth_headers, fake_external_apis):
    series = new_series(client, auth_headers, fake_external_apis, overview="Fresh.", genres=("Drama",))
    old_entry = {"found": True, "seasons": []}  # the shape of the cache before description and genres
    cache.set_json(f"omni:catalog:tmdb_tv:{series['fake_key']}", old_entry, 60)

    body = open_title(client, auth_headers, series["id"]).json()

    assert (body["description"], body["genres"]) == ("Fresh.", ["Drama"])
    assert fake_external_apis.count("tmdb") >= 1


@pytest.mark.parametrize(
    "entry",
    [
        {"found": True, "description": 5, "genres": []},
        {"found": True, "description": "ok", "genres": "Drama"},
        {"found": True, "description": "ok", "genres": [1, 2]},
        {"found": True, "description": "ok"},
        {"description": "ok", "genres": []},
        "garbage",
    ],
)
def test_a_cache_entry_that_does_not_look_right_counts_as_a_miss(client, auth_headers, fake_external_apis, entry):
    game = life_is_strange(client, auth_headers)
    calls = fake_external_apis.count("igdb")
    cache.set_json("omni:catalog:igdb:90001", entry, 60)

    body = open_title(client, auth_headers, game["id"]).json()

    assert fake_external_apis.count("igdb") == calls + 1
    assert body["genres"] == ["Adventure", "Indie"]


def test_a_save_that_loses_a_race_for_a_new_genre_is_tried_again(client, auth_headers, fake_external_apis, monkeypatch):
    game = life_is_strange(client, auth_headers)
    real = catalog_service._save_details_once
    attempts = []

    def lose_the_first_time(db, media_id, details):
        attempts.append(1)
        if len(attempts) == 1:
            raise IntegrityError("INSERT INTO genres", {}, Exception("duplicate key"))
        return real(db, media_id, details)

    monkeypatch.setattr(catalog_service, "_save_details_once", lose_the_first_time)

    body = open_title(client, auth_headers, game["id"]).json()

    assert len(attempts) == 2
    assert body["genres"] == ["Adventure", "Indie"]


def test_a_save_that_keeps_failing_is_raised(db, monkeypatch):
    item = MediaItem(title=unique("t"), media_type=catalog_service.MediaType.GAME, external_api_id=next(_outside_ids))
    db.add(item)
    db.commit()

    def always(*args):
        raise IntegrityError("INSERT INTO genres", {}, Exception("duplicate key"))

    monkeypatch.setattr(catalog_service, "_save_details_once", always)

    with pytest.raises(IntegrityError):
        catalog_service._save_details(db, item.id, catalog_service.ExternalDetails("x", ("Drama",)))


# ---------------------------------------------------------------- the tables
def test_deleting_a_title_removes_its_links_and_keeps_the_genre(db):
    item = MediaItem(title=unique("t"), media_type=catalog_service.MediaType.GAME)
    db.add(item)
    db.commit()
    give_genres(db, item.id, ["Cascade Test Genre"])
    genre_id = db.query(Genre).filter(Genre.name == "Cascade Test Genre").one().id

    db.delete(item)
    db.commit()

    links = db.query(media_item_genres).filter(media_item_genres.c.genre_id == genre_id).count()
    assert links == 0
    assert db.query(Genre).filter(Genre.id == genre_id).count() == 1


def test_a_genre_name_is_unique(db):
    db.add(Genre(name="Unique Test Genre"))
    db.commit()
    db.add(Genre(name="Unique Test Genre"))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ---------------------------------------------------------------- the other endpoints
def test_a_new_title_has_no_genres(client, auth_headers):
    assert create_media(client, auth_headers)["genres"] == []


def test_the_create_and_update_schemas_do_not_take_genres_or_a_description(client, auth_headers):
    payload = {"title": unique("t"), "media_type": "GAME", "genres": ["Drama"], "description": "x"}

    created = client.post("/media", json=payload, headers=auth_headers).json()

    assert created["genres"] == []  # ignored: they only come from the outside services
    assert "description" not in created


def test_the_library_shows_the_genres_of_each_title(client, auth_headers, db):
    item = create_media(client, auth_headers)
    give_genres(db, item["id"], ["Puzzle", "Adventure"])
    add_to_library(client, auth_headers, item["id"])

    entry = next(e for e in client.get("/library", headers=auth_headers).json() if e["media_item_id"] == item["id"])

    assert entry["media_item"]["genres"] == ["Adventure", "Puzzle"]


def count_queries(call):
    count = []
    record = lambda *args, **kwargs: count.append(1)  # noqa: E731
    event.listen(engine, "before_cursor_execute", record)
    try:
        call()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return len(count)


def test_the_number_of_queries_of_the_library_does_not_grow_with_the_genres(client, auth_headers, db):
    def add_titles(how_many):
        for _ in range(how_many):
            item = create_media(client, auth_headers)
            give_genres(db, item["id"], ["Adventure", "Puzzle", "Indie"])
            add_to_library(client, auth_headers, item["id"])

    add_titles(1)
    few = count_queries(lambda: client.get("/library", headers=auth_headers))
    add_titles(4)
    many = count_queries(lambda: client.get("/library", headers=auth_headers))

    assert few == many


def test_the_number_of_queries_of_a_search_does_not_grow_with_the_genres(client, auth_headers, fake_external_apis, db):
    first = find(client, auth_headers, "Life is Strange", "GAME")
    one = count_queries(lambda: find(client, auth_headers, "Life is Strange", "GAME"))
    for item in first:
        give_genres(db, item["id"], ["Adventure", "Puzzle"])
    all_three = count_queries(lambda: find(client, auth_headers, "Life is Strange", "GAME"))

    assert len(first) == 3
    assert one == all_three
