"""Reserved migration revision for the future US-12 decision tables.

The decision models and API are not implemented in this pull request yet. Creating
``user_decisions`` here while the tables are absent from ``Base.metadata`` makes
``alembic check`` report the tables and index as unexpected removals, which fails
both the backend and Docker Compose CI jobs.

Keep this revision as a no-op so the migration chain remains linear. Add the real
US-12 schema in a later migration together with its SQLAlchemy models.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-18
"""

# Revision identifiers used by Alembic
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Reserve revision 0008 until the US-12 models are implemented."""
    pass


def downgrade() -> None:
    """There is nothing to downgrade for this reserved revision."""
    pass
