"""Initial migration with all tables, indexes, and ENUM types.

Revision ID: 001_initial
Revises:
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lead_status ENUM type
    lead_status = postgresql.ENUM(
        'new', 'contacted', 'qualified', 'customer', 'churned',
        name='lead_status',
        create_type=True  # Let SQLAlchemy handle creation implicitly
    )

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('domain', sa.Text(), unique=True, nullable=True),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('technologies', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('twitter_url', sa.Text(), nullable=True),
        sa.Column('facebook_url', sa.Text(), nullable=True),
        sa.Column('revenue', sa.Numeric(15, 2), nullable=True),
        sa.Column('funding_date', sa.Date(), nullable=True),
        sa.Column('funding_data', postgresql.JSONB(), nullable=True),
        sa.Column('custom_tags_a', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('custom_tags_b', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('custom_tags_c', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('lead_source', sa.Text(), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=True),
        sa.Column('status', lead_status, server_default='new', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('first_name', sa.Text(), nullable=False),
        sa.Column('last_name', sa.Text(), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=True),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('working_company_name', sa.Text(), nullable=True),
        sa.Column('job_title', sa.Text(), nullable=True),
        sa.Column('seniority_level', sa.Text(), nullable=True),
        sa.Column('department', sa.Text(), nullable=True),
        sa.Column('company_domain', sa.Text(), nullable=True),
        sa.Column('company_linkedin_url', sa.Text(), nullable=True),
        sa.Column('custom_tags_a', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('custom_tags_b', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('custom_tags_c', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('lead_source', sa.Text(), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=True),
        sa.Column('status', lead_status, server_default='new', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes for companies
    op.create_index('idx_companies_domain', 'companies', ['domain'])
    op.create_index('idx_companies_status', 'companies', ['status'])
    op.create_index('idx_companies_industry', 'companies', ['industry'])
    op.create_index('idx_companies_country', 'companies', ['country'])
    op.create_index('idx_companies_lead_score', 'companies', ['lead_score'])

    # Create GIN indexes for array columns (companies)
    op.execute('CREATE INDEX idx_companies_keywords ON companies USING GIN(keywords)')
    op.execute('CREATE INDEX idx_companies_technologies ON companies USING GIN(technologies)')
    op.execute('CREATE INDEX idx_companies_tags_a ON companies USING GIN(custom_tags_a)')
    op.execute('CREATE INDEX idx_companies_tags_b ON companies USING GIN(custom_tags_b)')
    op.execute('CREATE INDEX idx_companies_tags_c ON companies USING GIN(custom_tags_c)')

    # Create full-text search index for companies
    op.execute("""
        CREATE INDEX idx_companies_fts ON companies USING GIN(
            to_tsvector('english',
                COALESCE(name, '') || ' ' ||
                COALESCE(description, '') || ' ' ||
                COALESCE(domain, '')
            )
        )
    """)

    # Create indexes for contacts
    op.create_index('idx_contacts_email', 'contacts', ['email'])
    op.create_index('idx_contacts_company_id', 'contacts', ['company_id'])
    op.create_index('idx_contacts_seniority', 'contacts', ['seniority_level'])
    op.create_index('idx_contacts_department', 'contacts', ['department'])

    # Create GIN indexes for array columns (contacts)
    op.execute('CREATE INDEX idx_contacts_tags_a ON contacts USING GIN(custom_tags_a)')
    op.execute('CREATE INDEX idx_contacts_tags_b ON contacts USING GIN(custom_tags_b)')
    op.execute('CREATE INDEX idx_contacts_tags_c ON contacts USING GIN(custom_tags_c)')

    # Create full-text search index for contacts
    op.execute("""
        CREATE INDEX idx_contacts_fts ON contacts USING GIN(
            to_tsvector('english',
                COALESCE(first_name, '') || ' ' ||
                COALESCE(last_name, '') || ' ' ||
                COALESCE(email, '') || ' ' ||
                COALESCE(job_title, '')
            )
        )
    """)

    # Create index for users
    op.create_index('idx_users_email', 'users', ['email'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_email', table_name='users')
    op.execute('DROP INDEX IF EXISTS idx_contacts_fts')
    op.execute('DROP INDEX IF EXISTS idx_contacts_tags_c')
    op.execute('DROP INDEX IF EXISTS idx_contacts_tags_b')
    op.execute('DROP INDEX IF EXISTS idx_contacts_tags_a')
    op.drop_index('idx_contacts_department', table_name='contacts')
    op.drop_index('idx_contacts_seniority', table_name='contacts')
    op.drop_index('idx_contacts_company_id', table_name='contacts')
    op.drop_index('idx_contacts_email', table_name='contacts')
    op.execute('DROP INDEX IF EXISTS idx_companies_fts')
    op.execute('DROP INDEX IF EXISTS idx_companies_tags_c')
    op.execute('DROP INDEX IF EXISTS idx_companies_tags_b')
    op.execute('DROP INDEX IF EXISTS idx_companies_tags_a')
    op.execute('DROP INDEX IF EXISTS idx_companies_technologies')
    op.execute('DROP INDEX IF EXISTS idx_companies_keywords')
    op.drop_index('idx_companies_lead_score', table_name='companies')
    op.drop_index('idx_companies_country', table_name='companies')
    op.drop_index('idx_companies_industry', table_name='companies')
    op.drop_index('idx_companies_status', table_name='companies')
    op.drop_index('idx_companies_domain', table_name='companies')

    # Drop tables
    op.drop_table('users')
    op.drop_table('contacts')
    op.drop_table('companies')

    # Drop ENUM type
    lead_status = postgresql.ENUM(name='lead_status')
    lead_status.drop(op.get_bind(), checkfirst=True)
