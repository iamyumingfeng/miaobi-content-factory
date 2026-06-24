"""add dashboard alert dismissal table

Revision ID: 20260420_1500
Revises:
Create Date: 2026-04-20 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20260420_1500'
down_revision: Union[str, None] = '20260419_2300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dashboard_alert_dismissal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
        sa.Column('task_id', sa.BigInteger(), nullable=False, comment='任务ID'),
        sa.Column('dismissed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='清除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'task_id', name='uk_user_task_dismissal')
    )
    op.create_index('ix_dashboard_alert_dismissal_user_id', 'dashboard_alert_dismissal', ['user_id'], unique=False)
    op.create_index('ix_dashboard_alert_dismissal_task_id', 'dashboard_alert_dismissal', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_dashboard_alert_dismissal_task_id', table_name='dashboard_alert_dismissal')
    op.drop_index('ix_dashboard_alert_dismissal_user_id', table_name='dashboard_alert_dismissal')
    op.drop_table('dashboard_alert_dismissal')
