"""drop user_id from dashboard_alert_dismissal

Revision ID: 20260420_1600
Revises: 5d7b4ddc4bb6
Create Date: 2026-04-20 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20260420_1600'
down_revision: Union[str, None] = '5d7b4ddc4bb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 删除旧的唯一约束和 user_id 列
    op.drop_index('ix_dashboard_alert_dismissal_user_id', table_name='dashboard_alert_dismissal')
    op.drop_index('ix_dashboard_alert_dismissal_task_id', table_name='dashboard_alert_dismissal')
    op.drop_constraint('uk_user_task_dismissal', 'dashboard_alert_dismissal', type_='unique')

    # 删除 user_id 列
    op.drop_column('dashboard_alert_dismissal', 'user_id')

    # 添加新的唯一索引（仅 task_id）
    op.create_index('ix_dashboard_alert_dismissal_task_id', 'dashboard_alert_dismissal', ['task_id'], unique=True)


def downgrade() -> None:
    # MySQL 不支持添加带条件的唯一索引，需要先删除唯一索引再添加
    op.drop_index('ix_dashboard_alert_dismissal_task_id', table_name='dashboard_alert_dismissal')

    # 添加 user_id 列（允许为空，后面会通过数据填充）
    op.add_column('dashboard_alert_dismissal', sa.Column('user_id', sa.BigInteger(), nullable=True, comment='用户ID'))

    # 恢复唯一约束
    op.create_unique_constraint('uk_user_task_dismissal', 'dashboard_alert_dismissal', ['user_id', 'task_id'])
    op.create_index('ix_dashboard_alert_dismissal_user_id', 'dashboard_alert_dismissal', ['user_id'], unique=False)