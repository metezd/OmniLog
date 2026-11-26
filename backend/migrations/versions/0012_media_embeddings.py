"""Store title embeddings using pgvector (issue #151).

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "media_embeddings",
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("source_text_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["media_item_id"],
            ["media_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("media_item_id", "model_name"),
    )

    op.execute(
        "CREATE INDEX ix_media_embeddings_embedding "
        "ON media_embeddings USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_media_embeddings_embedding",
        table_name="media_embeddings",
    )
    op.drop_table("media_embeddings")
