"""Personal record of one user for one chapter or episode, with the chapter rating (US-10).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chapter_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_entry_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("playtime_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="chk_progress_rating"
        ),
        sa.CheckConstraint("playtime_minutes >= 0", name="chk_progress_playtime"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["library_entry_id"], ["user_libraries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("library_entry_id", "chapter_id", name="uq_progress_entry_chapter"),
    )
    op.create_index(
        op.f("ix_chapter_progress_chapter_id"), "chapter_progress", ["chapter_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chapter_progress_chapter_id"), table_name="chapter_progress")
    op.drop_table("chapter_progress")
