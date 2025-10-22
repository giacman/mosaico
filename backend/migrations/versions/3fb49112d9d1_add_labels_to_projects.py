"""add_labels_to_projects

Revision ID: 3fb49112d9d1
Revises: 002
Create Date: 2025-10-20 17:25:28.400626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fb49112d9d1'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add labels column as an array of strings with empty array as default
    op.add_column('projects', sa.Column('labels', sa.ARRAY(sa.String()), nullable=False, server_default='{}'))


def downgrade() -> None:
    # Remove labels column
    op.drop_column('projects', 'labels')

