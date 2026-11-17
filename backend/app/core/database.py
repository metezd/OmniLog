import socket
from sqlalchemy import CheckConstraint, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL as _CONFIG_DATABASE_URL

DATABASE_URL = _CONFIG_DATABASE_URL

# Automatically fall back to SQLite in local dev if localhost PostgreSQL (port 5432) is not running
if DATABASE_URL.startswith("postgres") and (
    "@localhost" in DATABASE_URL or "@127.0.0.1" in DATABASE_URL
):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", 5432)) != 0:
            DATABASE_URL = "sqlite:///./omnilog_local.db"

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Strip Postgres-only CHECK constraints (like position('@' in username)) when using SQLite
@event.listens_for(Base.metadata, "before_create")
def _remove_pg_check_constraints(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            table.constraints = {
                c for c in table.constraints if not isinstance(c, CheckConstraint)
            }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
