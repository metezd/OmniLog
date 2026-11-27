import logging
import os
import time
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

def normalize_database_url(url: str) -> str:
    """Give a PostgreSQL URL without a driver the driver of this app (psycopg2).

    Hosts such as Render hand out "postgresql://..." (some "postgres://..."). SQLAlchemy 2.1 would
    pick psycopg (version 3) for it, which is not installed, and the start fails with
    "No module named 'psycopg'". A URL that names a driver is left as it is.
    """
    parsed = make_url(url)
    if parsed.drivername in ("postgres", "postgresql"):
        return parsed.set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
    return url


# PostgreSQL only: the migrations, the CHECK constraints and pgvector are written for it (#371).
# There is no fallback to a local file any more: it hid a database that was not running.
_raw_url = os.getenv("DATABASE_URL", "").strip()
if not _raw_url:
    raise RuntimeError("Missing required environment variable: DATABASE_URL")
DATABASE_URL = normalize_database_url(_raw_url)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_LOCAL_HOSTS = (None, "", "localhost", "127.0.0.1", "::1")


class DatabaseUnreachableError(RuntimeError):
    """The PostgreSQL on this computer does not answer, so the API cannot work."""


def check_database(target: Optional[Engine] = None) -> None:
    """Try the database once at the start of the API.

    A PostgreSQL on this computer that does not answer stops the start with a clear message,
    because the API cannot work without it and the error of the first request would be hard to
    read. A remote database (a Docker service, Render) can start later, so it only gives a warning,
    and /health/ready answers 503 until it is there. The password is never written.
    """
    target = target if target is not None else engine
    url = target.url
    where = f"{url.host or 'localhost'}:{url.port or 5432}"
    try:
        with target.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        reason = type(getattr(exc, "orig", None) or exc).__name__
        if url.host in _LOCAL_HOSTS:
            raise DatabaseUnreachableError(
                f"PostgreSQL does not answer at {where} ({reason}). "
                "Start it with `docker compose up -d`, or set DATABASE_URL to a database that runs."
            ) from None
        logger.warning("PostgreSQL does not answer at %s (%s). /health/ready answers 503 until it does.", where, reason)


def connect_with_retry(target: Engine, attempts: int = 10, delay_seconds: float = 3.0, sleep=time.sleep):
    """Open a connection, and try again while the database cannot be reached yet.

    On Render the migrations start right when a new instance starts. Then the private name of the
    database (dpg-...) sometimes cannot be resolved for a few seconds, and the first try failed with
    "could not translate host name". The start command stopped, and Render marked the deploy as
    failed, although a second try 30 seconds later worked. Only OperationalError (no connection) is
    tried again; any other error is raised at once. The password is never written.
    """
    for attempt in range(1, attempts + 1):
        try:
            return target.connect()
        except OperationalError as exc:
            if attempt == attempts:
                raise
            reason = type(getattr(exc, "orig", None) or exc).__name__
            logger.warning(
                "The database does not answer yet (%s), try %s of %s. Trying again in %s seconds.",
                reason, attempt, attempts, delay_seconds,
            )
            sleep(delay_seconds)
    raise RuntimeError("attempts must be 1 or more")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
