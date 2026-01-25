"""Add unique constraint on contact email

Revision ID: 002_add_email_unique
Revises: 001_initial
Create Date: 2026-01-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_email_unique'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraint on contacts.email where email is not null and not deleted."""
    # Create unique partial index on email (only for non-null, non-deleted rows)
    op.create_index(
        'idx_contacts_email_unique',
        'contacts',
        ['email'],
        unique=True,
        postgresql_where=sa.text('email IS NOT NULL AND deleted_at IS NULL')
    )


def downgrade() -> None:
    """Remove unique constraint on contacts.email."""
    op.drop_index('idx_contacts_email_unique', table_name='contacts')
