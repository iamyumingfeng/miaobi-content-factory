"""extend viral_type enum to 20 types

Revision ID: 20260510_viral_type_extend
Revises: 20260509_viral_template
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260510_viral_type_extend'
down_revision = '20260509_viral_template'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """检测列是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """
    扩展 viral_type 枚举到 20 种类型

    MySQL 不支持直接修改 ENUM 类型，需要使用 ALTER TABLE MODIFY COLUMN
    """
    conn = op.get_bind()

    # 检测列是否存在
    if not column_exists('template', 'viral_type'):
        print("Column 'viral_type' does not exist, skipping migration.")
        return

    # MySQL: 直接修改列定义来更新 ENUM 值
    # 新的 ENUM 包含 20 种类型
    op.execute("""
        ALTER TABLE template
        MODIFY COLUMN viral_type ENUM(
            'seeding',       -- 种草安利型
            'review',        -- 测评对比型
            'tutorial',      -- 教程攻略型
            'sharing',       -- 好物分享型
            'pain_point',    -- 痛点解决方案型
            'story',         -- 故事叙述型
            'lifestyle',     -- 生活场景型
            'before_after',  -- 前后对比型
            'unboxing',      -- 开箱体验型
            'faq',           -- 答疑解惑型
            'daily',         -- 日常记录型
            'collection',    -- 合集盘点型
            'hidden_gem',    -- 宝藏发现型
            'guide',         -- 新手指南型
            'transform',     -- 改造焕新型
            'hack',          -- 小妙招型
            'wishlist',      -- 许愿清单型
            'comparison',    -- 横评选购型
            'diary',         -- 日记打卡型
            'trend'          -- 热门趋势型
        )
        DEFAULT 'seeding'
        COMMENT '爆款类型：20种热门内容类型'
    """)


def downgrade():
    """回滚到原来的 7 种类型"""
    if not column_exists('template', 'viral_type'):
        return

    # 注意：如果数据库中已有新类型的值，回滚会失败
    op.execute("""
        ALTER TABLE template
        MODIFY COLUMN viral_type ENUM(
            'seeding',
            'review',
            'tutorial',
            'sharing',
            'pain_point',
            'story',
            'other'
        )
        DEFAULT 'seeding'
        COMMENT '爆款类型'
    """)
