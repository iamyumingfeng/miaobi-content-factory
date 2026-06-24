"""
Migrate data from 2-level to 3-level structure and clean up old fields

Step 1: Migrate MaterialTag data (parent_id -> platform + category)
Step 2: Migrate TemplatePlatform data -> CategoryPlatform
Step 3: Create default TemplateCategory for each platform
Step 4: Migrate TemplateTag.platform_id -> category_id
Step 5: Drop old fields (parent_id from material_tag)

Revision ID: 20260416_1501
Revises: 20260416_1500
Create Date: 2025-04-16 15:01:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '20260416_1501'
down_revision = '20260416_1500'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ============================================
    # Step 1: Migrate MaterialTag (2层 -> 3层)
    # 策略: parent_id=NULL 的记录 -> CategoryPlatform
    #       parent_id!=NULL 的记录 -> MaterialCategory
    # ============================================

    # 1a. 将一级标签 (parent_id IS NULL) 迁移到 category_platform
    conn.execute(text("""
        INSERT INTO category_platform (name, description, color, sort_order, created_by, owner_operator_id, created_at, updated_at)
        SELECT name, description, color, 0, created_by, owner_operator_id, created_at, updated_at
        FROM material_tag
        WHERE parent_id IS NULL
    """))

    # 1b. 将二级标签 (parent_id IS NOT NULL) 迁移到 material_category
    # 关联到对应的 category_platform (通过 parent_id 找到对应的一级标签)
    conn.execute(text("""
        INSERT INTO material_category (name, description, color, platform_id, sort_order, created_by, owner_operator_id, created_at, updated_at)
        SELECT 
            mt.name, 
            mt.description, 
            mt.color, 
            cp.id AS platform_id,
            0,
            mt.created_by, 
            mt.owner_operator_id, 
            mt.created_at, 
            mt.updated_at
        FROM material_tag mt
        JOIN material_tag parent_mt ON mt.parent_id = parent_mt.id
        JOIN category_platform cp ON cp.name = parent_mt.name 
            AND cp.owner_operator_id = parent_mt.owner_operator_id
        WHERE mt.parent_id IS NOT NULL
    """))

    # 1c. 更新 material_tag 的 category_id (MySQL JOIN 语法)
    conn.execute(text("""
        UPDATE material_tag mt
        JOIN material_category mc ON mt.name = mc.name 
            AND mt.owner_operator_id = mc.owner_operator_id
        SET mt.category_id = mc.id
        WHERE mt.parent_id IS NOT NULL
            AND mt.category_id IS NULL
    """))

    # ============================================
    # Step 2: Migrate TemplatePlatform -> CategoryPlatform
    # 使用 INSERT IGNORE 避免与 Step 1a 已插入的平台名冲突
    # ============================================
    conn.execute(text("""
        INSERT IGNORE INTO category_platform (name, description, color, sort_order, created_by, owner_operator_id, created_at, updated_at)
        SELECT name, description, color, sort_order, created_by, owner_operator_id, created_at, updated_at
        FROM template_platform
    """))

    # ============================================
    # Step 3: Create default TemplateCategory for each TemplatePlatform
    # ============================================
    conn.execute(text("""
        INSERT INTO template_category (name, description, platform_id, owner_operator_id, created_by, sort_order, created_at, updated_at)
        SELECT 
            '默认分类',
            '系统自动创建的默认分类',
            cp.id,
            tp.owner_operator_id,
            tp.created_by,
            0,
            NOW(),
            NOW()
        FROM template_platform tp
        JOIN category_platform cp ON cp.name = tp.name 
            AND cp.owner_operator_id = tp.owner_operator_id
    """))

    # ============================================
    # Step 4: Assign TemplateTags to a default category
    # 
    # 注意: template_tag 表原本没有 platform_id 列，无法确定归属
    # 策略: 将所有现有标签分配给第一个可用的默认分类
    # ============================================
    conn.execute(text("""
        UPDATE template_tag tt
        SET tt.category_id = (
            SELECT tc.id 
            FROM template_category tc 
            WHERE tc.name = '默认分类'
            ORDER BY tc.id
            LIMIT 1
        )
        WHERE tt.category_id IS NULL
            AND EXISTS (SELECT 1 FROM template_category WHERE name = '默认分类')
    """))

    # ============================================
    # Step 5: Drop old parent_id from material_tag
    # ============================================
    op.drop_constraint('fk_material_tag_parent', 'material_tag', type_='foreignkey')
    op.drop_index('ix_material_tag_parent_id', table_name='material_tag')
    op.drop_column('material_tag', 'parent_id')

    # ============================================
    # Step 6: Drop old platform_id from template_tag (可选，暂保留兼容)
    # ============================================
    # 暂不删除 template_tag.platform_id，保持向后兼容
    # 后续版本确认无问题后可删除


def downgrade():
    # 注意: 数据回滚需要手动恢复，此 migration 不可逆
    # 恢复 parent_id 字段
    op.add_column(
        'material_tag',
        sa.Column(
            'parent_id',
            sa.BigInteger(),
            nullable=True,
            comment='父标签ID'
        )
    )
    op.create_index('ix_material_tag_parent_id', 'material_tag', ['parent_id'])
    op.create_foreign_key(
        'fk_material_tag_parent',
        'material_tag',
        'material_tag',
        ['parent_id'],
        ['id'],
        ondelete='SET NULL'
    )
