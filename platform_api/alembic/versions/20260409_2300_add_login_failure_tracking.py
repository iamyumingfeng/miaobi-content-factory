"""add_login_failure_tracking

添加登录失败次数跟踪字段

Revision ID: add_login_failure_tracking
Revises: 9b2d3c4e8f7a
Create Date: 2026-04-09 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_login_failure_tracking'
down_revision: Union[str, None] = '9b2d3c4e8f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加登录失败相关字段到 super_admin 表
    op.add_column('super_admin', sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('super_admin', sa.Column('locked_until', sa.DateTime(), nullable=True))

    # 添加登录失败相关字段到 operator 表
    op.add_column('operator', sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('operator', sa.Column('locked_until', sa.DateTime(), nullable=True))

    # 添加登录失败相关字段到 sub_user 表
    op.add_column('sub_user', sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('sub_user', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # 从 super_admin 表移除字段
    op.drop_column('super_admin', 'locked_until')
    op.drop_column('super_admin', 'login_failure_count')

    # 从 operator 表移除字段
    op.drop_column('operator', 'locked_until')
    op.drop_column('operator', 'login_failure_count')

    # 从 sub_user 表移除字段
    op.drop_column('sub_user', 'locked_until')
    op.drop_column('sub_user', 'login_failure_count')
