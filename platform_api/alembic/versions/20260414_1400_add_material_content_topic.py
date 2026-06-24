"""add material content and topic fields

Revision ID: 20260414_1400
Revises: 20260413_1200
Create Date: 2026-04-14 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260414_1400'
down_revision = 'add_system_classification_fields'
branch_labels = None
depends_on = None


def upgrade():
    # 使用 bind 获取连接
    conn = op.get_bind()

    # 检查 content 字段是否已存在
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'material'
        AND COLUMN_NAME = 'content'
    """))
    content_exists = result.scalar() > 0

    # 检查 topic 字段是否已存在
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'material'
        AND COLUMN_NAME = 'topic'
    """))
    topic_exists = result.scalar() > 0

    # 只添加不存在的字段
    if not content_exists:
        op.add_column('material', sa.Column('content', sa.Text(), nullable=True, comment='素材内容（必填）'))

    if not topic_exists:
        op.add_column('material', sa.Column('topic', sa.String(255), nullable=True, comment='素材话题（必选）'))

    # 为现有数据设置默认值（只有当字段是新添加的时候才执行）
    if not content_exists:
        op.execute("UPDATE material SET content = text_content WHERE content IS NULL OR content = ''")

    if not topic_exists:
        op.execute("UPDATE material SET topic = '默认话题' WHERE topic IS NULL OR topic = ''")

    # 只对新添加的字段设置为 NOT NULL
    if not content_exists:
        op.alter_column('material', 'content', nullable=False)

    if not topic_exists:
        op.alter_column('material', 'topic', nullable=False)


def downgrade():
    op.drop_column('material', 'topic')
    op.drop_column('material', 'content')
