"""
Add benchmark config fields for generation tasks

Revision ID: 20260427_1600
Revises: 20260427_1500
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260427_1600'
down_revision = '20260427_1500'
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
    # 为 generation_task 表添加对标配置字段（幂等：已存在则跳过）
    if not column_exists('generation_task', 'benchmark_text_enabled'):
        op.add_column('generation_task', sa.Column('benchmark_text_enabled', sa.Boolean(), nullable=True, server_default=sa.text('true'), comment='文案对标开关'))
    if not column_exists('generation_task', 'benchmark_image_enabled'):
        op.add_column('generation_task', sa.Column('benchmark_image_enabled', sa.Boolean(), nullable=True, server_default=sa.text('true'), comment='图片对标开关'))
    if not column_exists('generation_task', 'benchmark_image_reference_options'):
        op.add_column('generation_task', sa.Column('benchmark_image_reference_options', sa.JSON(), nullable=True, comment='图片参考选项（构图/场景/风格）'))

    # 为 generation_item 表添加对标配置字段（用于存储每个子任务的对标配置快照）
    if not column_exists('generation_item', 'input_benchmark_text_enabled'):
        op.add_column('generation_item', sa.Column('input_benchmark_text_enabled', sa.Boolean(), nullable=True, comment='文案对标开关'))
    if not column_exists('generation_item', 'input_benchmark_image_enabled'):
        op.add_column('generation_item', sa.Column('input_benchmark_image_enabled', sa.Boolean(), nullable=True, comment='图片对标开关'))
    if not column_exists('generation_item', 'input_benchmark_image_reference_options'):
        op.add_column('generation_item', sa.Column('input_benchmark_image_reference_options', sa.JSON(), nullable=True, comment='图片参考选项'))


def downgrade():
    # 从 generation_task 表删除对标配置字段
    if column_exists('generation_task', 'benchmark_image_reference_options'):
        op.drop_column('generation_task', 'benchmark_image_reference_options')
    if column_exists('generation_task', 'benchmark_image_enabled'):
        op.drop_column('generation_task', 'benchmark_image_enabled')
    if column_exists('generation_task', 'benchmark_text_enabled'):
        op.drop_column('generation_task', 'benchmark_text_enabled')

    # 从 generation_item 表删除对标配置字段
    if column_exists('generation_item', 'input_benchmark_image_reference_options'):
        op.drop_column('generation_item', 'input_benchmark_image_reference_options')
    if column_exists('generation_item', 'input_benchmark_image_enabled'):
        op.drop_column('generation_item', 'input_benchmark_image_enabled')
    if column_exists('generation_item', 'input_benchmark_text_enabled'):
        op.drop_column('generation_item', 'input_benchmark_text_enabled')
