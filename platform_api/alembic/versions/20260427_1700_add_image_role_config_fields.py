"""
Add image role config fields for interactive editing

Revision ID: 20260427_1700
Revises: 20260427_1600
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260427_1700'
down_revision = '20260427_1600'
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
    # 为 generation_task 表添加图片角色配置字段（幂等：已存在则跳过）
    if not column_exists('generation_task', 'benchmark_image_roles_json'):
        op.add_column('generation_task', sa.Column('benchmark_image_roles_json', sa.JSON(), nullable=True, comment='对标图角色配置'))
    if not column_exists('generation_task', 'template_product_mapping_json'):
        op.add_column('generation_task', sa.Column('template_product_mapping_json', sa.JSON(), nullable=True, comment='模板产品映射'))

    # 为 generation_item 表添加图片角色配置快照字段（幂等：已存在则跳过）
    if not column_exists('generation_item', 'input_benchmark_image_roles_json'):
        op.add_column('generation_item', sa.Column('input_benchmark_image_roles_json', sa.JSON(), nullable=True, comment='对标图角色配置快照'))
    if not column_exists('generation_item', 'input_template_product_mapping_json'):
        op.add_column('generation_item', sa.Column('input_template_product_mapping_json', sa.JSON(), nullable=True, comment='模板产品映射快照'))


def downgrade():
    # 从 generation_task 表删除图片角色配置字段
    if column_exists('generation_task', 'template_product_mapping_json'):
        op.drop_column('generation_task', 'template_product_mapping_json')
    if column_exists('generation_task', 'benchmark_image_roles_json'):
        op.drop_column('generation_task', 'benchmark_image_roles_json')

    # 从 generation_item 表删除图片角色配置快照字段
    if column_exists('generation_item', 'input_template_product_mapping_json'):
        op.drop_column('generation_item', 'input_template_product_mapping_json')
    if column_exists('generation_item', 'input_benchmark_image_roles_json'):
        op.drop_column('generation_item', 'input_benchmark_image_roles_json')
