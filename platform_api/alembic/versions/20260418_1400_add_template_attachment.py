"""
Add template_attachment table and update template table

Revision ID: 20260418_1400
Revises: 20260418_1000
Create Date: 2026-04-18 14:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260418_1400'
down_revision = '20260418_1000'
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


def table_exists(conn, table_name):
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = :table_name
    """), {'table_name': table_name}).fetchone()
    return result is not None


def upgrade():
    conn = op.get_bind()

    # Create template_attachment table
    if not table_exists(conn, 'template_attachment'):
        op.create_table(
            'template_attachment',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
            sa.Column('template_id', sa.BigInteger(), nullable=False, comment='模板ID'),
            sa.Column('file_type', sa.Enum('image', 'video', name='template_attachment_type_enum'), nullable=False, comment='文件类型：image（图片）/ video（视频）'),
            sa.Column('file_url', sa.String(length=500), nullable=False, comment='腾讯云COS文件URL'),
            sa.Column('file_name', sa.String(length=255), nullable=False, comment='文件名'),
            sa.Column('file_size', sa.BigInteger(), nullable=True, comment='文件大小（字节）'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序'),
            sa.Column('width', sa.Integer(), nullable=True, comment='图片/视频宽度（像素）'),
            sa.Column('height', sa.Integer(), nullable=True, comment='图片/视频高度（像素）'),
            sa.Column('duration', sa.Float(), nullable=True, comment='视频时长（秒）'),
            sa.Column('thumbnail_url', sa.String(length=500), nullable=True, comment='缩略图URL'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        # Add index on template_id
        op.create_index('ix_template_attachment_template', 'template_attachment', ['template_id'])
        print("Created template_attachment table")
    else:
        print("template_attachment table already exists")

    # Add image_count column to template table
    if not column_exists(conn, 'template', 'image_count'):
        op.add_column('template',
                      sa.Column('image_count', sa.Integer(), nullable=False, server_default='0', comment='图片数量（冗余字段，提高查询效率）'))
        print("Added image_count column to template")
    else:
        print("image_count column already exists in template")

    # Add video_count column to template table
    if not column_exists(conn, 'template', 'video_count'):
        op.add_column('template',
                      sa.Column('video_count', sa.Integer(), nullable=False, server_default='0', comment='视频数量（冗余字段，提高查询效率）'))
        print("Added video_count column to template")
    else:
        print("video_count column already exists in template")


def downgrade():
    conn = op.get_bind()

    # Drop template_attachment table
    if table_exists(conn, 'template_attachment'):
        op.drop_table('template_attachment')
        print("Dropped template_attachment table")

    # Drop image_count column from template
    if column_exists(conn, 'template', 'image_count'):
        op.drop_column('template', 'image_count')
        print("Dropped image_count column from template")

    # Drop video_count column from template
    if column_exists(conn, 'template', 'video_count'):
        op.drop_column('template', 'video_count')
        print("Dropped video_count column from template")
