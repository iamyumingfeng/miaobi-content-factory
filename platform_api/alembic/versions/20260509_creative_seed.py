"""create creative_seed table

Revision ID: 20260509_creative_seed
Revises: 20260508_1000
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260509_creative_seed'
down_revision = '20260508_1000'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检测表是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade():
    # 检测表是否已存在，避免重复创建
    if table_exists('creative_seed'):
        print("Table 'creative_seed' already exists, skipping creation.")
        return

    # 创建创意种子库表
    op.create_table(
        'creative_seed',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
        sa.Column('name', sa.String(100), nullable=False, comment='种子名称'),
        sa.Column('seed_type', sa.Enum('opening', 'emotion', 'ending', name='creative_seed_type_enum'), nullable=False, comment='种子类型'),
        sa.Column('template', sa.String(500), nullable=False, comment='模板示例'),
        sa.Column('description', sa.Text(), nullable=True, comment='使用说明'),
        sa.Column('forbidden_patterns', sa.Text(), nullable=True, comment='禁止使用的模式（JSON数组）'),
        sa.Column('example_phrases', sa.Text(), nullable=True, comment='典型表达示例（JSON数组）'),
        sa.Column('avoid_phrases', sa.Text(), nullable=True, comment='避免的表达（JSON数组）'),
        sa.Column('category', sa.String(50), nullable=True, default='通用', comment='适用品类'),
        sa.Column('status', sa.Enum('enabled', 'disabled', name='creative_seed_status_enum'), nullable=False, default='enabled', comment='状态'),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False, comment='是否系统预置'),
        sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='所属运营管理员ID'),
        sa.Column('use_count', sa.BigInteger(), nullable=False, default=0, comment='使用次数统计'),
        sa.Column('success_rate', sa.Float(), nullable=True, comment='成功率'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], name='fk_creative_seed_operator'),
    )

    # 创建索引（检测是否存在）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('creative_seed')]

    if 'ix_creative_seed_type' not in existing_indexes:
        op.create_index('ix_creative_seed_type', 'creative_seed', ['seed_type'])
    if 'ix_creative_seed_status' not in existing_indexes:
        op.create_index('ix_creative_seed_status', 'creative_seed', ['status'])
    if 'ix_creative_seed_category' not in existing_indexes:
        op.create_index('ix_creative_seed_category', 'creative_seed', ['category'])
    if 'ix_creative_seed_owner' not in existing_indexes:
        op.create_index('ix_creative_seed_owner', 'creative_seed', ['owner_operator_id'])


def downgrade():
    if not table_exists('creative_seed'):
        print("Table 'creative_seed' does not exist, skipping downgrade.")
        return

    op.drop_index('ix_creative_seed_owner', 'creative_seed')
    op.drop_index('ix_creative_seed_category', 'creative_seed')
    op.drop_index('ix_creative_seed_status', 'creative_seed')
    op.drop_index('ix_creative_seed_type', 'creative_seed')
    op.drop_table('creative_seed')

    # 删除枚举类型（MySQL不需要显式删除ENUM类型）
    # op.execute("DROP TYPE IF EXISTS creative_seed_type_enum")
    # op.execute("DROP TYPE IF EXISTS creative_seed_status_enum")
