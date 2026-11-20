"""python -m app.sync [--type GAME|SERIES|MOVIE] [--id N ...] [--limit N] [--dry-run]

Manual sync of the catalog (UC-EP3-03, issue #125). It loads the description and genres (and the
seasons and episodes of a series) of every title that has an outside id and was never synced, for
example titles that went from a search into the library without being opened. Run it from the
backend container:

    docker compose exec backend python -m app.sync

The exit code is 0 when the run finished, 1 when loading raised an error for a title or the
database failed, and 2 for a wrong option.
"""
import argparse
import sys
from typing import Optional, Sequence

from app.core.database import SessionLocal
from app.models.entities import MediaType
from app.services import catalog_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.sync",
        description="Load the details of catalog titles that were never synced.",
    )
    parser.add_argument("--type", dest="media_type", choices=[t.value for t in MediaType], help="only this media type")
    parser.add_argument("--id", dest="media_ids", type=int, action="append", metavar="N", help="only this catalog id (repeatable)")
    parser.add_argument("--limit", type=int, metavar="N", help="stop after N titles")
    parser.add_argument("--dry-run", action="store_true", help="only count the titles, call no outside service")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _parser().parse_args(sys.argv[1:] if argv is None else list(argv))
    except SystemExit as exc:  # argparse exits for -h (0) and for a wrong option (2)
        return int(exc.code or 0)
    if args.limit is not None and args.limit < 1:
        print("--limit must be 1 or more", file=sys.stderr)
        return 2

    media_type = MediaType(args.media_type) if args.media_type else None
    db = SessionLocal()
    try:
        if args.dry_run:
            count = catalog_service.count_unsynced(db, media_type=media_type, media_ids=args.media_ids)
            if args.limit is not None:
                count = min(count, args.limit)
            print(f"Titles that would be synced: {count}")
            return 0
        report = catalog_service.sync_titles(
            db, media_type=media_type, media_ids=args.media_ids, limit=args.limit
        )
    except Exception as exc:
        print(f"The sync could not run. {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Titles selected: {report.selected}")
    print(f"Synced: {report.synced}")
    if report.unsynced:
        print(f"Not synced: {report.unsynced} (the outside service failed or does not know the title. See the log)")
    if report.errors:
        print(f"Errors: {report.errors} (see the log)")
    if report.not_selected:
        print(f"Not selected: {report.not_selected} id(s) are unknown, were added by hand or are already synced")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
