"""Initial schema

Revision ID: f6d8a37e1b5c
Revises: 
Create Date: 2026-03-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6d8a37e1b5c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('google_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=64), server_default='America/Sao_Paulo', nullable=False),
        sa.Column('google_refresh_token', sa.Text(), nullable=True),
        sa.Column('calendar_sync_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id', name='users_google_id_key')
    )
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='America/Sao_Paulo', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_user_id'), 'events', ['user_id'], unique=False)
    op.create_index('ix_events_user_start', 'events', ['user_id', 'start_datetime'], unique=False)
    op.create_index('ix_events_user_status', 'events', ['user_id', 'status'], unique=False)

    # Create calendar_syncs table
    op.create_table(
        'calendar_syncs',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('google_calendar_id', sa.String(length=255), server_default='primary', nullable=False),
        sa.Column('google_event_id', sa.String(length=255), nullable=True),
        sa.Column('sync_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('etag', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_syncs_event_id'), 'calendar_syncs', ['event_id'], unique=True)
    op.create_index(op.f('ix_calendar_syncs_user_id'), 'calendar_syncs', ['user_id'], unique=False)
    op.create_index('ix_calendar_syncs_user_status', 'calendar_syncs', ['user_id', 'sync_status'], unique=False)


def downgrade() -> None:
    op.drop_table('calendar_syncs')
    op.drop_table('events')
    op.drop_table('users')
