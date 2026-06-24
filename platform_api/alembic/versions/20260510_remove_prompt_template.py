"""remove prompt_template table and related columns + fix seed_id type

Revision ID: 20260510_remove_prompt_template
Revises: 20260510_viral_type_table
Create Date: 2026-05-10

提示词模板功能已废弃，采用一次性生成方案。
本迁移移除 prompt_template 表及 generation_item 表中的外键关联字段。

同时修复 seed_id 类型：
- viral_type: 从 ENUM 改为 String(50)，支持 'auto' 随机值
- opening_seed_id/emotion_seed_id/ending_seed_id: 从 BigInteger 改为 String(50)，支持 'auto' 随机值

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '20260510_remove_prompt_template'
down_revision = '20260510_viral_type_table'
branch_labels = None
depends_on = None


def _get_foreign_keys_for_column(conn, table_name: str, column_name: str) -> list:
    """获取指定表和列的外键约束名称列表"""
    result = conn.execute(sa.text("""
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
          AND COLUMN_NAME = :column_name
          AND REFERENCED_TABLE_NAME IS NOT NULL
    """), {"table_name": table_name, "column_name": column_name})
    return [row[0] for row in result.fetchall()]


def upgrade() -> None:
    """移除 prompt_template 表和相关字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. 检查并删除 generation_item 表中的外键约束和列
    if 'generation_item' in inspector.get_table_names():
        generation_item_columns = [col['name'] for col in inspector.get_columns('generation_item')]

        if 'text_prompt_template_id' in generation_item_columns:
            # 动态获取外键约束名称
            fk_names = _get_foreign_keys_for_column(conn, 'generation_item', 'text_prompt_template_id')
            for fk_name in fk_names:
                try:
                    op.drop_constraint(fk_name, 'generation_item', type_='foreignkey')
                    print(f"Dropped foreign key: {fk_name}")
                except Exception as e:
                    print(f"Warning: Could not drop foreign key {fk_name}: {e}")
            op.drop_column('generation_item', 'text_prompt_template_id')

        if 'image_prompt_template_id' in generation_item_columns:
            # 动态获取外键约束名称
            fk_names = _get_foreign_keys_for_column(conn, 'generation_item', 'image_prompt_template_id')
            for fk_name in fk_names:
                try:
                    op.drop_constraint(fk_name, 'generation_item', type_='foreignkey')
                    print(f"Dropped foreign key: {fk_name}")
                except Exception as e:
                    print(f"Warning: Could not drop foreign key {fk_name}: {e}")
            op.drop_column('generation_item', 'image_prompt_template_id')

    # 2. 检查并删除 prompt_template 表
    table_names = inspector.get_table_names()
    if 'prompt_template' in table_names:
        op.drop_table('prompt_template')

    # ===== 修复 seed_id 类型 =====
    # 3. 删除外键约束（因为现在要存储 "auto" 字符串，不再是外键）
    try:
        op.execute("ALTER TABLE template DROP FOREIGN KEY fk_template_opening_seed")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE template DROP FOREIGN KEY fk_template_emotion_seed")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE template DROP FOREIGN KEY fk_template_ending_seed")
    except Exception:
        pass

    # 4. viral_type: 从 ENUM 改为 String(50)
    op.alter_column('template', 'viral_type',
                    existing_type=mysql.ENUM('seeding', 'review', 'tutorial', 'sharing', 'pain_point', 'story', 'lifestyle', 'before_after', 'unboxing', 'faq', 'daily', 'collection', 'hidden_gem', 'guide', 'transform', 'hack', 'wishlist', 'comparison', 'diary', 'trend', collation='utf8mb4_unicode_ci'),
                    type_=sa.String(length=50),
                    existing_nullable=True,
                    existing_comment="爆款类型：20种热门内容类型",
                    comment="爆款类型：具体类型值 或 'auto' 表示随机选择")

    # 5. opening_seed_id: 从 BigInteger 改为 String(50)
    op.alter_column('template', 'opening_seed_id',
                    existing_type=mysql.BIGINT(),
                    type_=sa.String(length=50),
                    existing_nullable=True,
                    existing_comment="指定开头模式种子ID（NULL表示随机选择）",
                    comment="开头模式：'auto'表示随机，数字字符串表示指定种子ID")

    # 6. emotion_seed_id: 从 BigInteger 改为 String(50)
    op.alter_column('template', 'emotion_seed_id',
                    existing_type=mysql.BIGINT(),
                    type_=sa.String(length=50),
                    existing_nullable=True,
                    existing_comment="指定情感基调种子ID（NULL表示随机选择）",
                    comment="情感基调：'auto'表示随机，数字字符串表示指定种子ID")

    # 7. ending_seed_id: 从 BigInteger 改为 String(50)
    op.alter_column('template', 'ending_seed_id',
                    existing_type=mysql.BIGINT(),
                    type_=sa.String(length=50),
                    existing_nullable=True,
                    existing_comment="指定结尾模式种子ID（NULL表示随机选择）",
                    comment="结尾模式：'auto'表示随机，数字字符串表示指定种子ID")

    # 8. 数据迁移：将所有 NULL 值更新为 "auto"
    op.execute("UPDATE template SET viral_type = 'auto' WHERE viral_type IS NULL")
    op.execute("UPDATE template SET opening_seed_id = 'auto' WHERE opening_seed_id IS NULL")
    op.execute("UPDATE template SET emotion_seed_id = 'auto' WHERE emotion_seed_id IS NULL")
    op.execute("UPDATE template SET ending_seed_id = 'auto' WHERE ending_seed_id IS NULL")


