"""Edge cases for the personal statistics (US-15, rules 6.1 to 6.4, BR-16, NFR-02).

Genres and chapters are saved in the database directly, which is shorter than going through the
outside services (see epic4_helpers.py and test_epic3_description_and_genres.py).
"""
import pytest

from app.models.entities import Genre, MediaItem, UserLibrary
from epic4_helpers import add_chapter
from helpers import add_to_library, create_media, new_credentials, register_and_login


@pytest.fixture
def other_headers(client):
    """A second user."""
    return register_and_login(client, new_credentials())


def get_stats(client, headers):
    response = client.get("/stats", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def add_titles(client, headers, media_type, count, rating=None):
    entries = []
    for _ in range(count):
        media = create_media(client, headers, media_type=media_type)
        entries.append(add_to_library(client, headers, media["id"], rating=rating))
    return entries


def give_genres(db, media_id, names):
    item = db.get(MediaItem, media_id)
    for name in names:
        genre = db.query(Genre).filter(Genre.name == name).one_or_none()
        item.genres.append(genre or Genre(name=name))
    db.commit()


def log_minutes(client, db, headers, entry, minutes):
    """Log playtime on a new chapter of the title of the entry."""
    chapter_id = add_chapter(db, entry["media_item_id"], number=entry["media_item_id"])
    response = client.post(
        f"/library/{entry['id']}/chapters/{chapter_id}/playtime",
        json={"minutes": minutes},
        headers=headers,
    )
    assert response.status_code == 201, response.text


# ---------------------------------------------------------------- access
def test_stats_need_a_login(client):
    assert client.get("/stats").status_code == 401


def test_a_bad_token_is_refused(client):
    response = client.get("/stats", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401


# ---------------------------------------------------------------- the shape of the answer
def test_an_empty_library_has_every_field_with_zero_values(client, auth_headers):
    stats = get_stats(client, auth_headers)

    assert stats["total_items"] == 0
    assert stats["media_split"] == {"GAME": 0, "SERIES": 0, "MOVIE": 0}
    assert stats["rating_distribution"] == {str(value): 0 for value in range(1, 11)}
    assert stats["genre_breakdown"] == []
    assert stats["playtime"] == {"total_minutes": 0, "histogram": []}


def test_the_media_split_always_lists_every_media_type(client, auth_headers):
    add_titles(client, auth_headers, "MOVIE", 1)

    assert get_stats(client, auth_headers)["media_split"] == {"GAME": 0, "SERIES": 0, "MOVIE": 100}


# ---------------------------------------------------------------- media split
def test_total_items_counts_every_entry(client, auth_headers):
    add_titles(client, auth_headers, "GAME", 2)
    add_titles(client, auth_headers, "SERIES", 1)

    assert get_stats(client, auth_headers)["total_items"] == 3


@pytest.mark.parametrize(
    "games, series, movies, expected",
    [
        (1, 1, 1, {"GAME": 34, "SERIES": 33, "MOVIE": 33}),
        (1, 2, 0, {"GAME": 33, "SERIES": 67, "MOVIE": 0}),
        (2, 1, 0, {"GAME": 67, "SERIES": 33, "MOVIE": 0}),
        (3, 1, 0, {"GAME": 75, "SERIES": 25, "MOVIE": 0}),
        (1, 1, 5, {"GAME": 14, "SERIES": 14, "MOVIE": 72}),
    ],
)
def test_the_percents_are_whole_numbers_that_add_up_to_100(client, auth_headers, games, series, movies, expected):
    add_titles(client, auth_headers, "GAME", games)
    add_titles(client, auth_headers, "SERIES", series)
    add_titles(client, auth_headers, "MOVIE", movies)

    split = get_stats(client, auth_headers)["media_split"]

    assert split == expected
    assert sum(split.values()) == 100


# ---------------------------------------------------------------- rating distribution
def test_every_rating_from_1_to_10_has_a_key(client, auth_headers):
    for rating in (1, 10):
        add_titles(client, auth_headers, "GAME", 1, rating=rating)

    distribution = get_stats(client, auth_headers)["rating_distribution"]

    assert list(distribution) == [str(value) for value in range(1, 11)]
    assert distribution["1"] == 1 and distribution["10"] == 1
    assert sum(distribution.values()) == 2


def test_entries_without_a_rating_are_not_counted_in_the_distribution(client, auth_headers):
    add_titles(client, auth_headers, "GAME", 2)
    add_titles(client, auth_headers, "GAME", 1, rating=7)

    stats = get_stats(client, auth_headers)

    assert stats["total_items"] == 3
    assert sum(stats["rating_distribution"].values()) == 1


def test_a_rating_that_was_removed_leaves_the_distribution(client, auth_headers):
    [entry] = add_titles(client, auth_headers, "GAME", 1, rating=9)
    assert get_stats(client, auth_headers)["rating_distribution"]["9"] == 1

    client.patch(f"/library/{entry['id']}", json={"rating": None}, headers=auth_headers)

    assert get_stats(client, auth_headers)["rating_distribution"]["9"] == 0


@pytest.mark.parametrize("stored, bucket", [(7.5, "8"), (7.4, "7"), (1.0, "1"), (9.5, "10"), (10.0, "10")])
def test_a_rating_with_a_decimal_is_rounded_and_halves_go_up(client, auth_headers, db, stored, bucket):
    [entry] = add_titles(client, auth_headers, "GAME", 1)
    db.query(UserLibrary).filter(UserLibrary.id == entry["id"]).update({"rating": stored})
    db.commit()

    distribution = get_stats(client, auth_headers)["rating_distribution"]

    assert distribution[bucket] == 1
    assert sum(distribution.values()) == 1


# ---------------------------------------------------------------- genre breakdown
def test_a_title_with_two_genres_is_counted_once_for_each(client, auth_headers, db):
    [entry] = add_titles(client, auth_headers, "GAME", 1)
    give_genres(db, entry["media_item_id"], ["Puzzle", "Adventure"])

    stats = get_stats(client, auth_headers)

    assert stats["genre_breakdown"] == [
        {"genre": "Adventure", "count": 1},
        {"genre": "Puzzle", "count": 1},
    ]
    assert stats["total_items"] == 1


def test_genres_are_sorted_by_count_and_then_by_name(client, auth_headers, db):
    first, second, third = add_titles(client, auth_headers, "GAME", 3)
    give_genres(db, first["media_item_id"], ["Drama", "Action"])
    give_genres(db, second["media_item_id"], ["Drama", "Zombies"])
    give_genres(db, third["media_item_id"], ["Drama"])

    breakdown = get_stats(client, auth_headers)["genre_breakdown"]

    assert breakdown == [
        {"genre": "Drama", "count": 3},
        {"genre": "Action", "count": 1},
        {"genre": "Zombies", "count": 1},
    ]


def test_a_genre_groups_titles_of_different_media_types(client, auth_headers, db):
    [game] = add_titles(client, auth_headers, "GAME", 1)
    [series] = add_titles(client, auth_headers, "SERIES", 1)
    give_genres(db, game["media_item_id"], ["Mystery"])
    give_genres(db, series["media_item_id"], ["Mystery"])

    assert get_stats(client, auth_headers)["genre_breakdown"] == [{"genre": "Mystery", "count": 2}]


def test_titles_without_genres_do_not_appear_in_the_breakdown(client, auth_headers):
    add_titles(client, auth_headers, "GAME", 2)

    assert get_stats(client, auth_headers)["genre_breakdown"] == []


def test_only_genres_of_titles_in_my_library_are_counted(client, auth_headers, other_headers, db):
    mine = create_media(client, auth_headers)
    theirs = create_media(client, other_headers)
    give_genres(db, mine["id"], ["Racing"])
    give_genres(db, theirs["id"], ["Racing", "Sport"])
    add_to_library(client, auth_headers, mine["id"])
    add_to_library(client, other_headers, theirs["id"])

    assert get_stats(client, auth_headers)["genre_breakdown"] == [{"genre": "Racing", "count": 1}]


# ---------------------------------------------------------------- playtime
def test_titles_without_playtime_are_in_the_first_bucket(client, auth_headers):
    add_titles(client, auth_headers, "GAME", 4)

    assert get_stats(client, auth_headers)["playtime"] == {
        "total_minutes": 0,
        "histogram": [{"bucket": "0-5h", "count": 4}],
    }


def test_the_playtime_of_all_chapters_of_a_title_is_added_up(client, auth_headers, db):
    [entry] = add_titles(client, auth_headers, "GAME", 1)
    first = add_chapter(db, entry["media_item_id"], number=1)
    second = add_chapter(db, entry["media_item_id"], number=2)
    for chapter_id, minutes in ((first, 90), (first, 30), (second, 60)):
        url = f"/library/{entry['id']}/chapters/{chapter_id}/playtime"
        assert client.post(url, json={"minutes": minutes}, headers=auth_headers).status_code == 201

    playtime = get_stats(client, auth_headers)["playtime"]

    assert playtime["total_minutes"] == 180
    assert playtime["histogram"] == [{"bucket": "0-5h", "count": 1}]


def test_titles_are_put_in_buckets_of_five_hours(client, auth_headers, db):
    short, middle, long, none = add_titles(client, auth_headers, "GAME", 4)
    log_minutes(client, db, auth_headers, short, 120)  # 2 h
    log_minutes(client, db, auth_headers, middle, 420)  # 7 h
    log_minutes(client, db, auth_headers, long, 900)  # 15 h

    playtime = get_stats(client, auth_headers)["playtime"]

    assert playtime["total_minutes"] == 120 + 420 + 900
    assert playtime["histogram"] == [
        {"bucket": "0-5h", "count": 2},  # the 2 h title and the title with no playtime
        {"bucket": "5-10h", "count": 1},
        {"bucket": "10-15h", "count": 0},  # an empty bucket stays, so a chart has no gap
        {"bucket": "15-20h", "count": 1},
    ]
    assert sum(item["count"] for item in playtime["histogram"]) == 4


@pytest.mark.parametrize("minutes, bucket", [(299, "0-5h"), (300, "5-10h"), (599, "5-10h"), (600, "10-15h")])
def test_a_bucket_includes_its_lower_edge(client, auth_headers, db, minutes, bucket):
    [entry] = add_titles(client, auth_headers, "GAME", 1)
    log_minutes(client, db, auth_headers, entry, minutes)

    histogram = get_stats(client, auth_headers)["playtime"]["histogram"]

    assert [item["bucket"] for item in histogram if item["count"] == 1] == [bucket]


def test_the_playtime_of_a_removed_title_is_gone(client, auth_headers, db):
    [entry] = add_titles(client, auth_headers, "GAME", 1)
    log_minutes(client, db, auth_headers, entry, 120)
    assert get_stats(client, auth_headers)["playtime"]["total_minutes"] == 120

    assert client.delete(f"/library/{entry['id']}", headers=auth_headers).status_code == 204

    stats = get_stats(client, auth_headers)
    assert stats["total_items"] == 0
    assert stats["playtime"] == {"total_minutes": 0, "histogram": []}


# ---------------------------------------------------------------- BR-16: only my own library
def test_the_library_of_another_user_is_not_counted(client, auth_headers, other_headers, db):
    add_titles(client, auth_headers, "GAME", 1, rating=8)
    [theirs] = add_titles(client, other_headers, "SERIES", 3, rating=2)[:1]
    log_minutes(client, db, other_headers, theirs, 600)

    stats = get_stats(client, auth_headers)

    assert stats["total_items"] == 1
    assert stats["media_split"] == {"GAME": 100, "SERIES": 0, "MOVIE": 0}
    assert stats["rating_distribution"]["2"] == 0
    assert stats["playtime"]["total_minutes"] == 0


def test_two_users_with_the_same_title_each_see_their_own_numbers(client, auth_headers, other_headers):
    media = create_media(client, auth_headers)
    add_to_library(client, auth_headers, media["id"], rating=9)
    add_to_library(client, other_headers, media["id"], rating=3)

    assert get_stats(client, auth_headers)["rating_distribution"]["9"] == 1
    assert get_stats(client, auth_headers)["rating_distribution"]["3"] == 0
    assert get_stats(client, other_headers)["rating_distribution"]["3"] == 1


# ---------------------------------------------------------------- always current
def test_the_numbers_follow_changes_at_once(client, auth_headers):
    """There is no cache yet, so a change shows in the next request."""
    [entry] = add_titles(client, auth_headers, "GAME", 1, rating=5)
    assert get_stats(client, auth_headers)["rating_distribution"]["5"] == 1

    client.patch(f"/library/{entry['id']}", json={"rating": 6}, headers=auth_headers)

    distribution = get_stats(client, auth_headers)["rating_distribution"]
    assert distribution["5"] == 0 and distribution["6"] == 1
