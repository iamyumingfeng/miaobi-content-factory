"""
Fix generation_task_progress_log schema mismatch

Revision ID: 20260419_1100
Revises: 20260419_1000
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '20260419_1100'
down_revision = '20260419_1000'
branch_labels = None
depends_on = None


def upgrade():
    """
    Align generation_task_progress_log with ORM model:
    - Add status column (required by ORM)
    - Add progress_message column (required by ORM)
    - Add server defaults for total_count and paused_count (to allow INSERT without explicit values)
    """
    # Add status column with default 'pending'
    try:
        op.add_column(
            'generation_task_progress_log',
            sa.Column(
                'status',
                mysql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled'),
                nullable=False,
                server_default='pending',
                comment='任务状态'
            )
        )
    except Exception as e:
        print(f"Warning: Could not add status column: {e}")

    # Add progress_message column
    try:
        op.add_column(
            'generation_task_progress_log',
            sa.Column(
                'progress_message',
                sa.String(1000),
                nullable=True,
                comment='进度信息'
            )
        )
    except Exception as e:
        print(f"Warning: Could not add progress_message column: {e}")

    # Add server defaults for columns not in ORM but exist in DB
    # This allows INSERT to work without explicit values for these columns
    try:
        op.alter_column(
            'generation_task_progress_log',
            'total_count',
            existing_type=sa.Integer(),
            nullable=False,
            server_default='0'
        )
    except Exception as e:
        print(f"Warning: Could not add server_default to total_count: {e}")

    try:
        op.alter_column(
            'generation_task_progress_log',
            'paused_count',
            existing_type=sa.Integer(),
            nullable=False,
            server_default='0'
        )
    except Exception as e:
        print(f"Warning: Could not add server_default to paused_count: {e}")


def downgrade():
    """
    Remove added columns
    """
    try:
        op.drop_column('generation_task_progress_log', 'progress_message')
    except Exception:
        pass

    try:
        op.drop_column('generation_task_progress_log', 'status')
    except Exception:
        pass
