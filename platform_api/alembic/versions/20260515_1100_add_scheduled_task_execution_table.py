"""add scheduled_task_execution table

Revision ID: 20260515_1100
Revises: 20260515_1000
Create Date: 2026-05-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260515_1100'
down_revision = '20260515_1000'
branch_labels = None
depends_on = None


def upgrade():
    """创建定时任务执行历史表"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # 如果表已存在，跳过
    if 'scheduled_task_execution' in tables:
        print("WARNING: scheduled_task_execution table already exists, skipping")
        return
    
    # 辅助函数：检查表是否存在
    def _table_exists(table_name):
        return table_name in tables
    
    # 辅助函数：检查列是否存在
    def _column_exists(table_name, column_name):
        if not _table_exists(table_name):
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    
    # 创建 scheduled_task_execution 表
    op.create_table(
        'scheduled_task_execution',
        
        # 主键
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
        
        # 外键关联
        sa.Column('scheduled_task_id', sa.BigInteger(), nullable=False, comment='定时任务ID'),
        sa.Column('generation_task_id', sa.BigInteger(), nullable=True, comment='生成的任务ID'),
        
        # 执行信息
        sa.Column('execution_time', sa.DateTime(), nullable=False, comment='执行时间'),
        sa.Column('status', sa.String(50), nullable=False, comment='执行状态：success / failed / partial'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        
        # 执行详情
        sa.Column('execution_details_json', sa.String(2000), nullable=True, comment='执行详情JSON'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        
        # 约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['scheduled_task_id'], ['scheduled_task.id']),
        sa.ForeignKeyConstraint(['generation_task_id'], ['generation_task.id']),
    )
    
    # 创建索引
    op.create_index('ix_scheduled_task_execution_scheduled_task_id', 'scheduled_task_execution', ['scheduled_task_id'])
    op.create_index('ix_scheduled_task_execution_created_at', 'scheduled_task_execution', ['created_at'])
    
    print("INFO: scheduled_task_execution table created successfully")


def downgrade():
    """删除定时任务执行历史表"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'scheduled_task_execution' in tables:
        op.drop_index('ix_scheduled_task_execution_created_at', table_name='scheduled_task_execution')
        op.drop_index('ix_scheduled_task_execution_scheduled_task_id', table_name='scheduled_task_execution')
        op.drop_table('scheduled_task_execution')
        print("INFO: scheduled_task_execution table dropped successfully")
    else:
        print("WARNING: scheduled_task_execution table does not exist, skipping")
