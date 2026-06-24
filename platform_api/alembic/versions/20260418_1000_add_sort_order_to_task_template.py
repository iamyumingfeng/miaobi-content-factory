"""
Add sort_order to generation_task_template

Revision ID: 20260418_1000
Revises: 20260417_1300
Create Date: 2026-04-18 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260418_1000'
down_revision = '20260417_1300'
branch_labels = None
depends_on = None


def column_exists(conn, table_name, column_name):
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = DATABASE()
        AND table_name = :table_name
        AND column_name = :column_name
    """), {'table_name': table_name, 'column_name': column_name}).fetchone()
    return result is not None


def upgrade():
    conn = op.get_bind()

    # Add sort_order column to generation_task_template if it doesn't exist
    if not column_exists(conn, 'generation_task_template', 'sort_order'):
        op.add_column('generation_task_template',
                      sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'))
        print("Added sort_order column to generation_task_template")
    else:
        print("sort_order column already exists in generation_task_template")


def downgrade():
    conn = op.get_bind()
    if column_exists(conn, 'generation_task_template', 'sort_order'):
        op.drop_column('generation_task_template', 'sort_order')
        print("Dropped sort_order column from generation_task_template")