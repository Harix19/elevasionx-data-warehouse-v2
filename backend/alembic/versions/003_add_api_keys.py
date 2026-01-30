"""Add API keys table

Revision ID: 003_add_api_keys
Revises: 002_add_email_unique
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_api_keys'
down_revision: Union[str, None] = '002_add_email_unique'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create api_keys table for API key authentication."""
    # Create access_level ENUM type
    access_level = postgresql.ENUM(
        'read', 'write', 'admin',
        name='access_level',
        create_type=True
    )
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('access_level', access_level, server_default='read', nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_active', 'api_keys', ['is_active'])


def downgrade() -> None:
    """Drop api_keys table and ENUM type."""
    # Drop indexes
    op.drop_index('idx_api_keys_active', table_name='api_keys')
    op.drop_index('idx_api_keys_user_id', table_name='api_keys')
    op.drop_index('idx_api_keys_key_prefix', table_name='api_keys')
    
    # Drop table
    op.drop_table('api_keys')
    
    # Drop ENUM type
    access_level = postgresql.ENUM(name='access_level')
    access_level.drop(op.get_bind(), checkfirst=True)
