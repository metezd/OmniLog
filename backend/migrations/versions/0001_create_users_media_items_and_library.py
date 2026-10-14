"""create users media items and library

Revision ID: 0001
Revises: 
Create Date: 2026-10-14 19:09:45.987157
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('media_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('media_type', sa.Enum('GAME', 'SERIES', 'MOVIE', name='mediatype'), nullable=False),
    sa.Column('poster_url', sa.String(length=500), nullable=True),
    sa.Column('release_date', sa.String(length=50), nullable=True),
    sa.Column('external_api_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_items_external_api_id'), 'media_items', ['external_api_id'], unique=False)
    op.create_index(op.f('ix_media_items_title'), 'media_items', ['title'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('user_libraries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('media_item_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PLAN_TO_WATCH', 'IN_PROGRESS', 'COMPLETED', 'DROPPED', name='watchstatus'), nullable=False),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('rating >= 1 AND rating <= 10', name='chk_rating_range'),
    sa.ForeignKeyConstraint(['media_item_id'], ['media_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'media_item_id', name='uq_user_media_entry')
    )


def downgrade() -> None:
    op.drop_table('user_libraries')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_media_items_title'), table_name='media_items')
    op.drop_index(op.f('ix_media_items_external_api_id'), table_name='media_items')
    op.drop_table('media_items')

    # PostgreSQL keeps enum types after their tables are dropped, so drop them explicitly
    sa.Enum(name='watchstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='mediatype').drop(op.get_bind(), checkfirst=True)
