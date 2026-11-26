#!/usr/bin/env python3
"""Import a movie list from a CSV file into OmniLog (#336).

The script reads a CSV file with a title and a year on each row, finds each film with the catalog
search of the API (GET /catalog/search), creates a custom list (POST /lists) and adds the films to
it (POST /lists/{id}/items). It uses only the public API, so it works against a local backend and
against the one on Render. It does not read any website.

The CSV needs a column `title` (or `Name`, as in a Letterboxd export) and may have a column `year`
(or `Year`). Other columns are ignored, so the file that Letterboxd exports works as it is.

    export OMNILOG_USERNAME=alice
    export OMNILOG_PASSWORD='...'            # or leave it out and type it when asked
    python scripts/import_lists.py --list "Favourites" < films.csv
    python scripts/import_lists.py --list "Favourites" --api-url https://omnilog-api.onrender.com < films.csv

The CSV comes in on standard input, so the script opens no file path of its own: another program
that starts it cannot make it read any other file.

Running it again is safe: an existing list with the same name is used, and a film that is already
in the list is not added twice. A film that is not found is listed at the end and does not stop the
import. Only the Python standard library is used, so no virtual environment is needed.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

DEFAULT_API_URL = "http://localhost:8000"

# The backend allows 30 searches a minute for each user (RATE_LIMIT_SEARCH), so 2.5 seconds
# between searches stays under it, with room for a second client of the same user
DEFAULT_DELAY_SECONDS = 2.5

# A 429 answer says how long to wait (Retry-After). The import waits at most this long and tries
# at most this many times before it counts the film as failed
MAX_RETRY_WAIT_SECONDS = 60
MAX_TRIES = 3

TIMEOUT_SECONDS = 60  # a sleeping free backend on Render can need about a minute for its first answer
LIST_PAGE_SIZE = 200
MIN_YEAR, MAX_YEAR = 1870, 2100

TITLE_COLUMNS = ("title", "name")
YEAR_COLUMNS = ("year",)


class CsvError(Exception):
    """The CSV file cannot be read. The message says which line or column."""


class ApiError(Exception):
    """The API answered with an error, or could not be reached (status 0)."""

    def __init__(self, status: int, message: str, retry_after: Optional[float] = None):
        super().__init__(f"{status} {message}" if status else message)
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class Film:
    title: str
    year: Optional[int]

    def __str__(self) -> str:
        return f"{self.title} ({self.year})" if self.year else self.title


@dataclass
class Report:
    added: int = 0
    already: int = 0
    not_found: list[Film] = field(default_factory=list)
    failed: list[Film] = field(default_factory=list)


# ---------------------------------------------------------------- CSV
def _column(header: list[str], names: tuple[str, ...]) -> Optional[int]:
    cleaned = [name.strip().lower() for name in header]
    for name in names:
        if name in cleaned:
            return cleaned.index(name)
    return None


def read_films(data: bytes, source: str = "standard input") -> list[Film]:
    """Read the films of a CSV file. Empty rows are skipped, a wrong year stops with the line."""
    try:
        # utf-8-sig also reads a file that starts with a byte order mark (Excel writes one)
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvError(f"{source}: the file is not UTF-8. Save it as UTF-8 and try again") from exc
    rows = list(csv.reader(io.StringIO(text, newline="")))
    path = source

    if not rows:
        raise CsvError(f"{path}: the file is empty")
    header, body = rows[0], rows[1:]
    title_at = _column(header, TITLE_COLUMNS)
    if title_at is None:
        raise CsvError(f"{path}: no column 'title' (or 'Name') in the first line")
    year_at = _column(header, YEAR_COLUMNS)

    films = []
    for number, row in enumerate(body, start=2):
        title = row[title_at].strip() if title_at < len(row) else ""
        if not title:
            continue
        raw_year = row[year_at].strip() if year_at is not None and year_at < len(row) else ""
        year = None
        if raw_year:
            if not raw_year.isdigit() or not MIN_YEAR <= int(raw_year) <= MAX_YEAR:
                raise CsvError(f"{path}, line {number}: '{raw_year}' is not a year")
            year = int(raw_year)
        films.append(Film(title, year))
    return films


# ---------------------------------------------------------------- matching
def normalize_title(title: str) -> str:
    """Lower case, no accents, no punctuation, '&' as 'and', no leading 'the'."""
    text = unicodedata.normalize("NFKD", title)
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"[^0-9a-z]+", " ", text).strip()
    return re.sub(r"^the ", "", text)


def _year_of(item: dict[str, Any]) -> Optional[int]:
    date = item.get("release_date") or ""
    return int(date[:4]) if len(date) >= 4 and date[:4].isdigit() else None


def match_film(film: Film, results: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The search result that is this film, or None.

    The title must be the same (see normalize_title). With a year, the same year wins, then a
    year one off (release dates differ by country). A result without a date is taken only when
    the CSV has no year either. Without a year, the first result with the same title is taken.
    """
    wanted = normalize_title(film.title)
    same_title = [item for item in results if normalize_title(item.get("title", "")) == wanted]
    if film.year is None:
        return same_title[0] if same_title else None
    for distance in (0, 1):
        for item in same_title:
            year = _year_of(item)
            if year is not None and abs(year - film.year) == distance:
                return item
    return None


# ---------------------------------------------------------------- API
class Api:
    """A small JSON client for the OmniLog API with a Bearer token."""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, *, params: Optional[dict] = None, body: Any = None) -> Any:
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310 (the URL is checked by check_api_url)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as answer:  # noqa: S310
                raw = answer.read()
        except urllib.error.HTTPError as exc:
            retry = exc.headers.get("Retry-After")
            detail = _detail(exc.read())
            raise ApiError(exc.code, detail, float(retry) if retry and retry.isdigit() else None) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ApiError(0, f"cannot reach {self.base_url}: {getattr(exc, 'reason', exc)}") from exc
        return json.loads(raw) if raw else None


