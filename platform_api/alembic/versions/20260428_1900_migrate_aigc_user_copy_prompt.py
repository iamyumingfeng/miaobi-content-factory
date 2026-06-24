"""
Migrate data from aigc_user_copy_prompt to aigc_user_text_generator_user_prompt

Revision ID: 20260428_1900
Revises: 20260428_1800
Create Date: 2026-04-28
"""
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260428_1900'
down_revision = '20260428_1800'
branch_labels = None
depends_on = None


def upgrade():
    """
    将 aigc_user_copy_prompt 字段的数据迁移到 aigc_user_text_generator_user_prompt
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('generation_item')]

    # 检查旧字段是否存在
    if 'aigc_user_copy_prompt' in existing_columns and 'aigc_user_text_generator_user_prompt' in existing_columns:
        # 复制数据
        op.execute("""
            UPDATE generation_item
            SET aigc_user_text_generator_user_prompt = aigc_user_copy_prompt
            WHERE aigc_user_copy_prompt IS NOT NULL
              AND aigc_user_text_generator_user_prompt IS NULL
        """)


def downgrade():
    pass
