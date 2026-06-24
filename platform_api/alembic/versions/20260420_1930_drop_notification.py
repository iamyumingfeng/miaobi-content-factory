"""
Drop notification table and notification_type_enum

Removes the notification feature that was never fully implemented.
Backend API returned 501 NOT_IMPLEMENTED, frontend used mock data.

Revision ID: 20260420_1930
Revises: 20260420_1800
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = '20260420_1930'
down_revision = '20260420_1800'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('notification')
    # Drop the enum type (MySQL doesn't support DROP TYPE, but we clean up for other dialects)
    try:
        notification_type_enum = sa.Enum(
            'task_completed', 'task_failed', 'cleanup_reminder', 'content_received',
            name='notification_type_enum'
        )
        notification_type_enum.drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass


def downgrade():
    op.create_table(
        'notification',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('super_admin_id', sa.BigInteger(), nullable=True),
        sa.Column('operator_id', sa.BigInteger(), nullable=True),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=True),
        sa.Column('type', sa.Enum(
            'task_completed', 'task_failed', 'cleanup_reminder', 'content_received',
            name='notification_type_enum'
        ), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('related_id', sa.BigInteger(), nullable=True),
        sa.Column('related_type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['super_admin_id'], ['super_admin.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['operator.id']),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
