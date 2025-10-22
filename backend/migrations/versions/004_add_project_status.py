"""add project status enum and column

Revision ID: 004
Revises: 3fb49112d9d1
Create Date: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "3fb49112d9d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    project_status = sa.Enum("in_progress", "approved", name="projectstatus")
    project_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "projects",
        sa.Column("status", project_status, nullable=False, server_default="in_progress"),
    )


def downgrade() -> None:
    op.drop_column("projects", "status")
    sa.Enum(name="projectstatus").drop(op.get_bind(), checkfirst=True)


