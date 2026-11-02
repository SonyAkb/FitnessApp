"""pet_events history table (PET-09)

Журнал событий питомца: xp, level_up, mood, return_bonus. Пишется при каждом
изменении питомца — для статистики «сколько XP за неделю» и отладки правил.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('pet_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('xp_total', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
    sa.Column('mood', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pet_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pet_events_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pet_events_pet_id'), ['pet_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pet_events_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pet_events_type'), ['type'], unique=False)
        batch_op.create_index(batch_op.f('ix_pet_events_created_at'), ['created_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('pet_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pet_events_created_at'))
        batch_op.drop_index(batch_op.f('ix_pet_events_type'))
        batch_op.drop_index(batch_op.f('ix_pet_events_user_id'))
        batch_op.drop_index(batch_op.f('ix_pet_events_pet_id'))
        batch_op.drop_index(batch_op.f('ix_pet_events_id'))

    op.drop_table('pet_events')
