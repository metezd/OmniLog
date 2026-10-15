"""Diary events without a title, and unique list names per user.

Revision ID: 0003
Revises: 16c8eff0da76
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0003"
down_revision = "16c8eff0da76"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "diary_entries",
        "media_item_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_unique_constraint(
        "uq_user_list_name", "custom_lists", ["user_id", "name"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_list_name", "custom_lists", type_="unique")
    # The column can only become NOT NULL again if no event lacks a title.
    # This removes list events. It is the only way to restore the old schema.
    op.execute("DELETE FROM diary_entries WHERE media_item_id IS NULL")
    op.alter_column(
        "diary_entries",
        "media_item_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
