"""Add is_online, last_seen_at, timezone to user

Revision ID: add_user_online_status
Revises: 
Create Date: 2026-04-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_online_status'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('is_online', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('last_seen_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('timezone', sa.String(length=50), nullable=True, server_default='UTC'))


def downgrade() -> None:
    op.drop_column('user', 'timezone')
    op.drop_column('user', 'last_seen_at')
    op.drop_column('user', 'is_online')