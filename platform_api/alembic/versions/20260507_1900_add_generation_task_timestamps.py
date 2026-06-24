"""add generation_task started_at and completed_at fields

Revision ID: 20260507_1900
Revises: 20260506_1200
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260507_1900'
down_revision: Union[str, None] = '20260506_1200'
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
    """添加任务时间戳字段（幂等：已存在则跳过）"""

    # 添加 started_at 字段：任务开始处理时间（首次变为 processing 时设置）
    if not column_exists('generation_task', 'started_at'):
        op.add_column(
            'generation_task',
            sa.Column('started_at', sa.DateTime(), nullable=True, comment='任务开始处理时间（首次变为 processing 时设置）')
        )

    # 添加 completed_at 字段：任务完成时间（变为最终状态时设置）
    if not column_exists('generation_task', 'completed_at'):
        op.add_column(
            'generation_task',
            sa.Column('completed_at', sa.DateTime(), nullable=True, comment='任务完成时间（变为最终状态时设置）')
        )


def downgrade() -> None:
    """回滚：移除任务时间戳字段"""

    if column_exists('generation_task', 'completed_at'):
        op.drop_column('generation_task', 'completed_at')

    if column_exists('generation_task', 'started_at'):
        op.drop_column('generation_task', 'started_at')
