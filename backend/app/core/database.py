from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite is used locally for rapid development.
# Only this URL will change when switching to PostgreSQL in production!
SQLALCHEMY_DATABASE_URL = "sqlite:///./omnilog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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