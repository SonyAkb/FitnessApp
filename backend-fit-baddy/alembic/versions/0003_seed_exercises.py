"""seed exercises

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-25 14:44:19.429205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Лёгкое описание таблицы: не импортируем модель, чтобы миграция не зависела от будущих изменений models.py
exercises_t = sa.table(
    "exercises",
    sa.column("name", sa.String),
    sa.column("muscle_group", sa.String),
    sa.column("description", sa.Text),
)

# Предварительный состав: окончательный список согласует владелец модуля (см. WKT-06, «Вопросы»)
SEED = [
    ("Жим штанги лёжа", "chest"),
    ("Жим гантелей на наклонной скамье", "chest"),
    ("Разведение гантелей лёжа", "chest"),
    ("Отжимания на брусьях", "chest"),
    ("Подтягивания широким хватом", "back"),
    ("Тяга штанги в наклоне", "back"),
    ("Тяга верхнего блока", "back"),
    ("Тяга гантели одной рукой", "back"),
    ("Становая тяга", "back"),
    ("Приседания со штангой", "legs"),
    ("Жим ногами", "legs"),
    ("Выпады с гантелями", "legs"),
    ("Румынская тяга", "legs"),
    ("Подъём на носки стоя", "legs"),
    ("Болгарские приседания", "legs"),
    ("Ягодичный мостик", "glutes"),
    ("Отведение ноги в тренажёре", "glutes"),
    ("Жим штанги стоя", "shoulders"),
    ("Жим гантелей сидя", "shoulders"),
    ("Махи гантелей в стороны", "shoulders"),
    ("Махи в наклоне на заднюю дельту", "shoulders"),
    ("Сгибание рук со штангой", "biceps"),
    ("Молотковые сгибания", "biceps"),
    ("Сгибание рук на скамье Скотта", "biceps"),
    ("Французский жим лёжа", "triceps"),
    ("Разгибание рук на блоке", "triceps"),
    ("Жим узким хватом", "triceps"),
    ("Планка", "core"),
    ("Скручивания", "core"),
    ("Подъём ног в висе", "core"),
    ("Русские скручивания", "core"),
    ("Бёрпи", "full_body"),
    ("Махи гирей", "full_body"),
]


def upgrade() -> None:
    op.bulk_insert(
        exercises_t,
        [{"name": name, "muscle_group": group, "description": None} for name, group in SEED],
    )


def downgrade() -> None:
    names = [name for name, _ in SEED]
    op.execute(exercises_t.delete().where(exercises_t.c.name.in_(names)))