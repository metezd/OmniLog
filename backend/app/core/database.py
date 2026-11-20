import os
import socket
from sqlalchemy import create_engine, CheckConstraint, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omnilog_local.db")

# Fall back to SQLite only for a PostgreSQL on this machine that is not running (local development).
# A remote host (a Docker service such as "db", a managed database) is never replaced: a wrong or
# unreachable address must fail loudly, and the migrations are written for PostgreSQL.
if DATABASE_URL.startswith("postgres"):
    _url = make_url(DATABASE_URL)
    if _url.host in (None, "", "localhost", "127.0.0.1", "::1"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", _url.port or 5432)) != 0:
                DATABASE_URL = "sqlite:///./omnilog_local.db"

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
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