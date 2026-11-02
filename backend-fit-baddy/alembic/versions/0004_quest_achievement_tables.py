"""quest and achievement tables with seed data (PET-07)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('quests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('period', sa.String(), nullable=False),
    sa.Column('target', sa.Integer(), nullable=False),
    sa.Column('xp_reward', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='uq_quests_code')
    )
    with op.batch_alter_table('quests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_quests_id'), ['id'], unique=False)

    op.create_table('user_quests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('quest_id', sa.Integer(), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notified', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_quests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_quests_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_quests_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_quests_quest_id'), ['quest_id'], unique=False)

    op.create_table('achievements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('xp_reward', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='uq_achievements_code')
    )
    with op.batch_alter_table('achievements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_achievements_id'), ['id'], unique=False)

    op.create_table('user_achievements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('achievement_id', sa.Integer(), nullable=False),
    sa.Column('earned_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement')
    )
    with op.batch_alter_table('user_achievements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_achievements_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_achievements_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_achievements_achievement_id'), ['achievement_id'], unique=False)

    quests = sa.table(
        "quests",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("title", sa.String),
        sa.column("period", sa.String),
        sa.column("target", sa.Integer),
        sa.column("xp_reward", sa.Integer),
    )
    achievements = sa.table(
        "achievements",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("title", sa.String),
        sa.column("xp_reward", sa.Integer),
    )
    op.bulk_insert(quests, [
        {"id": 1, "code": "one_workout_today", "title": "1 тренировка сегодня",
         "period": "daily", "target": 1, "xp_reward": 20},
        {"id": 2, "code": "three_workouts_week", "title": "3 тренировки за неделю",
         "period": "weekly", "target": 3, "xp_reward": 50},
    ])
    op.bulk_insert(achievements, [
        {"id": 1, "code": "first_workout", "title": "Первая тренировка", "xp_reward": 10},
        {"id": 2, "code": "three_in_row", "title": "3 тренировки подряд", "xp_reward": 30},
        {"id": 3, "code": "week_no_miss", "title": "Неделя без пропусков", "xp_reward": 40},
    ])


def downgrade() -> None:
    with op.batch_alter_table('user_achievements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_achievements_achievement_id'))
        batch_op.drop_index(batch_op.f('ix_user_achievements_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_achievements_id'))
    op.drop_table('user_achievements')

    with op.batch_alter_table('achievements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_achievements_id'))
    op.drop_table('achievements')

    with op.batch_alter_table('user_quests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_quests_quest_id'))
        batch_op.drop_index(batch_op.f('ix_user_quests_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_quests_id'))
    op.drop_table('user_quests')

    with op.batch_alter_table('quests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_quests_id'))
    op.drop_table('quests')