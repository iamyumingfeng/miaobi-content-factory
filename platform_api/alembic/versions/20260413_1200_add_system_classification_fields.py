"""add_system_classification_fields

添加系统默认分类字段：
- template_platform 添加 is_system 字段
- template_tag 添加 is_system 和 platform_id 字段
- material_tag 添加 is_system 字段

为现有运营管理员创建默认"未分类"平台和"无标签"标签

Revision ID: add_system_classification_fields
Revises: add_login_failure_tracking
Create Date: 2026-04-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_system_classification_fields'
down_revision: Union[str, None] = 'add_login_failure_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 添加 template_platform 表的 is_system 字段
    op.add_column('template_platform', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'))

    # 2. 添加 template_tag 表的新字段
    op.add_column('template_tag', sa.Column('platform_id', sa.BigInteger(), sa.ForeignKey('template_platform.id'), nullable=True))
    op.add_column('template_tag', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'))

    # 3. 添加 material_tag 表的 is_system 字段
    op.add_column('material_tag', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'))

    # 4. 为现有运营管理员创建默认分类
    # 使用 raw SQL 执行数据迁移
    conn = op.get_bind()

    # 获取所有运营管理员 ID
    operators = conn.execute(sa.text("SELECT id FROM operator")).fetchall()

    for operator in operators:
        operator_id = operator[0]

        # 创建默认"未分类"平台
        result = conn.execute(sa.text("""
            INSERT INTO template_platform (name, description, color, sort_order, is_system, created_by, owner_operator_id, created_at, updated_at)
            VALUES ('未分类', '系统默认平台分类，未设置平台的模板将归类到此', '#909399', 0, 1, :operator_id, :operator_id, NOW(), NOW())
        """), {'operator_id': operator_id})

        platform_id = result.lastrowid

        # 为该平台创建默认"无标签"标签
        conn.execute(sa.text("""
            INSERT INTO template_tag (name, description, color, platform_id, is_system, created_by, created_at, updated_at)
            VALUES ('无标签', '系统默认标签，未设置标签的模板将归类到此', '#909399', :platform_id, 1, :operator_id, NOW(), NOW())
        """), {'platform_id': platform_id, 'operator_id': operator_id})

        # 创建素材的默认"无标签"标签
        conn.execute(sa.text("""
            INSERT INTO material_tag (name, description, color, is_system, owner_operator_id, created_by, created_at, updated_at)
            VALUES ('无标签', '系统默认标签，未设置标签的素材将归类到此', '#909399', 1, :operator_id, :operator_id, NOW(), NOW())
        """), {'operator_id': operator_id})

    # 5. 更新现有模板的关联（未设置平台的模板关联到默认未分类平台）
    # 这里暂时不处理，因为现有模板可能有 platform_id 或没有

    # 6. 更新现有标签，将它们关联到对应的平台（如果需要）
    # 现有标签的 platform_id 保持为 NULL，表示通用标签


def downgrade() -> None:
    # 删除创建的默认分类数据
    conn = op.get_bind()

    # 删除默认标签
    conn.execute(sa.text("DELETE FROM template_tag WHERE is_system = 1"))
    conn.execute(sa.text("DELETE FROM material_tag WHERE is_system = 1"))

    # 删除默认平台
    conn.execute(sa.text("DELETE FROM template_platform WHERE is_system = 1"))

    # 删除字段
    op.drop_column('material_tag', 'is_system')
    op.drop_column('template_tag', 'is_system')
    op.drop_column('template_tag', 'platform_id')
    op.drop_column('template_platform', 'is_system')
