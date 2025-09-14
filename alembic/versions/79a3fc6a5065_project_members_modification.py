"""project members modification

Revision ID: 79a3fc6a5065
Revises: 1912c4b9c1b3
Create Date: 2025-09-14 23:20:53.776738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '79a3fc6a5065'
down_revision: Union[str, Sequence[str], None] = '1912c4b9c1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', name="fk_project_members_project"), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', name="fk_project_members_user"), nullable=False),
        sa.Column('role', sa.String, nullable=False),
        sa.Column('added_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # Add indexes for faster lookups
    op.create_index('ix_project_members_project_id', 'project_members', ['project_id'])
    op.create_index('ix_project_members_user_id', 'project_members', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_project_members_project_id', table_name='project_members')
    op.drop_index('ix_project_members_user_id', table_name='project_members')
    op.drop_table('project_members')

