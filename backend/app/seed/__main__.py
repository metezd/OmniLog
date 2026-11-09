"""python -m app.seed [path]  loads the chapters and decision points of games.

Without a path the file next to this module is used. The exit code is 0 when the load worked and 1
when the file was refused or the database failed.
"""
import sys
from pathlib import Path
from typing import Optional, Sequence

from app.core.database import SessionLocal
from app.seed.loader import DEFAULT_SEED_PATH, SeedError, apply_seed, read_seed_file


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1 or (args and args[0] in {"-h", "--help"}):
        print("Usage: python -m app.seed [path-to-json]", file=sys.stderr)
        return 0 if args and args[0] in {"-h", "--help"} else 1
    path = Path(args[0]) if args else DEFAULT_SEED_PATH

    try:
        seed = read_seed_file(path)
    except SeedError as exc:
        print(f"The seed file was refused. Nothing was saved.\n{exc}", file=sys.stderr)
        return 1

    if not seed.games:
        print(f"{path} has no games. Nothing to do.")
        return 0

    db = SessionLocal()
    try:
        report = apply_seed(db, seed)
    except Exception as exc:  # the transaction is already rolled back
        print(f"The seed could not be saved. Nothing was saved. {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Games created: {report.games_created}")
    print(f"Chapters created: {report.chapters_created}, updated: {report.chapters_updated}")
    print(f"Decision points created: {report.decision_points_created}, updated: {report.decision_points_updated}")
    print(f"Options created: {report.options_created}, updated: {report.options_updated}")
    if not report.changed:
        print("The database already matched the file.")
    for warning in report.warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
