"""add missing operation_log columns

Revision ID: 20260507_1910
Revises: 20260507_1900
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260507_1910'
down_revision: Union[str, None] = '20260507_1900'
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
    """添加缺失的 operation_log 表字段（幂等：已存在则跳过）"""

    # 添加 module 字段
    if not column_exists('operation_log', 'module'):
        op.add_column(
            'operation_log',
            sa.Column('module', sa.String(50), nullable=True, comment='模块：users/templates/materials/generation/distribution/system')
        )

    # 添加 description 字段
    if not column_exists('operation_log', 'description'):
        op.add_column(
            'operation_log',
            sa.Column('description', sa.String(500), nullable=True, comment='操作描述，如：创建素材：素材标题')
        )

    # 添加 extra_data_json 字段
    if not column_exists('operation_log', 'extra_data_json'):
        op.add_column(
            'operation_log',
            sa.Column('extra_data_json', sa.JSON(), nullable=True, comment='额外参数（JSON格式），如标签列表、操作条件等')
        )


def downgrade() -> None:
    """回滚：移除添加的字段"""

    if column_exists('operation_log', 'extra_data_json'):
        op.drop_column('operation_log', 'extra_data_json')

    if column_exists('operation_log', 'description'):
        op.drop_column('operation_log', 'description')

    if column_exists('operation_log', 'module'):
        op.drop_column('operation_log', 'module')