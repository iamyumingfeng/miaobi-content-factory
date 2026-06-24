"""创建爆款类型配置表

Revision ID: 20260510_viral_type_table
Revises: 20260510_viral_type_extend
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260510_viral_type_table'
down_revision = '20260510_viral_type_extend'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建爆款类型配置表
    op.create_table(
        'viral_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('value', sa.String(50), nullable=False, comment='类型值，如 seeding, review'),
        sa.Column('label', sa.String(100), nullable=False, comment='显示标签，如 种草安利型'),
        sa.Column('description', sa.Text(), nullable=True, comment='类型描述'),
        sa.Column('keywords', sa.Text(), nullable=True, comment='关键词 JSON 数组'),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0, comment='排序顺序'),
        sa.Column('status', sa.String(20), nullable=True, default='enabled', comment='状态: enabled/disabled'),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False, comment='是否系统预置'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('value'),
    )

    # 创建索引
    op.create_index(op.f('ix_viral_type_id'), 'viral_type', ['id'], unique=False)
    op.create_index(op.f('ix_viral_type_value'), 'viral_type', ['value'], unique=True)


def downgrade() -> None:
    # 删除索引
    op.drop_index(op.f('ix_viral_type_value'), table_name='viral_type')
    op.drop_index(op.f('ix_viral_type_id'), table_name='viral_type')

    # 删除表
    op.drop_table('viral_type')