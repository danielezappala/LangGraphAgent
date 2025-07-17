"""initial_migration

Revision ID: 1bcfc6c0f7b7
Revises: 
Create Date: 2025-07-14 22:09:56.345695

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1bcfc6c0f7b7'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create the llm_providers table with SQLite-compatible syntax
    op.create_table(
        'llm_providers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('provider_type', sa.String(20), nullable=False),  # 'openai' or 'azure'
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=True),  # Azure-specific
        sa.Column('deployment', sa.String(100), nullable=True),  # Azure-specific
        sa.Column('api_version', sa.String(20), nullable=True),  # Azure-specific
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'),
                 onupdate=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sqlite_autoincrement=True
    )
    
    # Create a unique constraint for active providers per type
    with op.batch_alter_table('llm_providers', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_provider_type_active',
            ['provider_type', 'is_active'],
            sqlite_where=sa.text('is_active = 1')
        )

def downgrade() -> None:
    # Drop the table if it exists
    op.drop_table('llm_providers')