def downgrade() -> None:
    """重新创建 prompt_template 表和相关字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. 检查 prompt_template 表是否存在，不存在则创建
    table_names = inspector.get_table_names()
    if 'prompt_template' not in table_names:
        op.create_table(
            'prompt_template',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(100), nullable=False, comment='模板名称'),
            sa.Column('type', sa.Enum('text', 'image', name='prompt_template_type_enum'), nullable=False, comment='模板类型：text(文案)/image(图片)'),
            sa.Column('content', sa.Text(), nullable=False, comment='模板内容'),
            sa.Column('description', sa.String(500), nullable=True, comment='模板描述'),
            sa.Column('status', sa.Enum('active', 'inactive', name='prompt_template_status_enum'), nullable=False, default='active', comment='状态'),
            sa.Column('owner_operator_id', sa.BigInteger(), nullable=False, comment='所属运营管理员ID'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], name='fk_prompt_template_owner_operator_id'),
            sa.PrimaryKeyConstraint('id'),
            comment='提示词模板表'
        )

    # 2. 检查 generation_item 表中的列，不存在则添加
    if 'generation_item' in inspector.get_table_names():
        generation_item_columns = [col['name'] for col in inspector.get_columns('generation_item')]

        if 'text_prompt_template_id' not in generation_item_columns:
            op.add_column('generation_item', sa.Column('text_prompt_template_id', sa.BigInteger(), nullable=True, comment='文案提示词模板ID'))

        if 'image_prompt_template_id' not in generation_item_columns:
            op.add_column('generation_item', sa.Column('image_prompt_template_id', sa.BigInteger(), nullable=True, comment='图片提示词模板ID'))

        # 添加外键约束（仅在列刚添加时）
        if 'text_prompt_template_id' not in generation_item_columns:
            try:
                op.create_foreign_key('fk_generation_item_text_prompt_template_id', 'generation_item', 'prompt_template', ['text_prompt_template_id'], ['id'])
            except Exception:
                pass

        if 'image_prompt_template_id' not in generation_item_columns:
            try:
                op.create_foreign_key('fk_generation_item_image_prompt_template_id', 'generation_item', 'prompt_template', ['image_prompt_template_id'], ['id'])
            except Exception:
                pass

    # ===== 回滚 seed_id 类型 =====
    # 1. 先将 "auto" 值转回 NULL
    op.execute("UPDATE template SET viral_type = NULL WHERE viral_type = 'auto'")
    op.execute("UPDATE template SET opening_seed_id = NULL WHERE opening_seed_id = 'auto'")
    op.execute("UPDATE template SET emotion_seed_id = NULL WHERE emotion_seed_id = 'auto'")
    op.execute("UPDATE template SET ending_seed_id = NULL WHERE ending_seed_id = 'auto'")

    # 2. 回滚：从 String(50) 改回 BigInteger
    op.alter_column('template', 'ending_seed_id',
                    existing_type=sa.String(length=50),
                    type_=mysql.BIGINT(),
                    existing_nullable=True)

    op.alter_column('template', 'emotion_seed_id',
                    existing_type=sa.String(length=50),
                    type_=mysql.BIGINT(),
                    existing_nullable=True)

    op.alter_column('template', 'opening_seed_id',
                    existing_type=sa.String(length=50),
                    type_=mysql.BIGINT(),
                    existing_nullable=True)

    # 3. 回滚 viral_type 到 ENUM 类型
    op.alter_column('template', 'viral_type',
                    existing_type=sa.String(length=50),
                    type_=mysql.ENUM('seeding', 'review', 'tutorial', 'sharing', 'pain_point', 'story', 'lifestyle', 'before_after', 'unboxing', 'faq', 'daily', 'collection', 'hidden_gem', 'guide', 'transform', 'hack', 'wishlist', 'comparison', 'diary', 'trend', collation='utf8mb4_unicode_ci'),
                    existing_nullable=True)
