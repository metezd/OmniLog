"""A username cannot contain @ (BR-18).

The login field accepts a username or an email. A value with @ is read as an email, so a username
with @ would be unreachable and could look like the email of another user. The check constraint
keeps this impossible in the database too.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    offenders = op.get_bind().execute(
        sa.text("SELECT id, username FROM users WHERE position('@' in username) > 0 ORDER BY id")
    ).fetchall()
    if offenders:
        names = ", ".join(f"{row.id}:{row.username}" for row in offenders)
        raise RuntimeError(
            "Cannot add chk_username_no_at. These users (id:username) have an @ in the username: "
            f"{names}. Rename them first, for example: UPDATE users SET username = "
            "replace(username, '@', '_') WHERE position('@' in username) > 0;"
        )
    op.create_check_constraint("chk_username_no_at", "users", "position('@' in username) = 0")


def downgrade() -> None:
    op.drop_constraint("chk_username_no_at", "users", type_="check")
