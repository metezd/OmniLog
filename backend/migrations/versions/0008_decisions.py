"""Branching decisions of a chapter and the choices of users (US-12).

The composite foreign keys make the database check two rules itself. The chosen option must
belong to the decision point (BR-13), and the library entry and the decision point must belong
to the same title (BR-11).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(length=300), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("position >= 1", name="chk_decision_point_position"),
        sa.ForeignKeyConstraint(
            ["chapter_id", "media_item_id"],
            ["chapters.id", "chapters.media_item_id"],
            name="fk_decision_point_chapter_title",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "media_item_id", name="uq_decision_point_id_media_item"),
    )
    op.create_index(
        op.f("ix_decision_points_chapter_id"), "decision_points", ["chapter_id"], unique=False
    )

    op.create_table(
        "decision_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("decision_point_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=10), nullable=False),
        sa.Column("text", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["decision_point_id"], ["decision_points.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_point_id", "id", name="uq_option_point_id"),
        sa.UniqueConstraint("decision_point_id", "label", name="uq_option_point_label"),
    )

    op.create_table(
        "user_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_entry_id", sa.Integer(), nullable=False),
        sa.Column("decision_point_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "decided_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["library_entry_id", "media_item_id"],
            ["user_libraries.id", "user_libraries.media_item_id"],
            name="fk_decision_entry_title",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["decision_point_id", "media_item_id"],
            ["decision_points.id", "decision_points.media_item_id"],
            name="fk_decision_point_title",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["decision_point_id", "option_id"],
            ["decision_options.decision_point_id", "decision_options.id"],
            name="fk_decision_option_point",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "library_entry_id", "decision_point_id", name="uq_user_decision_entry_point"
        ),
    )
    op.create_index(
        op.f("ix_user_decisions_decision_point_id"),
        "user_decisions",
        ["decision_point_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_decisions_decision_point_id"), table_name="user_decisions")
    op.drop_table("user_decisions")
    op.drop_table("decision_options")
    op.drop_index(op.f("ix_decision_points_chapter_id"), table_name="decision_points")
    op.drop_table("decision_points")
