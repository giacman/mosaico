"""add_labels_table

Revision ID: 005_add_labels
Revises: 1bc1e61d11ff
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_labels'
down_revision = '1bc1e61d11ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create labels table for dynamic label management
    op.create_table('labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=50), server_default='gray', nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=255), nullable=True),
        sa.Column('created_by_user_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_labels_id'), 'labels', ['id'], unique=False)
    op.create_index(op.f('ix_labels_name'), 'labels', ['name'], unique=True)
    
    # Seed with default labels (migrated from hardcoded list)
    op.execute("""
        INSERT INTO labels (name, color, description, created_at, updated_at)
        VALUES 
            ('promo', 'red', 'Promotional campaigns', NOW(), NOW()),
            ('category', 'blue', 'Category-specific content', NOW(), NOW()),
            ('design', 'purple', 'Design-focused content', NOW(), NOW()),
            ('october 2025', 'orange', 'October 2025 campaigns', NOW(), NOW()),
            ('november 2025', 'orange', 'November 2025 campaigns', NOW(), NOW()),
            ('december 2025', 'orange', 'December 2025 campaigns', NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_labels_name'), table_name='labels')
    op.drop_index(op.f('ix_labels_id'), table_name='labels')
    op.drop_table('labels')

