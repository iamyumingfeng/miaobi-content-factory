"""
Add category tables for 3-level hierarchy (Platform -> Category -> Tag)

Revision ID: 20260416_1500
Revises: 20260415_0400
Create Date: 2025-04-16 15:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260416_1500'
down_revision = '20260415_0400'
branch_labels = None
depends_on = None


def upgrade():
    # ============================================
    # 1. Create category_platform table (统一平台表)
    # ============================================
    op.create_table(
        'category_platform',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='平台名称'),
        sa.Column('description', sa.String(500), nullable=True, comment='平台描述'),
        sa.Column('color', sa.String(20), nullable=True, comment='平台颜色'),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0, comment='排序权重'),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='创建者运营管理员ID'),
        sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, comment='所属运营管理员ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_operator_id', 'name', name='uq_platform_owner_name')
    )
    op.create_index('ix_category_platform_owner', 'category_platform', ['owner_operator_id'])

    # ============================================
    # 2. Create material_category table (素材分类表)
    # ============================================
    op.create_table(
        'material_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='分类名称'),
        sa.Column('description', sa.String(500), nullable=True, comment='分类描述'),
        sa.Column('color', sa.String(20), nullable=True, comment='分类颜色'),
        sa.Column('platform_id', sa.BigInteger(), sa.ForeignKey('category_platform.id'), nullable=False, comment='所属平台ID'),
        sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, comment='所属运营管理员ID'),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='创建者运营管理员ID'),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0, comment='排序'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_operator_id', 'name', name='uq_material_category_owner_name')
    )
    op.create_index('ix_material_category_platform', 'material_category', ['platform_id'])
    op.create_index('ix_material_category_owner', 'material_category', ['owner_operator_id'])

    # ============================================
    # 3. Create template_category table (模板分类表)
    # ============================================
    op.create_table(
        'template_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='分类名称'),
        sa.Column('description', sa.String(500), nullable=True, comment='分类描述'),
        sa.Column('color', sa.String(20), nullable=True, comment='分类颜色'),
        sa.Column('platform_id', sa.BigInteger(), sa.ForeignKey('category_platform.id'), nullable=False, comment='所属平台ID'),
        sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, comment='所属运营管理员ID'),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='创建者运营管理员ID'),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0, comment='排序'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_operator_id', 'name', name='uq_template_category_owner_name')
    )
    op.create_index('ix_template_category_platform', 'template_category', ['platform_id'])
    op.create_index('ix_template_category_owner', 'template_category', ['owner_operator_id'])

    # ============================================
    # 4. Add category_id to material_tag (暂时允许NULL用于迁移)
    # ============================================
    op.add_column(
        'material_tag',
        sa.Column('category_id', sa.BigInteger(), nullable=True, comment='所属分类ID')
    )
    op.create_index('ix_material_tag_category', 'material_tag', ['category_id'])
    op.create_foreign_key(
        'fk_material_tag_category',
        'material_tag',
        'material_category',
        ['category_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # ============================================
    # 5. Add category_id to template_tag (暂时允许NULL用于迁移)
    # ============================================
    op.add_column(
        'template_tag',
        sa.Column('category_id', sa.BigInteger(), nullable=True, comment='所属分类ID')
    )
    op.create_index('ix_template_tag_category', 'template_tag', ['category_id'])
    op.create_foreign_key(
        'fk_template_tag_category',
        'template_tag',
        'template_category',
        ['category_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop template_tag category_id
    op.drop_constraint('fk_template_tag_category', 'template_tag', type_='foreignkey')
    op.drop_index('ix_template_tag_category', table_name='template_tag')
    op.drop_column('template_tag', 'category_id')

    # Drop material_tag category_id
    op.drop_constraint('fk_material_tag_category', 'material_tag', type_='foreignkey')
    op.drop_index('ix_material_tag_category', table_name='material_tag')
    op.drop_column('material_tag', 'category_id')

    # Drop template_category table
    op.drop_table('template_category')

    # Drop material_category table
    op.drop_table('material_category')

    # Drop category_platform table
    op.drop_table('category_platform')
