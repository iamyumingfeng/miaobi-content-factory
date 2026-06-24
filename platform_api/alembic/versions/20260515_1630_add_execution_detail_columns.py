"""add execution detail columns to scheduled_task_execution

Revision ID: 20260515_1630
Revises: a566112d7917
Create Date: 2026-05-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '20260515_1630'
down_revision: Union[str, None] = 'a566112d7917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(connection, table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = inspect(connection)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """添加执行详情列到 scheduled_task_execution 表"""
    connection = op.get_bind()
    
    if not _table_exists(connection, "scheduled_task_execution"):
        print("WARNING: scheduled_task_execution table does not exist, skipping")
        return
    
    # 1. 添加 execution_type 列
    if _column_exists(connection, "scheduled_task_execution", "execution_type"):
        print("INFO: execution_type column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "execution_type",
                sa.String(50),
                nullable=False,
                server_default="scheduled",
                comment="执行类型：scheduled(定时) / manual(手动)"
            )
        )
        print("INFO: added execution_type column")
    
    # 2. 添加 scheduled_at 列
    if _column_exists(connection, "scheduled_task_execution", "scheduled_at"):
        print("INFO: scheduled_at column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "scheduled_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
                comment="计划执行时间"
            )
        )
        print("INFO: added scheduled_at column")
    
    # 3. 添加 started_at 列
    if _column_exists(connection, "scheduled_task_execution", "started_at"):
        print("INFO: started_at column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "started_at",
                sa.DateTime(),
                nullable=True,
                comment="实际开始执行时间"
            )
        )
        print("INFO: added started_at column")
    
    # 4. 添加 completed_at 列
    if _column_exists(connection, "scheduled_task_execution", "completed_at"):
        print("INFO: completed_at column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "completed_at",
                sa.DateTime(),
                nullable=True,
                comment="执行完成时间"
            )
        )
        print("INFO: added completed_at column")
    
    # 5. 添加 total_items 列
    if _column_exists(connection, "scheduled_task_execution", "total_items"):
        print("INFO: total_items column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "total_items",
                sa.Integer(),
                nullable=True,
                server_default="0",
                comment="总生成项数"
            )
        )
        print("INFO: added total_items column")
    
    # 6. 添加 success_items 列
    if _column_exists(connection, "scheduled_task_execution", "success_items"):
        print("INFO: success_items column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "success_items",
                sa.Integer(),
                nullable=True,
                server_default="0",
                comment="成功项数"
            )
        )
        print("INFO: added success_items column")
    
    # 7. 添加 failed_items 列
    if _column_exists(connection, "scheduled_task_execution", "failed_items"):
        print("INFO: failed_items column already exists, skipping")
    else:
        op.add_column(
            "scheduled_task_execution",
            sa.Column(
                "failed_items",
                sa.Integer(),
                nullable=True,
                server_default="0",
                comment="失败项数"
            )
        )
        print("INFO: added failed_items column")
    
    # 8. 修改 status 列默认值和注释
    try:
        op.alter_column(
            "scheduled_task_execution",
            "status",
            existing_type=sa.String(50),
            server_default="pending",
            existing_nullable=False,
            comment="执行状态：pending(排队中) / running(执行中) / completed(完成) / failed(失败) / partial(部分成功) / cancelled(已取消)"
        )
        print("INFO: updated status column defaults")
    except Exception as e:
        print(f"WARNING: failed to update status column: {e}")
    
    print("INFO: migration completed successfully")


def downgrade() -> None:
    """回退执行详情列"""
    connection = op.get_bind()
    
    if not _table_exists(connection, "scheduled_task_execution"):
        print("WARNING: scheduled_task_execution table does not exist, skipping")
        return
    
    # 按添加的逆序删除列
    columns_to_drop = [
        "failed_items",
        "success_items",
        "total_items",
        "completed_at",
        "started_at",
        "scheduled_at",
        "execution_type",
    ]
    
    for col in columns_to_drop:
        if _column_exists(connection, "scheduled_task_execution", col):
            try:
                op.drop_column("scheduled_task_execution", col)
                print(f"INFO: dropped {col} column")
            except Exception as e:
                print(f"WARNING: failed to drop {col} column: {e}")
        else:
            print(f"INFO: {col} column does not exist, skipping")
    
    print("INFO: downgrade completed successfully")
