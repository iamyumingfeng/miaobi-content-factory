"""add generation_task name field

Revision ID: 20260420_1800
Revises: 20260420_1600
Create Date: 2026-04-20 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260420_1800'
down_revision: Union[str, None] = '20260420_1600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.fetchone()[0] > 0


def upgrade() -> None:
    # 添加任务名称字段（幂等：已存在则跳过）
    if not column_exists('generation_task', 'name'):
        op.add_column('generation_task', sa.Column('name', sa.String(200), nullable=True, comment='任务名称'))


def downgrade() -> None:
    # 删除任务名称字段（幂等：已存在才删除）
    if column_exists('generation_task', 'name'):
        op.drop_column('generation_task', 'name')