def _detail(raw: bytes) -> str:
    try:
        detail = json.loads(raw).get("detail")
    except (ValueError, AttributeError):
        return "error"
    return detail if isinstance(detail, str) else "error"


def log_in(api: Api, username: str, password: str) -> None:
    answer = api.request("POST", "/auth/login", body={"username": username, "password": password})
    api.token = answer["access_token"]


def _find_list(api: Any, name: str) -> Optional[dict[str, Any]]:
    offset = 0
    while True:
        page = api.request("GET", "/lists", params={"limit": LIST_PAGE_SIZE, "offset": offset})
        for item in page:
            if item["name"] == name:
                return item
        if len(page) < LIST_PAGE_SIZE:
            return None
        offset += len(page)


def _search(api: Any, film: Film, sleep: Callable[[float], None]) -> list[dict[str, Any]]:
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return api.request("GET", "/catalog/search", params={"q": film.title, "type": "MOVIE"})
        except ApiError as exc:
            if exc.status != 429 or attempt == MAX_TRIES:
                raise
            sleep(min(exc.retry_after or 30, MAX_RETRY_WAIT_SECONDS))
    return []


# ---------------------------------------------------------------- import
def import_list(
    api: Any,
    list_name: str,
    films: list[Film],
    *,
    delay: float = DEFAULT_DELAY_SECONDS,
    dry_run: bool = False,
    sleep: Optional[Callable[[float], None]] = None,
    log: Callable[[str], None] = print,
) -> Report:
    """Find each film and add it to the list `list_name`, which is created when it is missing.

    With dry_run nothing is written: the films are only searched and matched.
    """
    # Looked up at call time, not when the module loads
    sleep = sleep or time.sleep
    report = Report()
    target = _find_list(api, list_name)
    if target is None and not dry_run:
        target = api.request("POST", "/lists", body={"name": list_name})
        log(f"Created the list '{list_name}'")
    elif target is not None:
        log(f"Using the existing list '{list_name}'")
    present = {item["media_item_id"] for item in (target or {}).get("items", [])}

    for index, film in enumerate(films):
        if index and delay:
            sleep(delay)
        try:
            found = match_film(film, _search(api, film, sleep))
        except ApiError as exc:
            report.failed.append(film)
            log(f"failed     {film}: {exc}")
            continue
        if found is None:
            report.not_found.append(film)
            log(f"not found  {film}")
            continue
        if found["id"] in present:
            report.already += 1
            log(f"in list    {film}")
            continue
        if not dry_run:
            api.request("POST", f"/lists/{target['id']}/items", body={"media_item_id": found["id"]})
        present.add(found["id"])
        report.added += 1
        log(f"{'would add' if dry_run else 'added':<10} {film}")
    return report


# ---------------------------------------------------------------- command line
def check_api_url(url: str) -> str:
    """Only https, except for this computer, because the password and the token are sent."""
    parsed = urllib.parse.urlparse(url.strip())
    local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"'{url}' is not an http or https address")
    if parsed.scheme != "https" and not local:
        raise ValueError(f"use https for '{parsed.hostname}': the password would be sent in clear text")
    return url.strip().rstrip("/")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import a movie list from a CSV file (columns title and year, or a Letterboxd export). "
            "The file comes in on standard input: import_lists.py --list NAME < films.csv"
        ),
        epilog=(
            "The password is read from OMNILOG_PASSWORD, or asked for when it is not set. "
            "It is never an argument, so it does not show up in the shell history."
        ),
    )
    parser.add_argument("--list", required=True, dest="list_name", help="the name of the list")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("OMNILOG_API_URL", DEFAULT_API_URL),
        help=f"the address of the API (default: OMNILOG_API_URL or {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("OMNILOG_USERNAME"),
        help="the username or email (default: OMNILOG_USERNAME)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"seconds between two searches (default {DEFAULT_DELAY_SECONDS}, the backend allows 30 a minute)",
    )
    parser.add_argument("--dry-run", action="store_true", help="only search and match, write nothing")
    return parser.parse_args(argv)


def credentials(args: argparse.Namespace, prompt: Callable[[str], str] = getpass.getpass) -> tuple[str, str]:
    username = args.username or input("Username or email: ").strip()
    password = os.environ.get("OMNILOG_PASSWORD") or prompt("Password: ")
    return username, password


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if sys.stdin.isatty():
        print("error: send the CSV file on standard input, for example: --list NAME < films.csv", file=sys.stderr)
        return 2
    try:
        films = read_films(sys.stdin.buffer.read())
        api_url = check_api_url(args.api_url)
    except (CsvError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not films:
        print("error: the file has no films", file=sys.stderr)
        return 2
    if args.delay < 0:
        print("error: --delay cannot be negative", file=sys.stderr)
        return 2

    api = Api(api_url)
    username, password = credentials(args)
    try:
        log_in(api, username, password)
        print(f"{len(films)} films into '{args.list_name}' on {api_url}")
        report = import_list(api, args.list_name, films, delay=args.delay, dry_run=args.dry_run)
    except ApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"\nDone: {report.added} {'would be added' if args.dry_run else 'added'}, "
        f"{report.already} already in the list, {len(report.not_found)} not found, {len(report.failed)} failed."
    )
    for film in report.not_found:
        print(f"  not found: {film}")
    for film in report.failed:
        print(f"  failed:    {film} (run the script again later)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
