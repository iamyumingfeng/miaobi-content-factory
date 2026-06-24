"""
Add missing fields to generation_item table (idempotent version)

Revision ID: 20260428_1800
Revises: 20260427_1700
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260428_1800'
down_revision = '20260427_1700'
branch_labels = None
depends_on = None


def upgrade():
    """
    使用 Python 检查列是否存在，然后安全地添加
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('generation_item')]

    # 需要添加的所有字段
    columns_to_add = [
        ('aigc_user_text_generator_user_prompt', sa.Text(), 'AIGC生成的文案用户提示词'),
        ('aigc_user_image_prompts_json', sa.JSON(), 'AIGC生成的图片用户提示词列表'),
        ('dedup_check_passed', sa.Boolean(), '去重检测是否通过'),
        ('dedup_similarity', sa.Float(), '最大相似度'),
        ('dedup_referenced_items_json', sa.JSON(), '相似内容引用'),
        ('dedup_checked_at', sa.DateTime(), '去重检测时间'),
        ('current_step', sa.String(length=50), '当前执行步骤'),
        ('generated_image_count', sa.Integer(), '实际生成图片数量'),
        ('output_topics', sa.JSON(), '输出话题'),
    ]

    # 添加不存在的列
    for col_name, col_type, col_comment in columns_to_add:
        if col_name not in existing_columns:
            op.add_column(
                'generation_item',
                sa.Column(col_name, col_type, nullable=True, comment=col_comment)
            )


def downgrade():
    pass

