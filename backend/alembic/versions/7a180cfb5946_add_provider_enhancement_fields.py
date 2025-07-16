"""add_provider_enhancement_fields

Revision ID: 7a180cfb5946
Revises: 2_add_llm_providers_table
Create Date: 2025-07-16 14:09:56.236557

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a180cfb5946'
down_revision = '2_add_llm_providers_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to llm_providers table
    with op.batch_alter_table('llm_providers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_from_env', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('validation_errors', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('last_tested', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('connection_status', sa.String(20), nullable=False, server_default='untested'))


def downgrade() -> None:
    # Remove the added columns
    with op.batch_alter_table('llm_providers', schema=None) as batch_op:
        batch_op.drop_column('connection_status')
        batch_op.drop_column('last_tested')
        batch_op.drop_column('validation_errors')
        batch_op.drop_column('is_valid')
        batch_op.drop_column('is_from_env')
