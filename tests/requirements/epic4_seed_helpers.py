"""Helpers for the tests of the seed file and of the decision points in title details."""
import itertools

from app.models.entities import MediaItem, MediaType
from app.seed.loader import apply_seed
from app.seed.schema import SeedFile

# The tests share one database, so every test gets outside ids of its own
_ids = itertools.count(2_000_000)


def seed_data(chapters=None, external_id=None, title="Seed Game"):
    """A seed document with one game. By default it has two chapters, and the first has a
    decision point with two options."""
    if chapters is None:
        chapters = [
            {
                "number": 1,
                "title": "One",
                "decision_points": [
                    {
                        "prompt": "Which way?",
                        "options": [{"label": "A", "text": "Left"}, {"label": "B", "text": "Right"}],
                    }
                ],
            },
            {"number": 2, "title": "Two"},
        ]
    return {
        "games": [
            {
                "external_api_id": external_id if external_id is not None else next(_ids),
                "title": title,
                "chapters": chapters,
            }
        ]
    }


def load(db, data):
    return apply_seed(db, SeedFile.model_validate(data))


def game_of(db, data):
    return (
        db.query(MediaItem)
        .filter(
            MediaItem.media_type == MediaType.GAME,
            MediaItem.external_api_id == data["games"][0]["external_api_id"],
        )
        .one_or_none()
    )


def next_external_id() -> int:
    """An outside id that no other test uses."""
    return next(_ids)
