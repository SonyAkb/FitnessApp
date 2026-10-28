"""add last_counted_at and completions columns to user_quests (PET-08)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user_quests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_counted_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('completions', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('user_quests', schema=None) as batch_op:
        batch_op.drop_column('completions')
        batch_op.drop_column('last_counted_at')
