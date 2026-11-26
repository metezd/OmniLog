"""scripts/import_lists.py: import a movie list from a CSV file through the API (#336).

The API is replaced by a fake that keeps lists in memory, so no server and no network are needed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import import_lists  # noqa: E402
from import_lists import (  # noqa: E402
    ApiError,
    CsvError,
    Film,
    import_list,
    match_film,
    normalize_title,
    read_films,
)


# ---------------------------------------------------------------- CSV
def write(tmp_path, text, name="films.csv", encoding="utf-8"):
    path = tmp_path / name
    path.write_text(text, encoding=encoding)
    return path


def test_reads_title_and_year(tmp_path):
    path = write(tmp_path, "title,year\nInception,2010\nArrival,2016\n")

    assert read_films(path) == [Film("Inception", 2010), Film("Arrival", 2016)]


def test_reads_a_letterboxd_export(tmp_path):
    # A Letterboxd export has the columns Date, Name, Year and Letterboxd URI
    path = write(
        tmp_path,
        "Date,Name,Year,Letterboxd URI\n2026-01-02,Parasite,2019,https://boxd.it/abc\n",
    )

    assert read_films(path) == [Film("Parasite", 2019)]


def test_column_names_ignore_case_spaces_and_a_bom(tmp_path):
    path = write(tmp_path, " Title , YEAR \nHer,2013\n", encoding="utf-8-sig")

    assert read_films(path) == [Film("Her", 2013)]


def test_a_title_with_a_comma_in_quotes(tmp_path):
    path = write(tmp_path, 'title,year\n"Crouching Tiger, Hidden Dragon",2000\n')

    assert read_films(path) == [Film("Crouching Tiger, Hidden Dragon", 2000)]


def test_an_empty_year_is_allowed(tmp_path):
    path = write(tmp_path, "title,year\nMetropolis,\n")

    assert read_films(path) == [Film("Metropolis", None)]


def test_empty_rows_are_skipped(tmp_path):
    path = write(tmp_path, "title,year\n\n,\nAlien,1979\n")

    assert read_films(path) == [Film("Alien", 1979)]


def test_a_title_column_is_required(tmp_path):
    path = write(tmp_path, "film,year\nAlien,1979\n")

    with pytest.raises(CsvError, match="title"):
        read_films(path)


@pytest.mark.parametrize("year", ["19x9", "1700", "3000"])
def test_a_wrong_year_names_the_line(tmp_path, year):
    path = write(tmp_path, f"title,year\nAlien,1979\nHeat,{year}\n")

    with pytest.raises(CsvError, match="line 3"):
        read_films(path)


def test_a_file_that_is_not_utf8_is_refused(tmp_path):
    path = tmp_path / "films.csv"
    path.write_bytes("title,year\nAmélie,2001\n".encode("latin-1"))

    with pytest.raises(CsvError, match="UTF-8"):
        read_films(path)


def test_a_missing_file_is_refused(tmp_path):
    with pytest.raises(CsvError, match="not found"):
        read_films(tmp_path / "nothing.csv")


# ---------------------------------------------------------------- matching
@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("The Matrix", "matrix"),
        ("Amélie", "Amelie"),
        ("Spider-Man: Into the Spider-Verse", "Spider Man Into the Spider Verse"),
        ("Fast & Furious", "Fast and Furious"),
        ("  Se7en ", "se7en"),
    ],
)
def test_titles_are_compared_without_case_accents_and_punctuation(a, b):
    assert normalize_title(a) == normalize_title(b)


def result(media_id, title, release_date):
    return {"id": media_id, "title": title, "release_date": release_date, "media_type": "MOVIE"}


def test_the_title_and_the_year_win():
    results = [
        result(1, "Dune", "1984-12-14"),
        result(2, "Dune", "2021-10-22"),
    ]

    assert match_film(Film("Dune", 2021), results)["id"] == 2


def test_a_year_one_off_is_accepted_when_nothing_is_exact():
    # Release dates differ by country, so a film from late 2019 can be listed as 2020
    results = [result(3, "1917", "2020-01-10")]

    assert match_film(Film("1917", 2019), results)["id"] == 3


def test_the_exact_year_beats_a_year_one_off():
    results = [result(4, "Heat", "1996-02-01"), result(5, "Heat", "1995-12-15")]

    assert match_film(Film("Heat", 1995), results)["id"] == 5


def test_another_title_is_not_taken():
    results = [result(6, "Inception: The Cobol Job", "2010-12-07")]

    assert match_film(Film("Inception", 2010), results) is None


def test_the_right_title_with_a_far_year_is_not_taken():
    results = [result(7, "Dune", "1984-12-14")]

    assert match_film(Film("Dune", 2021), results) is None


def test_without_a_year_the_first_title_match_is_taken():
    results = [result(8, "Metropolis", "1927-01-10"), result(9, "Metropolis", "2001-05-26")]

    assert match_film(Film("Metropolis", None), results)["id"] == 8


def test_a_result_without_a_date_matches_only_without_a_year():
    results = [result(10, "Alien", None)]

    assert match_film(Film("Alien", 1979), results) is None
    assert match_film(Film("Alien", None), results)["id"] == 10


def test_no_results_give_no_match():
    assert match_film(Film("Alien", 1979), []) is None


# ---------------------------------------------------------------- import with a fake API
class FakeApi:
    """The parts of the OmniLog API that the import uses, in memory."""

    def __init__(self, catalog, fail_search=()):
        self.catalog = catalog
        self.fail_search = set(fail_search)
        self.lists = {}
        self.calls = []

    def request(self, method, path, *, params=None, body=None):
        self.calls.append((method, path))
        if (method, path) == ("GET", "/catalog/search"):
            if params["q"] in self.fail_search:
                raise ApiError(503, "catalog unavailable")
            assert params["type"] == "MOVIE"
            return [item for item in self.catalog if item["title"].lower() == params["q"].lower()]
        if (method, path) == ("GET", "/lists"):
            rows = sorted(self.lists.values(), key=lambda item: item["id"])
            return rows[params["offset"]: params["offset"] + params["limit"]]
        if (method, path) == ("POST", "/lists"):
            new = {"id": len(self.lists) + 1, "name": body["name"], "items": []}
            self.lists[new["id"]] = new
            return new
        if method == "POST" and path.endswith("/items"):
            target = self.lists[int(path.split("/")[2])]
            if all(item["media_item_id"] != body["media_item_id"] for item in target["items"]):
                target["items"].append({"media_item_id": body["media_item_id"]})
            return {}
        raise AssertionError(f"unexpected call {method} {path}")


CATALOG = [
    result(101, "Inception", "2010-07-16"),
    result(102, "Arrival", "2016-11-11"),
    result(103, "Parasite", "2019-05-30"),
]


def run(api, films, **kwargs):
    lines = []
    report = import_list(api, "Favourites", films, delay=0, sleep=lambda _: None, log=lines.append, **kwargs)
    return report, lines


def test_creates_the_list_and_adds_the_films():
    api = FakeApi(CATALOG)

    report, _ = run(api, [Film("Inception", 2010), Film("Arrival", 2016)])

    assert [item["media_item_id"] for item in api.lists[1]["items"]] == [101, 102]
    assert (report.added, report.already, len(report.not_found), len(report.failed)) == (2, 0, 0, 0)


def test_a_film_that_is_not_found_is_listed_and_the_import_goes_on():
    api = FakeApi(CATALOG)

    report, lines = run(api, [Film("No Such Film", 1999), Film("Parasite", 2019)])

    assert [item["media_item_id"] for item in api.lists[1]["items"]] == [103]
    assert report.not_found == [Film("No Such Film", 1999)]
    assert any("not found" in line and "No Such Film" in line for line in lines)


def test_a_failed_search_is_listed_and_the_import_goes_on():
    api = FakeApi(CATALOG, fail_search={"Inception"})

    report, _ = run(api, [Film("Inception", 2010), Film("Arrival", 2016)])

    assert report.failed == [Film("Inception", 2010)]
    assert report.added == 1


def test_running_again_adds_nothing_twice():
    api = FakeApi(CATALOG)
    films = [Film("Inception", 2010), Film("Arrival", 2016)]
    run(api, films)

    report, _ = run(api, films)

    assert len(api.lists) == 1
    assert [item["media_item_id"] for item in api.lists[1]["items"]] == [101, 102]
    assert (report.added, report.already) == (0, 2)


def test_the_same_film_twice_in_the_file_is_added_once():
    api = FakeApi(CATALOG)

    report, _ = run(api, [Film("Arrival", 2016), Film("Arrival", 2016)])

    assert [item["media_item_id"] for item in api.lists[1]["items"]] == [102]
    assert (report.added, report.already) == (1, 1)


def test_an_existing_list_on_a_later_page_is_found():
    api = FakeApi(CATALOG)
    for number in range(1, 251):
        api.lists[number] = {"id": number, "name": f"list {number}", "items": []}
    api.lists[251] = {"id": 251, "name": "Favourites", "items": []}

    run(api, [Film("Inception", 2010)])

    assert len(api.lists) == 251
    assert api.lists[251]["items"] == [{"media_item_id": 101}]


def test_a_dry_run_writes_nothing():
    api = FakeApi(CATALOG)

    report, _ = run(api, [Film("Inception", 2010)], dry_run=True)

    assert api.lists == {}
    assert all(method == "GET" for method, _ in api.calls)
    assert report.added == 1


def test_searches_are_spaced_out():
    api = FakeApi(CATALOG)
    waits = []

    import_list(
        api, "Favourites", [Film("Inception", 2010), Film("Arrival", 2016), Film("Parasite", 2019)],
        delay=2.5, sleep=waits.append, log=lambda _: None,
    )

    # No wait before the first search, then one before each of the others
    assert waits == [2.5, 2.5]


def test_the_default_delay_keeps_under_the_search_limit():
    # The backend allows 30 searches a minute for each user (RATE_LIMIT_SEARCH)
    assert 60 / import_lists.DEFAULT_DELAY_SECONDS <= 30


# ---------------------------------------------------------------- credentials
def test_no_secret_is_written_in_the_script():
    text = (Path(import_lists.__file__)).read_text(encoding="utf-8")

    assert "OMNILOG_PASSWORD" in text
    assert "password=" not in text.replace("password=password", "")


def test_the_password_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("OMNILOG_USERNAME", "alice")
    monkeypatch.setenv("OMNILOG_PASSWORD", "s3cret-pass")

    args = import_lists.parse_args(["films.csv", "--list", "Favourites"])

    assert import_lists.credentials(args, prompt=lambda _: pytest.fail("no prompt")) == ("alice", "s3cret-pass")


def test_the_password_is_asked_for_when_it_is_not_set(monkeypatch):
    monkeypatch.delenv("OMNILOG_PASSWORD", raising=False)
    args = import_lists.parse_args(["films.csv", "--list", "Favourites", "--username", "bob"])

    assert import_lists.credentials(args, prompt=lambda _: "typed") == ("bob", "typed")


def test_the_api_url_comes_from_an_argument_or_the_environment(monkeypatch):
    monkeypatch.setenv("OMNILOG_API_URL", "https://api.example.com/")
    assert import_lists.parse_args(["f.csv", "--list", "L"]).api_url == "https://api.example.com/"
    assert import_lists.parse_args(["f.csv", "--list", "L", "--api-url", "http://localhost:8000"]).api_url == "http://localhost:8000"


def test_a_plain_http_url_is_allowed_only_for_this_computer():
    assert import_lists.check_api_url("http://localhost:8000") == "http://localhost:8000"
    assert import_lists.check_api_url("https://omnilog-api.onrender.com/") == "https://omnilog-api.onrender.com"
    with pytest.raises(ValueError, match="https"):
        import_lists.check_api_url("http://omnilog-api.onrender.com")
