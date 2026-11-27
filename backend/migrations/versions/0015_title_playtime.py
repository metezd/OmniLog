"""Playtime of a whole title, without a chapter (issue #413).

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-27

A game or a movie is often logged as a whole. user_libraries gets the total of these entries,
and a playtime entry can now point to a library entry instead of a chapter progress row.
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_libraries",
        sa.Column("playtime_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_check_constraint("chk_library_playtime", "user_libraries", "playtime_minutes >= 0")

    op.alter_column("playtime_logs", "chapter_progress_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("playtime_logs", sa.Column("library_entry_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_playtime_logs_library_entry_id",
        "playtime_logs",
        "user_libraries",
        ["library_entry_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_playtime_logs_library_entry_id"), "playtime_logs", ["library_entry_id"]
    )
    op.create_check_constraint(
        "chk_playtime_log_target",
        "playtime_logs",
        "num_nonnulls(chapter_progress_id, library_entry_id) = 1",
    )


def downgrade() -> None:
    # The entries of whole titles have no chapter, so they cannot stay after the downgrade
    op.execute("DELETE FROM playtime_logs WHERE chapter_progress_id IS NULL")
    op.drop_constraint("chk_playtime_log_target", "playtime_logs", type_="check")
    op.drop_index(op.f("ix_playtime_logs_library_entry_id"), table_name="playtime_logs")
    op.drop_constraint("fk_playtime_logs_library_entry_id", "playtime_logs", type_="foreignkey")
    op.drop_column("playtime_logs", "library_entry_id")
    op.alter_column("playtime_logs", "chapter_progress_id", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint("chk_library_playtime", "user_libraries", type_="check")
    op.drop_column("user_libraries", "playtime_minutes")
