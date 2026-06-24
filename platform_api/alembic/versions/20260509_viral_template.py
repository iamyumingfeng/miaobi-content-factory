"""add viral template fields

Revision ID: 20260509_viral_template
Revises: 20260509_material_seed
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260509_viral_template'
down_revision = '20260509_material_seed'
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


def enum_exists(enum_name):
    """检测ENUM类型是否存在（MySQL）"""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"SHOW TYPE FROM mysql.enum WHERE name = '{enum_name}'")).fetchone()
    return result is not None


def upgrade():
    # 添加爆款类型字段（检测是否存在）
    if not column_exists('template', 'viral_type'):
        op.add_column(
            'template',
            sa.Column(
                'viral_type',
                sa.Enum(
                    'seeding', 'review', 'tutorial', 'sharing',
                    'pain_point', 'story', 'other',
                    name='viral_type_enum'
                ),
                nullable=True,
                server_default='seeding',
                comment='爆款类型'
            )
        )

    # 添加创意种子关联字段（检测是否存在）
    if not column_exists('template', 'opening_seed_id'):
        op.add_column(
            'template',
            sa.Column('opening_seed_id', sa.BigInteger(), nullable=True, comment='指定开头模式种子ID')
        )
    if not column_exists('template', 'emotion_seed_id'):
        op.add_column(
            'template',
            sa.Column('emotion_seed_id', sa.BigInteger(), nullable=True, comment='指定情感基调种子ID')
        )
    if not column_exists('template', 'ending_seed_id'):
        op.add_column(
            'template',
            sa.Column('ending_seed_id', sa.BigInteger(), nullable=True, comment='指定结尾模式种子ID')
        )

    # 创建外键约束（检测是否存在）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('template')]

    if 'fk_template_opening_seed' not in existing_fks:
        op.create_foreign_key(
            'fk_template_opening_seed',
            'template',
            'creative_seed',
            ['opening_seed_id'],
            ['id']
        )
    if 'fk_template_emotion_seed' not in existing_fks:
        op.create_foreign_key(
            'fk_template_emotion_seed',
            'template',
            'creative_seed',
            ['emotion_seed_id'],
            ['id']
        )
    if 'fk_template_ending_seed' not in existing_fks:
        op.create_foreign_key(
            'fk_template_ending_seed',
            'template',
            'creative_seed',
            ['ending_seed_id'],
            ['id']
        )

    # 创建索引（检测是否存在）
    if not index_exists('template', 'ix_template_opening_seed'):
        op.create_index('ix_template_opening_seed', 'template', ['opening_seed_id'])
    if not index_exists('template', 'ix_template_emotion_seed'):
        op.create_index('ix_template_emotion_seed', 'template', ['emotion_seed_id'])
    if not index_exists('template', 'ix_template_ending_seed'):
        op.create_index('ix_template_ending_seed', 'template', ['ending_seed_id'])
    if not index_exists('template', 'ix_template_viral_type'):
        op.create_index('ix_template_viral_type', 'template', ['viral_type'])

    # 添加产品卖点字段（检测是否存在）
    if not column_exists('template', 'product_selling_points'):
        op.add_column(
            'template',
            sa.Column('product_selling_points', sa.Text(), nullable=True, comment='产品卖点描述')
        )

    # 添加爆款指数字段（检测是否存在）
    if not column_exists('template', 'viral_score'):
        op.add_column(
            'template',
            sa.Column('viral_score', sa.Float(), nullable=True, server_default='0', comment='爆款指数')
        )

    # 添加爆款标签字段（检测是否存在）
    if not column_exists('template', 'viral_tags'):
        op.add_column(
            'template',
            sa.Column('viral_tags', sa.JSON(), nullable=True, comment='爆款标签JSON数组')
        )

    # 添加统计字段（检测是否存在）
    if not column_exists('template', 'use_count'):
        op.add_column(
            'template',
            sa.Column('use_count', sa.BigInteger(), nullable=False, server_default='0', comment='使用次数统计')
        )
    if not column_exists('template', 'success_count'):
        op.add_column(
            'template',
            sa.Column('success_count', sa.BigInteger(), nullable=False, server_default='0', comment='成功生成次数')
        )


def downgrade():
    # 删除统计字段
    if column_exists('template', 'success_count'):
        op.drop_column('template', 'success_count')
    if column_exists('template', 'use_count'):
        op.drop_column('template', 'use_count')

    # 删除爆款标签字段
    if column_exists('template', 'viral_tags'):
        op.drop_column('template', 'viral_tags')
    if column_exists('template', 'viral_score'):
        op.drop_column('template', 'viral_score')
    if column_exists('template', 'product_selling_points'):
        op.drop_column('template', 'product_selling_points')

    # 删除索引
    if index_exists('template', 'ix_template_viral_type'):
        op.drop_index('ix_template_viral_type', 'template')
    if index_exists('template', 'ix_template_ending_seed'):
        op.drop_index('ix_template_ending_seed', 'template')
    if index_exists('template', 'ix_template_emotion_seed'):
        op.drop_index('ix_template_emotion_seed', 'template')
    if index_exists('template', 'ix_template_opening_seed'):
        op.drop_index('ix_template_opening_seed', 'template')

    # 删除外键约束
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('template')]

    if 'fk_template_ending_seed' in existing_fks:
        op.drop_constraint('fk_template_ending_seed', 'template', type_='foreignkey')
    if 'fk_template_emotion_seed' in existing_fks:
        op.drop_constraint('fk_template_emotion_seed', 'template', type_='foreignkey')
    if 'fk_template_opening_seed' in existing_fks:
        op.drop_constraint('fk_template_opening_seed', 'template', type_='foreignkey')

    # 删除创意种子关联字段
    if column_exists('template', 'ending_seed_id'):
        op.drop_column('template', 'ending_seed_id')
    if column_exists('template', 'emotion_seed_id'):
        op.drop_column('template', 'emotion_seed_id')
    if column_exists('template', 'opening_seed_id'):
        op.drop_column('template', 'opening_seed_id')

    # 删除爆款类型字段
    if column_exists('template', 'viral_type'):
        op.drop_column('template', 'viral_type')
    # MySQL不需要显式删除ENUM类型
    # op.execute("DROP TYPE IF EXISTS viral_type_enum")
