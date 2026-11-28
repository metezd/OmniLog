import logging
import os
import time
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core import config

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

def engine_options(url: str) -> dict:
    """The pool settings of the engine (#411).

    On Render the database (Supabase) or a proxy between closes a connection that was idle for a
    while, and a Render instance that slept wakes up with such dead connections in its pool. The
    first request then failed or waited for a long time.

    - pool_pre_ping: each connection is tested with a cheap ping when it leaves the pool, and a
      dead one is replaced, so the request gets a working connection.
    - pool_recycle: a connection older than 300 seconds is closed and opened again.
    - TCP keepalives and connect_timeout (psycopg2 only): a connection that the network dropped
      fails in seconds instead of hanging until the frontend gives up.
    - pool_size, max_overflow and pool_timeout: the settings DB_POOL_SIZE, DB_MAX_OVERFLOW and
      DB_POOL_TIMEOUT (#432). A request that waits longer than the timeout gets 503 (app.core.errors).
    """
    options: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": config.DB_POOL_SIZE,
        "max_overflow": config.DB_MAX_OVERFLOW,
        "pool_timeout": config.DB_POOL_TIMEOUT,
    }
    if make_url(url).get_dialect().driver == "psycopg2":
        options["connect_args"] = {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    return options


def set_statement_timeout(target: Engine, milliseconds: int) -> None:
    """Give every new connection of the engine a statement_timeout (#432). 0 sets nothing.

    It is set with SET after the connection opens, not with the startup option `options`, because
    a connection pooler such as the one of Supabase may refuse startup options. The value stays for
    the whole session, also when the pool gives the connection out again.
    """
    if milliseconds <= 0:
        return

    @event.listens_for(target, "connect")
    def _set_timeout(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        try:
            # psycopg2 fills in the value on the client, so SET can take it as a parameter
            cursor.execute("SET statement_timeout = %s", (int(milliseconds),))
        finally:
            cursor.close()
        # SET opens a transaction in psycopg2. End it, so the connection starts clean.
        dbapi_connection.commit()


engine = create_engine(DATABASE_URL, **engine_options(DATABASE_URL))
set_statement_timeout(engine, config.DB_STATEMENT_TIMEOUT_MS)
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
