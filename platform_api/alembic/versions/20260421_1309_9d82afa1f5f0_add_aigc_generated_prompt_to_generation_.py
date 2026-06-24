"""add aigc_generated_prompt column to generation_item

Revision ID: 9d82afa1f5f0
Revises: 20260421_1151
Create Date: 2026-04-21 13:09:58.640516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d82afa1f5f0'
down_revision: Union[str, None] = '20260421_1151'
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
    # 添加字段（幂等：已存在则跳过）
    if not column_exists('generation_item', 'aigc_generated_prompt'):
        op.add_column(
            'generation_item',
            sa.Column(
                'aigc_generated_prompt',
                sa.Text(),
                nullable=True,
                comment='AIGC提示词生成器产出的精炼提示词',
            ),
        )


def downgrade() -> None:
    # 删除字段（幂等：已存在才删除）
    if column_exists('generation_item', 'aigc_generated_prompt'):
        op.drop_column('generation_item', 'aigc_generated_prompt')
