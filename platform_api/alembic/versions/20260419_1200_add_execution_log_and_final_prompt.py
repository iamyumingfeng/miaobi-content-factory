"""
Add generation_item_execution_log table and final_prompt field

Revision ID: 20260419_1200
Revises: 20260419_1100
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '20260419_1200'
down_revision = '20260419_1100'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return result.fetchone()[0] > 0


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


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND index_name = :index_name
        """),
        {"table_name": table_name, "index_name": index_name}
    )
    return result.fetchone()[0] > 0


def upgrade():
    """
    Add generation_item_execution_log table and final_prompt column to generation_item.
    """
    # 1. Add final_prompt column to generation_item（幂等：已存在则跳过）
    if not column_exists('generation_item', 'final_prompt'):
        op.add_column(
            'generation_item',
            sa.Column(
                'final_prompt',
                sa.Text(),
                nullable=True,
                comment='最终发送给模型的完整提示词'
            )
        )

    # 2. Create generation_item_execution_log table（幂等：已存在则跳过）
    if not table_exists('generation_item_execution_log'):
        op.create_table(
            'generation_item_execution_log',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
            sa.Column('item_id', sa.BigInteger(), nullable=False, comment='子任务ID'),
            sa.Column('node_name', sa.String(50), nullable=False, comment='节点名称: prompt_build / llm_call / image_call / save_result'),
            sa.Column(
                'node_status',
                mysql.ENUM('running', 'success', 'failed', 'skipped'),
                nullable=False,
                comment='节点状态: running / success / failed / skipped'
            ),
            sa.Column('input_data', sa.JSON(), nullable=True, comment='节点输入数据(JSON)'),
            sa.Column('output_data', sa.JSON(), nullable=True, comment='节点输出数据(JSON)'),
            sa.Column('error_data', sa.JSON(), nullable=True, comment='结构化错误信息(JSON)'),
            sa.Column('duration_ms', sa.Integer(), nullable=True, comment='耗时毫秒'),
            sa.Column('started_at', sa.DateTime(), nullable=True, comment='节点开始时间'),
            sa.Column('completed_at', sa.DateTime(), nullable=True, comment='节点完成时间'),
            sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
            sa.ForeignKeyConstraint(['item_id'], ['generation_item.id']),
            sa.PrimaryKeyConstraint('id'),
        )

        # Add index on item_id（幂等：已存在则跳过）
        if not index_exists('generation_item_execution_log', 'ix_generation_item_execution_log_item_id'):
            op.create_index(
                'ix_generation_item_execution_log_item_id',
                'generation_item_execution_log',
                ['item_id'],
            )


def downgrade():
    """
    Remove generation_item_execution_log table and final_prompt column.
    """
    # Drop the execution log table（幂等：已存在才删除）
    if index_exists('generation_item_execution_log', 'ix_generation_item_execution_log_item_id'):
        op.drop_index('ix_generation_item_execution_log_item_id', table_name='generation_item_execution_log')

    if table_exists('generation_item_execution_log'):
        op.drop_table('generation_item_execution_log')

    # Drop final_prompt column（幂等：已存在才删除）
    if column_exists('generation_item', 'final_prompt'):
        op.drop_column('generation_item', 'final_prompt')