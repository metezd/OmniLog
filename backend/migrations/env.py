from logging.config import fileConfig

from alembic import context

from app.core.config import DATABASE_URL
from app.core.database import Base, engine

# Importing the models registers every table on Base.metadata
import app.models.entities  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares the database against these tables
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without a database connection."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database."""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
