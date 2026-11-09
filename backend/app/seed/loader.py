"""Read the seed file and write it to the database.

The rules:
- The file is checked first (schema.py). A file with an error changes nothing.
- Everything is written in one transaction. When anything fails, nothing is saved.
- Running it again is safe. A row is found by its key and only changed when a value is different:
  the game by its IGDB id, a chapter by its number, a decision point by its position and an
  option by its label.
- Nothing is ever deleted. The choices of the users point to these rows (US-12), the same rule as
  for the episodes in catalog_service. A row that is in the database but not in the file is
  reported as a warning.
- A game that is already in the catalog keeps its title, poster and date. A search at IGDB has
  written them, and the seed must not overwrite them.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from pydantic import ValidationError
from sqlalchemy.orm import Session, selectinload

from app.models.entities import (
    Chapter,
    ChapterKind,
    DecisionOption,
    DecisionPoint,
    MediaItem,
    MediaType,
)
from app.seed.schema import SeedChapter, SeedDecisionPoint, SeedFile, SeedGame

DEFAULT_SEED_PATH = Path(__file__).with_name("game_chapters.json")


class SeedError(Exception):
    """The seed file cannot be used. The message says what to fix, one problem for each line."""


@dataclass
class SeedReport:
    games_created: int = 0
    chapters_created: int = 0
    chapters_updated: int = 0
    decision_points_created: int = 0
    decision_points_updated: int = 0
    options_created: int = 0
    options_updated: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(
            (
                self.games_created,
                self.chapters_created,
                self.chapters_updated,
                self.decision_points_created,
                self.decision_points_updated,
                self.options_created,
                self.options_updated,
            )
        )


def read_seed_file(path: Path = DEFAULT_SEED_PATH) -> SeedFile:
    """Read and check the file. Raises SeedError, with one line for each problem."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SeedError(f"{path}: the file does not exist") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise SeedError(f"{path}: the file cannot be read ({exc})") from None
    except json.JSONDecodeError as exc:
        raise SeedError(f"{path}: not valid JSON (line {exc.lineno}, column {exc.colno}: {exc.msg})") from None

    try:
        return SeedFile.model_validate(raw)
    except ValidationError as exc:
        lines = [
            f"{_format_location(error['loc'])}: {error['msg'].removeprefix('Value error, ')}"
            for error in exc.errors()
        ]
        raise SeedError("\n".join(lines)) from None


def _format_location(location: Sequence) -> str:
    """('games', 0, 'chapters', 2, 'number') becomes games[0].chapters[2].number"""
    text = ""
    for part in location:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text or "file"


def apply_seed(db: Session, seed: SeedFile) -> SeedReport:
    """Write the seed. Commits when everything worked and rolls back when anything failed."""
    report = SeedReport()
    try:
        for game in seed.games:
            _apply_game(db, game, report)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return report


def _apply_game(db: Session, game: SeedGame, report: SeedReport) -> None:
    item = (
        db.query(MediaItem)
        .filter(MediaItem.media_type == MediaType.GAME, MediaItem.external_api_id == game.external_api_id)
        .one_or_none()
    )
    if item is None:
        item = MediaItem(
            title=game.title,
            media_type=MediaType.GAME,
            poster_url=game.poster_url,
            release_date=game.release_date,
            external_api_id=game.external_api_id,
        )
        db.add(item)
        db.flush()  # gives the new row its id
        report.games_created += 1
    elif item.title.casefold() != game.title.casefold():
        # The most likely cause is a wrong id in the file
        report.warnings.append(
            f"IGDB id {game.external_api_id}: the catalog has the title {item.title!r}, "
            f"but the file says {game.title!r}. Check the id."
        )

    existing = {
        chapter.number: chapter
        for chapter in db.query(Chapter)
        .options(selectinload(Chapter.decision_points).selectinload(DecisionPoint.options))
        .filter(Chapter.media_item_id == item.id, Chapter.season_id.is_(None))
    }

    wanted = {chapter.number for chapter in game.chapters}
    for number in sorted(set(existing) - wanted):
        report.warnings.append(
            f"{game.title}: chapter {number} is in the database but not in the file. It is kept."
        )

    for seed_chapter in game.chapters:
        chapter = existing.get(seed_chapter.number)
        if chapter is None:
            chapter = Chapter(
                media_item_id=item.id,
                number=seed_chapter.number,
                kind=ChapterKind.CHAPTER,
                title=seed_chapter.title,
                release_date=seed_chapter.release_date,
                runtime_minutes=seed_chapter.runtime_minutes,
            )
            db.add(chapter)
            db.flush()
            report.chapters_created += 1
        else:
            report.chapters_updated += _update(
                chapter,
                title=seed_chapter.title,
                release_date=seed_chapter.release_date,
                runtime_minutes=seed_chapter.runtime_minutes,
            )
        _apply_decision_points(db, game, item, chapter, seed_chapter, report)


def _apply_decision_points(
    db: Session,
    game: SeedGame,
    item: MediaItem,
    chapter: Chapter,
    seed_chapter: SeedChapter,
    report: SeedReport,
) -> None:
    # decision_points is sorted by position and id. When rows share a position (the database
    # allows it), the first one is the one that the file talks about.
    by_position: dict[int, DecisionPoint] = {}
    for point in chapter.decision_points:
        by_position.setdefault(point.position, point)

    place = f"{game.title}, chapter {seed_chapter.number}"
    wanted_positions = set(range(1, len(seed_chapter.decision_points) + 1))
    for point in chapter.decision_points:
        if by_position.get(point.position) is not point or point.position not in wanted_positions:
            report.warnings.append(
                f"{place}: the decision point at position {point.position} (id {point.id}) is in "
                "the database but not in the file. It is kept."
            )

    for position, seed_point in enumerate(seed_chapter.decision_points, start=1):
        point = by_position.get(position)
        if point is None:
            point = DecisionPoint(
                chapter_id=chapter.id,
                media_item_id=item.id,
                prompt=seed_point.prompt,
                position=position,
            )
            db.add(point)
            db.flush()
            report.decision_points_created += 1
            options = {}
        else:
            report.decision_points_updated += _update(point, prompt=seed_point.prompt)
            options = {option.label: option for option in point.options}
        _apply_options(db, f"{place}, decision {position}", point, options, seed_point, report)


def _apply_options(
    db: Session,
    place: str,
    point: DecisionPoint,
    existing: dict[str, DecisionOption],
    seed_point: SeedDecisionPoint,
    report: SeedReport,
) -> None:
    wanted = {option.label for option in seed_point.options}
    for label in sorted(set(existing) - wanted):
        report.warnings.append(f"{place}: option {label} is in the database but not in the file. It is kept.")

    for seed_option in seed_point.options:
        option = existing.get(seed_option.label)
        if option is None:
            db.add(DecisionOption(decision_point_id=point.id, label=seed_option.label, text=seed_option.text))
            report.options_created += 1
        else:
            report.options_updated += _update(option, text=seed_option.text)


def _update(row: object, **values: Optional[object]) -> int:
    """Set the values that are different. Returns 1 when the row changed and 0 when it did not."""
    changed = False
    for name, value in values.items():
        if getattr(row, name) != value:
            setattr(row, name, value)
            changed = True
    return int(changed)
