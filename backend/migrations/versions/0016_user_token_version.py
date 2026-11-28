"""users.token_version for "log out on all devices" and a new password.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-27

Every token carries the version of its user. Raising it ends every token issued before (#426).
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
