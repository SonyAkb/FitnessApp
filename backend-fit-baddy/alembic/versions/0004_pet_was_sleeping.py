"""add was_sleeping flag to pets (PET-06)

Колонка-флаг «питомец спал» (настроение sleeping, 14+ дней без тренировки):
по нему `apply_workout_completed` выдаёт приветствие «Рад тебя видеть!» и
бонус +10 XP при пробуждении, даже если настроение уже пересчитано на GET /pet.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('pets', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('was_sleeping', sa.Boolean(), nullable=False, server_default='0')
        )


def downgrade() -> None:
    with op.batch_alter_table('pets', schema=None) as batch_op:
        batch_op.drop_column('was_sleeping')
