"""update_distribution_status_enum

Revision ID: 20260505_2000
Revises: 20260428_1900
Create Date: 2026-05-05 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '20260505_2000'
down_revision = '20260428_1900'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 更新枚举类型，添加新状态 - MySQL 版本
    # 注意：在 MySQL 中修改枚举需要指定完整列表

    # 1. 更新 generation_item 表
    op.execute("""
        ALTER TABLE generation_item
        MODIFY COLUMN distribution_status ENUM('draft', 'ready', 'distributed', 'pending_publish', 'published')
        NOT NULL DEFAULT 'draft'
        COMMENT '分发状态：draft(草稿)/ready(待分发)/distributed(已分发)/pending_publish(待发布)/published(已发布)'
    """)

    # 2. 更新 distribution 表
    op.execute("""
        ALTER TABLE distribution
        MODIFY COLUMN status ENUM('pending', 'distributed', 'pending_publish', 'published')
        NOT NULL DEFAULT 'pending'
    """)

    # 3. 数据迁移：将所有已完成(status='completed')的子任务设置为待发布状态
    # 同时确保 distribution_status 不在 ('pending_publish', 'published') 中，避免重复更新
    op.execute("""
        UPDATE generation_item
        SET distribution_status = 'pending_publish'
        WHERE status = 'completed'
        AND distribution_status NOT IN ('pending_publish', 'published')
    """)


def downgrade() -> None:
    # 降级 - 回滚到之前的状态
    op.execute("""
        ALTER TABLE generation_item
        MODIFY COLUMN distribution_status ENUM('pending', 'distributed', 'published')
        NOT NULL DEFAULT 'pending'
    """)
    op.execute("""
        ALTER TABLE distribution
        MODIFY COLUMN status ENUM('pending', 'distributed', 'published')
        NOT NULL DEFAULT 'pending'
    """)
