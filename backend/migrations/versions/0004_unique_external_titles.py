"""One catalog row for each outside title (media type + outside id).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-16
"""
from alembic import op


# Revision identifiers used by Alembic
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fails if the same outside title is already saved twice. Remove the copies first, and
    # move any library entries and list items to the row you keep.
    op.create_unique_constraint(
        "uq_media_type_external_id", "media_items", ["media_type", "external_api_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_media_type_external_id", "media_items", type_="unique")
