"""add periodic to schedule_type enum

Revision ID: 94e98f60bd6a
Revises: 20260515_1630
Create Date: 2026-05-16 09:32:39.777110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '94e98f60bd6a'
down_revision: Union[str, None] = '20260515_1630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(connection, table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = inspect(connection)
    if not _table_exists(connection, table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """升级：向 schedule_type 枚举添加 'periodic' 值"""
    connection = op.get_bind()
    
    # 1. 检查表是否存在
    if not _table_exists(connection, 'scheduled_task'):
        print("WARNING: scheduled_task table does not exist, skipping migration")
        return
    
    # 2. 检查列是否存在
    if not _column_exists(connection, 'scheduled_task', 'schedule_type'):
        print("WARNING: schedule_type column does not exist in scheduled_task table, skipping")
        return
    
    try:
        # 3. 修改 schedule_type 列的 Enum 类型，添加 'periodic'
        print("INFO: Adding 'periodic' to schedule_type enum...")
        op.alter_column(
            'scheduled_task',
            'schedule_type',
            type_=sa.Enum('daily', 'weekly', 'periodic', name='schedule_type_enum'),
            existing_type=sa.Enum('daily', 'weekly', name='schedule_type_enum'),
            nullable=False
        )
        print("SUCCESS: schedule_type enum updated to include 'periodic'")
        
    except Exception as e:
        print(f"ERROR: Failed to update schedule_type enum: {e}")
        raise


def downgrade() -> None:
    """降级：从 schedule_type 枚举移除 'periodic' 值"""
    connection = op.get_bind()
    
    # 1. 检查表是否存在
    if not _table_exists(connection, 'scheduled_task'):
        print("WARNING: scheduled_task table does not exist, skipping downgrade")
        return
    
    # 2. 检查列是否存在
    if not _column_exists(connection, 'scheduled_task', 'schedule_type'):
        print("WARNING: schedule_type column does not exist in scheduled_task table, skipping")
        return
    
    try:
        # 3. 先将所有 periodic 类型的任务改为 daily（避免数据丢失）
        print("INFO: Converting 'periodic' tasks to 'daily' before downgrade...")
        connection.execute(
            sa.text("UPDATE scheduled_task SET schedule_type = 'daily' WHERE schedule_type = 'periodic'")
        )
        print("SUCCESS: All 'periodic' tasks converted to 'daily'")
        
        # 4. 修改 schedule_type 列的 Enum 类型，移除 'periodic'
        print("INFO: Removing 'periodic' from schedule_type enum...")
        op.alter_column(
            'scheduled_task',
            'schedule_type',
            type_=sa.Enum('daily', 'weekly', name='schedule_type_enum'),
            existing_type=sa.Enum('daily', 'weekly', 'periodic', name='schedule_type_enum'),
            nullable=False
        )
        print("SUCCESS: schedule_type enum downgraded (removed 'periodic')")
        
    except Exception as e:
        print(f"ERROR: Failed to downgrade schedule_type enum: {e}")
        raise
