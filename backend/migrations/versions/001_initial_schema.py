"""Initial schema creation - users, media, episodes, logs

Revision ID: 001_initial_schema
Revises: mete
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    media_type_enum = sa.Enum('game', 'tv_series', name='mediatype')
    log_status_enum = sa.Enum('watching', 'completed', 'dropped', 'planning', name='logstatus')
    
    media_type_enum.create(op.get_bind())
    log_status_enum.create(op.get_bind())
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Media table
    op.create_table(
        'media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('game', 'tv_series', name='mediatype'), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('imdb_rating', sa.Float(), nullable=True),
        sa.Column('average_user_rating', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_external_id'), 'media', ['external_id'], unique=False)
    op.create_index(op.f('ix_media_id'), 'media', ['id'], unique=False)
    op.create_index(op.f('ix_media_title'), 'media', ['title'], unique=False)
    op.create_index(op.f('ix_media_type'), 'media', ['type'], unique=False)
    
    # Episodes table
    op.create_table(
        'episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('season_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('air_date', sa.Date(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_episodes_id'), 'episodes', ['id'], unique=False)
    op.create_index(op.f('ix_episodes_media_id'), 'episodes', ['media_id'], unique=False)
    
    # User logs table
    op.create_table(
        'user_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('watching', 'completed', 'dropped', 'planning', name='logstatus'), nullable=True),
        sa.Column('playtime_minutes', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_logs_created_at'), 'user_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_user_logs_id'), 'user_logs', ['id'], unique=False)
    op.create_index(op.f('ix_user_logs_media_id'), 'user_logs', ['media_id'], unique=False)
    op.create_index(op.f('ix_user_logs_status'), 'user_logs', ['status'], unique=False)
    op.create_index(op.f('ix_user_logs_user_id'), 'user_logs', ['user_id'], unique=False)
    
    # User choices table
    op.create_table(
        'user_choices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('episode_id', sa.Integer(), nullable=False),
        sa.Column('choice_key', sa.String(length=100), nullable=False),
        sa.Column('choice_value', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_choices_id'), 'user_choices', ['id'], unique=False)
    op.create_index(op.f('ix_user_choices_user_id'), 'user_choices', ['user_id'], unique=False)
    
    # Custom lists table
    op.create_table(
        'custom_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_lists_id'), 'custom_lists', ['id'], unique=False)
    op.create_index(op.f('ix_custom_lists_user_id'), 'custom_lists', ['user_id'], unique=False)
    
    # List-Media association table (many-to-many)
    op.create_table(
        'list_media_association',
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['custom_lists.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ),
        sa.PrimaryKeyConstraint('list_id', 'media_id')
    )


def downgrade() -> None:
    op.drop_table('list_media_association')
    op.drop_table('custom_lists')
    op.drop_table('user_choices')
    op.drop_table('user_logs')
    op.drop_table('episodes')
    op.drop_table('media')
    op.drop_table('users')
    
    # Drop ENUM types
    sa.Enum(name='logstatus').drop(op.get_bind())
    sa.Enum(name='mediatype').drop(op.get_bind())
