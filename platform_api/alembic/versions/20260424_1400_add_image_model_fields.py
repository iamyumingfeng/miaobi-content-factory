"""add image model fields to generation task

Revision ID: 20260424_1400
Revises: 20260424_1000
Create Date: 2026-04-24 14:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260424_1400'
down_revision = '20260424_1000'
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
    # 添加图片模型字段到 generation_task 表
    if not column_exists('generation_task', 'image_model_platform'):
        op.add_column('generation_task', sa.Column('image_model_platform', sa.String(100), nullable=True, comment='选择的图片模型平台'))
    if not column_exists('generation_task', 'image_model_id'):
        op.add_column('generation_task', sa.Column('image_model_id', sa.String(100), nullable=True, comment='选择的图片模型'))
    # 添加图片模型字段到 generation_item 表
    if not column_exists('generation_item', 'image_model_platform'):
        op.add_column('generation_item', sa.Column('image_model_platform', sa.String(100), nullable=True, comment='选择的图片模型平台'))
    if not column_exists('generation_item', 'image_model_id'):
        op.add_column('generation_item', sa.Column('image_model_id', sa.String(100), nullable=True, comment='选择的图片模型'))


def downgrade():
    op.drop_column('generation_task', 'image_model_id')
    op.drop_column('generation_task', 'image_model_platform')
    op.drop_column('generation_item', 'image_model_id')
    op.drop_column('generation_item', 'image_model_platform')