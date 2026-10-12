import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# The database URL is read from the environment.
# SQLite is used locally for rapid development; set DATABASE_URL to switch
# to PostgreSQL in production, e.g.:
#   postgresql+psycopg2://user:password@localhost:5432/omnilog
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omnilog.db")

# check_same_thread is a SQLite-only option, so it must not be passed
# to other database engines.
connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Discards stale connections before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


# Dependency generator to manage database session lifecycle per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()