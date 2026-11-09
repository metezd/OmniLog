"""Description and genres of titles (US-09, US-15).

media_items.description holds the synopsis. Genres are rows of their own, so the statistics of
Epic 6 are a plain JOIN, and a library can be filtered by genre. Nothing changes for the rows that
exist: the new column is empty and the new tables start empty.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media_items", sa.Column("description", sa.Text(), nullable=True))
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "media_item_genres",
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_item_id", "genre_id"),
    )
    op.create_index("ix_media_item_genres_genre_id", "media_item_genres", ["genre_id"])


def downgrade() -> None:
    op.drop_index("ix_media_item_genres_genre_id", table_name="media_item_genres")
    op.drop_table("media_item_genres")
    op.drop_table("genres")
    op.drop_column("media_items", "description")
