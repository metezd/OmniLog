"""Single playtime entries of a chapter or episode (US-11).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playtime_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_progress_id", sa.Integer(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column(
            "logged_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.CheckConstraint("minutes >= 1", name="chk_playtime_minutes"),
        sa.ForeignKeyConstraint(
            ["chapter_progress_id"], ["chapter_progress.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_playtime_logs_chapter_progress_id"),
        "playtime_logs",
        ["chapter_progress_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_playtime_logs_chapter_progress_id"), table_name="playtime_logs")
    op.drop_table("playtime_logs")
