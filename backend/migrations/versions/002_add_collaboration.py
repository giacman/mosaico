"""add collaboration support

Revision ID: 002
Revises: 001
Create Date: 2025-10-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove user_id column from projects (it was for ownership, not needed for shared projects)
    op.drop_column('projects', 'user_id')
    
    # Add audit fields to projects
    op.add_column('projects', sa.Column('created_by_user_id', sa.String(255), nullable=True))
    op.add_column('projects', sa.Column('created_by_user_name', sa.String(255), nullable=True))
    op.add_column('projects', sa.Column('updated_by_user_id', sa.String(255), nullable=True))
    op.add_column('projects', sa.Column('updated_by_user_name', sa.String(255), nullable=True))
    
    # Create activity_logs table
    op.create_table('activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('field_changed', sa.String(100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_logs_id'), 'activity_logs', ['id'], unique=False)
    op.create_index(op.f('ix_activity_logs_project_id'), 'activity_logs', ['project_id'], unique=False)


def downgrade() -> None:
    # Drop activity_logs table
    op.drop_index(op.f('ix_activity_logs_project_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
    
    # Remove audit fields from projects
    op.drop_column('projects', 'updated_by_user_name')
    op.drop_column('projects', 'updated_by_user_id')
    op.drop_column('projects', 'created_by_user_name')
    op.drop_column('projects', 'created_by_user_id')
    
    # Add back user_id column
    op.add_column('projects', sa.Column('user_id', sa.String(255), nullable=False, server_default='unknown'))

