"""add embedding model type

Revision ID: 20260506_1000
Revises: 20260505_2000
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260506_1000'
down_revision = '20260505_2000'
branch_labels = None
depends_on = None


def upgrade():
    """添加 embedding 模型类型到 model_type_enum 枚举"""

    # MySQL 修改枚举类型需要重新定义整个枚举
    # model_config 表
    op.execute("""
        ALTER TABLE model_config
        MODIFY COLUMN model_type ENUM('llm', 'image', 'video', 'embedding')
        NOT NULL COMMENT '模型类型：llm / image / video / embedding'
    """)

    # user_default_model 表
    op.execute("""
        ALTER TABLE user_default_model
        MODIFY COLUMN model_type ENUM('llm', 'image', 'video', 'embedding')
        NOT NULL COMMENT '模型类型：llm / image / video / embedding'
    """)


def downgrade():
    """回滚：移除 embedding 模型类型"""

    # 先删除 embedding 类型的记录
    op.execute("DELETE FROM model_config WHERE model_type = 'embedding'")
    op.execute("DELETE FROM user_default_model WHERE model_type = 'embedding'")

    # 恢复原来的枚举定义
    op.execute("""
        ALTER TABLE model_config
        MODIFY COLUMN model_type ENUM('llm', 'image', 'video')
        NOT NULL COMMENT '模型类型：llm / image / video'
    """)

    op.execute("""
        ALTER TABLE user_default_model
        MODIFY COLUMN model_type ENUM('llm', 'image', 'video')
        NOT NULL COMMENT '模型类型：llm / image / video'
    """)
