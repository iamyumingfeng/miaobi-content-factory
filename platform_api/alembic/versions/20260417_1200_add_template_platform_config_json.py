"""
Add missing config_json column to template_platform table

Revision ID: 20260417_1200
Revises: 20250120_1000
Create Date: 2026-04-17 12:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260417_1200'
down_revision = '20250120_1000'
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
    if not column_exists(conn, 'template_platform', 'config_json'):
        op.add_column(
            'template_platform',
            sa.Column('config_json', sa.JSON(), nullable=True, comment='平台配置JSON（预留扩展）')
        )


def downgrade():
    conn = op.get_bind()
    if column_exists(conn, 'template_platform', 'config_json'):
        op.drop_column('template_platform', 'config_json')
