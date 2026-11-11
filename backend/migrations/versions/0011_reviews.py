"""Reviews of library entries with spoiler detection fields (US-14).

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_entry_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("contains_spoiler", sa.Boolean(), nullable=True),
        sa.Column("spoiler_score", sa.Float(), nullable=True),
        sa.Column("spoiler_model_version", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["library_entry_id"], ["user_libraries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("library_entry_id", name="uq_review_library_entry"),
    )


def downgrade() -> None:
    op.drop_table("reviews")
