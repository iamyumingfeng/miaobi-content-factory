"""add creative_seed fields to material

Revision ID: 20260509_material_seed
Revises: 20260509_creative_seed
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260509_material_seed'
down_revision = '20260509_creative_seed'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """检测列是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name, index_name):
    """检测索引是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade():
    # 添加创意种子关联字段（检测是否存在）
    if not column_exists('material', 'creative_seed_id'):
        op.add_column(
            'material',
            sa.Column('creative_seed_id', sa.BigInteger(), nullable=True, comment='关联的创意种子ID（用于指定开头/情感/结尾模式）')
        )

    # 创建外键（检测是否存在）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('material')]
    if 'fk_material_creative_seed' not in existing_fks:
        op.create_foreign_key(
            'fk_material_creative_seed',
            'material',
            'creative_seed',
            ['creative_seed_id'],
            ['id']
        )

    # 创建索引（检测是否存在）
    if not index_exists('material', 'ix_material_creative_seed'):
        op.create_index(
            'ix_material_creative_seed',
            'material',
            ['creative_seed_id']
        )

    # 添加产品卖点字段（检测是否存在）
    if not column_exists('material', 'product_selling_points'):
        op.add_column(
            'material',
            sa.Column('product_selling_points', sa.Text(), nullable=True, comment='产品卖点描述（用于文案生成时强调重点）')
        )


def downgrade():
    # 删除产品卖点字段
    if column_exists('material', 'product_selling_points'):
        op.drop_column('material', 'product_selling_points')

    # 删除创意种子关联字段
    if index_exists('material', 'ix_material_creative_seed'):
        op.drop_index('ix_material_creative_seed', 'material')

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('material')]
    if 'fk_material_creative_seed' in existing_fks:
        op.drop_constraint('fk_material_creative_seed', 'material', type_='foreignkey')

    if column_exists('material', 'creative_seed_id'):
        op.drop_column('material', 'creative_seed_id')
