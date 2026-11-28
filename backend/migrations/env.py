from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.config import DATABASE_URL
from app.core.database import Base, DATABASE_URL as ENGINE_URL, connect_with_retry, engine_options

# Importing the models registers every table on Base.metadata
import app.models.entities  # noqa: F401

config = context.config
if config.config_file_name is not None:
    # Keep the loggers of the app (imported above), so the retries of connect_with_retry are shown
    fileConfig(config.config_file_name, disable_existing_loggers=False)

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
    """Run migrations against the configured database.

    The connection is tried again for about 30 seconds, because on Render the database name may not
    be resolvable yet when a new instance starts.
    """
    # Its own engine without the statement_timeout of the API, so a migration may take longer
    # than a request (#432)
    engine = create_engine(ENGINE_URL, **engine_options(ENGINE_URL))
    with connect_with_retry(engine) as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
