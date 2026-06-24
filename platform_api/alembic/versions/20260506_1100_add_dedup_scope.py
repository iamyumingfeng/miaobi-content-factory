"""add dedup_scope to generation_task

Revision ID: 20260506_1100
Revises: 20260506_1000
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260506_1100'
down_revision = '20260506_1000'
branch_labels = None
depends_on = None


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


def upgrade():
    """添加去重范围配置字段（幂等：已存在则跳过）"""
    if not column_exists('generation_task', 'dedup_scope'):
        op.add_column(
            'generation_task',
            sa.Column(
                'dedup_scope',
                sa.JSON(),
                nullable=True,
                server_default=sa.text('JSON_ARRAY("subuser_history")'),
                comment='去重范围配置：subuser_history/current_task/all_history'
            )
        )


def downgrade():
    """回滚：移除去重范围配置字段"""
    if column_exists('generation_task', 'dedup_scope'):
        op.drop_column('generation_task', 'dedup_scope')
