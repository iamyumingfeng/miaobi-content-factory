"""add user_default_model table

Revision ID: 20260424_1000
Revises: 20260423_1710
Create Date: 2026-04-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260424_1000'
down_revision: Union[str, None] = '20260423_1710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return result.fetchone()[0] > 0


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND index_name = :index_name
        """),
        {"table_name": table_name, "index_name": index_name}
    )
    return result.fetchone()[0] > 0


def upgrade() -> None:
    # 首先创建需要的枚举类型（如果不存在）
    # user_type_enum - 复用现有或创建
    # model_type_enum - 已经存在

    # 创建 user_default_model 表（幂等：已存在则跳过）
    if not table_exists('user_default_model'):
        op.create_table(
            'user_default_model',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
            sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
            sa.Column('user_type', sa.Enum('super_admin', 'operator', name='user_type_enum'), nullable=False, comment='用户类型：super_admin / operator'),
            sa.Column('model_type', sa.Enum('llm', 'image', 'video', name='model_type_enum'), nullable=False, comment='模型类型：llm / image / video'),
            sa.Column('model_config_id', sa.BigInteger(), nullable=True, comment='关联的模型配置ID，NULL表示自动选择'),
            sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),

            # 主键约束
            sa.PrimaryKeyConstraint('id'),

            # 唯一约束
            sa.UniqueConstraint('user_id', 'user_type', 'model_type', name='uq_user_model_type'),

            # 外键约束 - ON DELETE SET NULL 确保删除模型时自动回退为 auto
            sa.ForeignKeyConstraint(
                ['model_config_id'],
                ['model_config.id'],
                name='fk_user_default_model_config_id',
                ondelete='SET NULL'
            ),
        )

        # 创建索引（幂等：已存在则跳过）
        if not index_exists('user_default_model', 'ix_user_default_model_user_id'):
            op.create_index('ix_user_default_model_user_id', 'user_default_model', ['user_id'])
        if not index_exists('user_default_model', 'ix_user_default_model_user_type'):
            op.create_index('ix_user_default_model_user_type', 'user_default_model', ['user_type'])
        if not index_exists('user_default_model', 'ix_user_default_model_model_config_id'):
            op.create_index('ix_user_default_model_model_config_id', 'user_default_model', ['model_config_id'])


def downgrade() -> None:
    # 删除表
    if table_exists('user_default_model'):
        op.drop_table('user_default_model')

    # 注意：不删除枚举类型，因为可能被其他表使用
