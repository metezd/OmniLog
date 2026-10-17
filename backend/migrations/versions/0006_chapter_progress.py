"""Personal record of one user for one chapter or episode, with the chapter rating (US-10).

The table also holds the title (media_item_id). Two composite foreign keys point to the library
entry and to the chapter together with the title, so the database itself rejects a progress row
whose chapter belongs to another title than the library entry (BR-11). The composite keys need a
unique constraint on (id, media_item_id) in user_libraries and in chapters.

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
    op.create_unique_constraint(
        "uq_user_library_id_media_item", "user_libraries", ["id", "media_item_id"]
    )
    op.create_unique_constraint("uq_chapter_id_media_item", "chapters", ["id", "media_item_id"])

    op.create_table(
        "chapter_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_entry_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("playtime_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="chk_progress_rating"
        ),
        sa.CheckConstraint("playtime_minutes >= 0", name="chk_progress_playtime"),
        sa.ForeignKeyConstraint(
            ["library_entry_id", "media_item_id"],
            ["user_libraries.id", "user_libraries.media_item_id"],
            name="fk_progress_entry_title",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chapter_id", "media_item_id"],
            ["chapters.id", "chapters.media_item_id"],
            name="fk_progress_chapter_title",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("library_entry_id", "chapter_id", name="uq_progress_entry_chapter"),
    )
    op.create_index(
        op.f("ix_chapter_progress_chapter_id"), "chapter_progress", ["chapter_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chapter_progress_chapter_id"), table_name="chapter_progress")
    op.drop_table("chapter_progress")
    op.drop_constraint("uq_chapter_id_media_item", "chapters", type_="unique")
    op.drop_constraint("uq_user_library_id_media_item", "user_libraries", type_="unique")
