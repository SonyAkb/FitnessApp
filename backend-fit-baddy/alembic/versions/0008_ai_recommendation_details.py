"""ai_recommendations: reason, intensity, sources, engine (AI-03)

Ответ LLM + RAG-сервиса хранится целиком, чтобы история показывала
обоснование, интенсивность и источники. engine — кто ответил: rules или rag.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ai_recommendations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('intensity', sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column('sources', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('engine', sa.String(length=16), nullable=False, server_default='rules'))


def downgrade() -> None:
    with op.batch_alter_table('ai_recommendations', schema=None) as batch_op:
        batch_op.drop_column('engine')
        batch_op.drop_column('sources')
        batch_op.drop_column('intensity')
        batch_op.drop_column('reason')
