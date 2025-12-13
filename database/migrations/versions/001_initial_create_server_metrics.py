"""Initial migration: create server_metrics table

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create server_metrics table
    op.create_table(
        'server_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('vm', sa.String(length=255), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('max_value', sa.DECIMAL(10, 5), nullable=True),
        sa.Column('min_value', sa.DECIMAL(10, 5), nullable=True),
        sa.Column('avg_value', sa.DECIMAL(10, 5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_metrics_vm_date', 'server_metrics', ['vm', 'date', 'metric'], unique=False)
    op.create_index('idx_metrics_date', 'server_metrics', ['date'], unique=False)
    op.create_index('idx_metrics_metric', 'server_metrics', ['metric'], unique=False)
    op.create_index(op.f('ix_server_metrics_id'), 'server_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_server_metrics_vm'), 'server_metrics', ['vm'], unique=False)
    op.create_index(op.f('ix_server_metrics_date'), 'server_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_server_metrics_metric'), 'server_metrics', ['metric'], unique=False)
    
    # Create unique constraint
    op.create_unique_constraint('uq_vm_date_metric', 'server_metrics', ['vm', 'date', 'metric'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_server_metrics_metric'), table_name='server_metrics')
    op.drop_index(op.f('ix_server_metrics_date'), table_name='server_metrics')
    op.drop_index(op.f('ix_server_metrics_vm'), table_name='server_metrics')
    op.drop_index(op.f('ix_server_metrics_id'), table_name='server_metrics')
    op.drop_index('idx_metrics_metric', table_name='server_metrics')
    op.drop_index('idx_metrics_date', table_name='server_metrics')
    op.drop_index('idx_metrics_vm_date', table_name='server_metrics')
    
    # Drop unique constraint
    op.drop_constraint('uq_vm_date_metric', 'server_metrics', type_='unique')
    
    # Drop table
    op.drop_table('server_metrics')

