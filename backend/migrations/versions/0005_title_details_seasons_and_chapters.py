"""Title details (US-09): seasons, episodes and chapters, and the last sync time of a title.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty until the seasons of the title are loaded from the outside service
    op.add_column("media_items", sa.Column("last_synced", sa.DateTime(), nullable=True))

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("air_date", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_item_id", "season_number", name="uq_season_media_number"),
    )
    op.create_index(op.f("ix_seasons_media_item_id"), "seasons", ["media_item_id"], unique=False)

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Enum("EPISODE", "CHAPTER", name="chapterkind"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("release_date", sa.String(length=50), nullable=True),
        sa.Column("runtime_minutes", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(kind = 'EPISODE' AND season_id IS NOT NULL)"
            " OR (kind = 'CHAPTER' AND season_id IS NULL)",
            name="chk_chapter_kind_season",
        ),
        sa.CheckConstraint("number >= 0", name="chk_chapter_number"),
        sa.CheckConstraint(
            "runtime_minutes IS NULL OR runtime_minutes >= 0", name="chk_chapter_runtime"
        ),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_id", "number", name="uq_chapter_season_number"),
    )
    op.create_index(op.f("ix_chapters_media_item_id"), "chapters", ["media_item_id"], unique=False)
    op.create_index(op.f("ix_chapters_season_id"), "chapters", ["season_id"], unique=False)
    # The number of a game chapter is unique inside its game. A NULL season id is never equal to
    # another NULL, so the constraint above does not cover game chapters.
    op.create_index(
        "uq_chapter_game_number",
        "chapters",
        ["media_item_id", "number"],
        unique=True,
        postgresql_where=sa.text("season_id IS NULL"),
        sqlite_where=sa.text("season_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_chapter_game_number",
        table_name="chapters",
        postgresql_where=sa.text("season_id IS NULL"),
        sqlite_where=sa.text("season_id IS NULL"),
    )
    op.drop_index(op.f("ix_chapters_season_id"), table_name="chapters")
    op.drop_index(op.f("ix_chapters_media_item_id"), table_name="chapters")
    op.drop_table("chapters")
    # PostgreSQL keeps the enum type after the table is gone. Drop it, so upgrade works again.
    sa.Enum(name="chapterkind").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_seasons_media_item_id"), table_name="seasons")
    op.drop_table("seasons")
    op.drop_column("media_items", "last_synced")
