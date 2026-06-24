"""creative_seed template field to Text

Revision ID: 20260511_seed_template_text
Revises: 20260510_remove_prompt_template
Create Date: 2026-05-11 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260511_seed_template_text'
down_revision = '20260510_remove_prompt_template'
branch_labels = None
depends_on = None


def upgrade():
    """
    将 creative_seed 表的 template 字段从 String(500) 改为 Text，
    以支持存储多个模板的 JSON 数组格式。
    """
    # 修改 template 字段类型
    op.alter_column(
        'creative_seed',
        'template',
        existing_type=sa.String(500),
        type_=sa.Text,
        existing_nullable=False,
        comment='模板示例（JSON数组格式，如：[\'没想到这个xxx居然...\', \'谁能想到xxx竟然...\']）'
    )


def downgrade():
    """
    回滚：将 template 字段改回 String(500)
    注意：如果数据中包含超过500字符的JSON，回滚会失败
    """
    op.alter_column(
        'creative_seed',
        'template',
        existing_type=sa.Text,
        type_=sa.String(500),
        existing_nullable=False,
        comment='模板示例（如：没想到这个xxx居然...）'
    )
