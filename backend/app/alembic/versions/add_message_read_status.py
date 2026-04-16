"""Add is_read field to ChatMessage

Revision ID: add_message_is_read
Revises: add_user_online_status
Create Date: 2026-04-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_message_is_read'
down_revision: Union[str, None] = 'add_user_online_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ChatMessage already has last_read_at in ChatMember table
    # The is_read field is computed on-the-fly, not stored in DB
    pass


def downgrade() -> None:
    pass