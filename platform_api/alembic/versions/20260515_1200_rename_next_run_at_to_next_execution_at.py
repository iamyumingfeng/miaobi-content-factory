"""rename next_run_at to next_execution_at in scheduled_task table

Revision ID: 20260515_1200
Revises: 20260515_1100
Create Date: 2026-05-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260515_1200'
down_revision = '20260515_1000'
branch_labels = None
depends_on = None


def upgrade():
    """将 scheduled_task 表中的 next_run_at 列重命名为 next_execution_at"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # 检查表是否存在
    if 'scheduled_task' not in tables:
        print("WARNING: scheduled_task table does not exist, skipping")
        return
    
    # 检查列是否存在
    columns = [col['name'] for col in inspector.get_columns('scheduled_task')]
    
    # 如果新列已存在，跳过
    if 'next_execution_at' in columns:
        print("WARNING: next_execution_at column already exists, skipping")
        return
    
    # 如果旧列不存在，跳过
    if 'next_run_at' not in columns:
        print("WARNING: next_run_at column does not exist, skipping")
        return
    
    print("INFO: Renaming column next_run_at to next_execution_at")
    
    # MySQL 语法：重命名列
    # 注意：不同数据库的语法不同，这里使用 MySQL 语法
    op.execute("ALTER TABLE scheduled_task CHANGE COLUMN next_run_at next_execution_at DATETIME")
    
    # 删除旧索引（如果存在）
    try:
        op.drop_index('ix_scheduled_task_next_run_at', table_name='scheduled_task')
        print("INFO: Dropped old index ix_scheduled_task_next_run_at")
    except Exception as e:
        print(f"INFO: Could not drop old index: {e}")
    
    # 创建新索引
    op.create_index('ix_scheduled_task_next_execution_at', 'scheduled_task', ['next_execution_at'])
    print("INFO: Created new index ix_scheduled_task_next_execution_at")
    
    # 更新复合索引
    try:
        op.drop_index('ix_scheduled_task_status_active', table_name='scheduled_task')
        print("INFO: Dropped old composite index ix_scheduled_task_status_active")
    except Exception as e:
        print(f"INFO: Could not drop old composite index: {e}")
    
    # 重新创建复合索引（使用新列名）
    op.create_index(
        'ix_scheduled_task_status_active',
        'scheduled_task',
        ['is_active', 'status', 'next_execution_at']
    )
    print("INFO: Created new composite index ix_scheduled_task_status_active")


def downgrade():
    """将 scheduled_task 表中的 next_execution_at 列重命名回 next_run_at"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # 检查表是否存在
    if 'scheduled_task' not in tables:
        print("WARNING: scheduled_task table does not exist, skipping")
        return
    
    # 检查列是否存在
    columns = [col['name'] for col in inspector.get_columns('scheduled_task')]
    
    # 如果旧列已存在，跳过
    if 'next_run_at' in columns:
        print("WARNING: next_run_at column already exists, skipping")
        return
    
    # 如果新列不存在，跳过
    if 'next_execution_at' not in columns:
        print("WARNING: next_execution_at column does not exist, skipping")
        return
    
    print("INFO: Renaming column next_execution_at to next_run_at")
    
    # MySQL 语法：重命名列
    op.execute("ALTER TABLE scheduled_task CHANGE COLUMN next_execution_at next_run_at DATETIME")
    
    # 删除新索引
    try:
        op.drop_index('ix_scheduled_task_next_execution_at', table_name='scheduled_task')
        print("INFO: Dropped new index ix_scheduled_task_next_execution_at")
    except Exception as e:
        print(f"INFO: Could not drop new index: {e}")
    
    # 创建旧索引
    op.create_index('ix_scheduled_task_next_run_at', 'scheduled_task', ['next_run_at'])
    print("INFO: Created old index ix_scheduled_task_next_run_at")
    
    # 更新复合索引
    try:
        op.drop_index('ix_scheduled_task_status_active', table_name='scheduled_task')
        print("INFO: Dropped new composite index ix_scheduled_task_status_active")
    except Exception as e:
        print(f"INFO: Could not drop new composite index: {e}")
    
    # 重新创建复合索引（使用旧列名）
    op.create_index(
        'ix_scheduled_task_status_active',
        'scheduled_task',
        ['is_active', 'status', 'next_run_at']
    )
    print("INFO: Created old composite index ix_scheduled_task_status_active")
