"""Add image_model fields to generation_item

Revision ID: 20260423_1600
Revises: 20260422_1100
Create Date: 2026-04-23 16:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260423_1600'
down_revision = '20260422_1100'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查字段是否已存在，避免重复添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('generation_item')]

    # 添加图片模型平台字段
    if 'image_model_platform' not in existing_columns:
        op.add_column('generation_item', sa.Column('image_model_platform', sa.String(100), nullable=True, comment='实际使用的图片模型平台'))

    # 添加图片模型ID字段
    if 'image_model_id' not in existing_columns:
        op.add_column('generation_item', sa.Column('image_model_id', sa.String(100), nullable=True, comment='实际使用的图片模型'))


def downgrade() -> None:
    op.drop_column('generation_item', 'image_model_id')
    op.drop_column('generation_item', 'image_model_platform')
