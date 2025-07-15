"""Add llm_providers table

Revision ID: 2_add_llm_providers_table
Revises: 1bcfc6c0f7b7
Create Date: 2025-07-14 22:13:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

def table_exists(table_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()

def upgrade() -> None:
    if not table_exists('llm_providers'):
        op.create_table(
            'llm_providers',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(100), nullable=False, unique=True),
            sa.Column('provider_type', sa.String(20), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
            sa.Column('api_key', sa.String(255), nullable=False),
            sa.Column('model', sa.String(100), nullable=True),
            sa.Column('endpoint', sa.String(255), nullable=True),
            sa.Column('deployment', sa.String(100), nullable=True),
            sa.Column('api_version', sa.String(20), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'),
                     onupdate=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        )
        
        # Create a unique constraint for active providers per type
        with op.batch_alter_table('llm_providers', schema=None) as batch_op:
            batch_op.create_unique_constraint(
                'uix_provider_type_active',
                ['provider_type', 'is_active'],
                sqlite_where=sa.text('is_active = 1')
            )

def downgrade() -> None:
    if table_exists('llm_providers'):
        op.drop_table('llm_providers')
