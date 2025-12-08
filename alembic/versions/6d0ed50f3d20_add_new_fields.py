"""Add profile/metadata fields without dropping existing tables.

Revision ID: 6d0ed50f3d20
Revises: 79a3fc6a5065
Create Date: 2025-12-08 20:48:40.615050
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6d0ed50f3d20'
down_revision: Union[str, Sequence[str], None] = '79a3fc6a5065'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.add_column("users", sa.Column("profile_picture", sa.String(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(), server_default="UTC", nullable=True),
    )
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))

    # projects
    op.add_column(
        "projects", sa.Column("status", sa.String(length=30), server_default="active")
    )
    op.add_column("projects", sa.Column("deadline", sa.DateTime(), nullable=True))
    op.add_column("projects", sa.Column("tags", sa.String(), nullable=True))

    # tasks
    op.add_column("tasks", sa.Column("estimated_hours", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("actual_hours", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("tags", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("attachments", sa.String(), nullable=True))


def downgrade() -> None:
    # tasks
    op.drop_column("tasks", "attachments")
    op.drop_column("tasks", "tags")
    op.drop_column("tasks", "actual_hours")
    op.drop_column("tasks", "estimated_hours")

    # projects
    op.drop_column("projects", "tags")
    op.drop_column("projects", "deadline")
    op.drop_column("projects", "status")

    # users
    op.drop_column("users", "last_login")
    op.drop_column("users", "timezone")
    op.drop_column("users", "bio")
    op.drop_column("users", "profile_picture")
