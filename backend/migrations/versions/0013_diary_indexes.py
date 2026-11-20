"""Indexes on diary_entries for the diary list and the delete cascade of a title.

Revision ID: 0013
Revises: 0011
Create Date: 2026-11-19

0012 is reserved for the pgvector migration (issue #151). Until it is merged, 0013 follows 0011.
When 0012 is on main, change down_revision below to "0012", so there is one head again.
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0013"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GET /diary filters by user_id and sorts by created_at, newest first
    op.create_index(
        "ix_diary_entries_user_id_created_at",
        "diary_entries",
        ["user_id", sa.text("created_at DESC")],
    )
    # Deleting a title cascades to its diary events. Without this index it scans the table.
    op.create_index(
        "ix_diary_entries_media_item_id",
        "diary_entries",
        ["media_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_diary_entries_media_item_id", table_name="diary_entries")
    op.drop_index("ix_diary_entries_user_id_created_at", table_name="diary_entries")
