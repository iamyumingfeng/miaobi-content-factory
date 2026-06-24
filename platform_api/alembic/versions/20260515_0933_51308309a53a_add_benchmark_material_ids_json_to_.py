"""add_benchmark_material_ids_json_to_scheduled_task

Revision ID: 51308309a53a
Revises: 20260515_1000
Create Date: 2026-05-15 09:33:19.579226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '51308309a53a'
down_revision: Union[str, None] = '20260515_1000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(connection, table_name: str) -> bool:
    """检查表是否存在"""
    inspector = sa_inspect(connection)
    return table_name in inspector.get_table_names()


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = sa_inspect(connection)
    if not _table_exists(connection, table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    connection = op.get_bind()
    
    # 检查 scheduled_task 表是否存在
    if not _table_exists(connection, 'scheduled_task'):
        print("WARNING: scheduled_task table does not exist, skipping migration")
        return
    
    # 检查 benchmark_material_ids_json 字段是否已存在
    if _column_exists(connection, 'scheduled_task', 'benchmark_material_ids_json'):
        print("INFO: benchmark_material_ids_json column already exists, skipping add_column")
    else:
        # 添加 benchmark_material_ids_json 字段
        op.add_column(
            'scheduled_task',
            sa.Column('benchmark_material_ids_json', sa.JSON(), nullable=True, comment='对标素材ID列表JSON')
        )
        print("INFO: Added benchmark_material_ids_json column to scheduled_task")
    
    # 数据迁移：对于 benchmark 类型的任务，将 material_id 的值迁移到 benchmark_material_ids_json
    # 只迁移 benchmark_material_ids_json 为 NULL 的记录（避免重复迁移）
    try:
        result = connection.execute(
            text("""
                UPDATE scheduled_task 
                SET benchmark_material_ids_json = JSON_ARRAY(material_id)
                WHERE task_type = 'benchmark' 
                  AND material_id IS NOT NULL
                  AND benchmark_material_ids_json IS NULL
            """)
        )
        if result.rowcount > 0:
            print(f"INFO: Migrated {result.rowcount} rows to benchmark_material_ids_json")
    except Exception as e:
        print(f"WARNING: Data migration failed (may be already migrated): {str(e)}")
    
    # 注意：不删除 material_id 字段，因为自定义文案类型仍在使用


def downgrade() -> None:
    connection = op.get_bind()
    
    # 检查 scheduled_task 表是否存在
    if not _table_exists(connection, 'scheduled_task'):
        print("WARNING: scheduled_task table does not exist, skipping downgrade")
        return
    
    # 检查 benchmark_material_ids_json 字段是否存在
    if not _column_exists(connection, 'scheduled_task', 'benchmark_material_ids_json'):
        print("INFO: benchmark_material_ids_json column does not exist, skipping drop_column")
        return
    
    # 降级：删除 benchmark_material_ids_json 字段
    try:
        op.drop_column('scheduled_task', 'benchmark_material_ids_json')
        print("INFO: Dropped benchmark_material_ids_json column from scheduled_task")
    except Exception as e:
        print(f"WARNING: Failed to drop column (may not exist): {str(e)}")
