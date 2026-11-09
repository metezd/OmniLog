"""Genre names from IGDB and TMDB, made the same before they are saved (process 3.4, rule 3.7).

Most names stay as the source wrote them. Only the few names that would otherwise hide that two
titles share a genre are changed: TMDB joins genres in some TV names ("Action & Adventure"), and
those are split into the plain names that the other sources use. To add a rule, add a line to
_ALIASES.
"""
import logging
import re
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Limits of the genres.name column, and of the genres of one title
MAX_GENRE_LENGTH = 50
MAX_GENRES = 10
# Never look at more entries than this, however many an outside service sends
_MAX_ENTRIES = 50

# Lower case source name -> the names that it stands for
_ALIASES: dict[str, tuple[str, ...]] = {
    "action & adventure": ("Action", "Adventure"),
    "sci-fi & fantasy": ("Science Fiction", "Fantasy"),
    "war & politics": ("War", "Politics"),
}

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def normalize_genres(names: Iterable[Any]) -> tuple[str, ...]:
    """Clean the names, apply the aliases and drop the repeats, keeping the order of the source.

    A name that is not text, is empty, or is longer than a genre name can be is wrong data and is
    dropped. At most MAX_GENRES are kept.
    """
    result: list[str] = []
    seen: set[str] = set()
    for raw in names:
        if not isinstance(raw, str):
            continue
        name = " ".join(_CONTROL_CHARACTERS.sub(" ", raw).split())
        if not name:
            continue
        for canonical in _ALIASES.get(name.casefold(), (name,)):
            if len(canonical) > MAX_GENRE_LENGTH:
                logger.warning("A genre name of %s characters was dropped", len(canonical))
                continue
            if canonical.casefold() not in seen:
                seen.add(canonical.casefold())
                result.append(canonical)
    return tuple(result[:MAX_GENRES])


def genres_from_entries(entries: Any) -> tuple[str, ...]:
    """Normalize a list such as [{"id": 12, "name": "Adventure"}], the form of IGDB and TMDB."""
    if not isinstance(entries, list):
        return ()
    return normalize_genres(
        entry.get("name") for entry in entries[:_MAX_ENTRIES] if isinstance(entry, dict)
    )
