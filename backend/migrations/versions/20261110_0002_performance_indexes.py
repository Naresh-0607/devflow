"""Performance indexes for dashboard, project and chat queries.

Revision ID: 0002_performance_indexes
Revises: 0001_initial
Create Date: 2026-11-10

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_performance_indexes"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_projects_user_status", "projects", ["user_id", "status"], unique=False
    )
    op.create_index(
        "ix_ai_summaries_project_created",
        "ai_summaries",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_summaries_project_created", table_name="ai_summaries")
    op.drop_index("ix_projects_user_status", table_name="projects")
