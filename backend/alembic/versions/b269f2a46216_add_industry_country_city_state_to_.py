"""add industry country city state to contacts

Revision ID: b269f2a46216
Revises: 003_add_api_keys
Create Date: 2026-01-31 00:21:07.176783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b269f2a46216'
down_revision: Union[str, None] = '003_add_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to contacts table
    op.add_column('contacts', sa.Column('industry', sa.Text(), nullable=True))
    op.add_column('contacts', sa.Column('country', sa.Text(), nullable=True))
    op.add_column('contacts', sa.Column('city', sa.Text(), nullable=True))
    op.add_column('contacts', sa.Column('state', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove columns from contacts table
    op.drop_column('contacts', 'state')
    op.drop_column('contacts', 'city')
    op.drop_column('contacts', 'country')
    op.drop_column('contacts', 'industry')
