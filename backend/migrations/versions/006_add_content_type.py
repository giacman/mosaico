"""Add content_type column to projects

Revision ID: 006_add_content_type
Revises: 005_add_labels_table
Create Date: 2026-01-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_content_type'
down_revision = '005_add_labels'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('content_type', sa.String(50), nullable=False, server_default='newsletter'))


def downgrade():
    op.drop_column('projects', 'content_type')
