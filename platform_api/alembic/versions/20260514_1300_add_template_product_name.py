"""add template product_name

Revision ID: 20260514_1300
Revises: 20260511_seed_template_text
Create Date: 2026-05-14 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260514_1300'
down_revision = '20260511_seed_template_text'
branch_labels = None
depends_on = None


def upgrade():
    # 获取数据库连接和检查器
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # 检查 template 表是否存在
    tables = inspector.get_table_names()
    if 'template' not in tables:
        return
    
    # 检查 product_name 列是否已存在
    columns = [col['name'] for col in inspector.get_columns('template')]
    
    if 'product_name' not in columns:
        # 添加 product_name 字段（允许为空）
        op.add_column(
            'template',
            sa.Column(
                'product_name',
                sa.String(255),
                nullable=True,
                comment='产品名称（用于提示词中明确推广的产品，防止与对标素材混淆）'
            )
        )
        
        # 为现有记录设置默认值
        conn.execute(sa.text("UPDATE template SET product_name = '产品' WHERE product_name IS NULL"))
        
        # MySQL 需要使用 MODIFY COLUMN 来修改约束
        op.execute(
            "ALTER TABLE template MODIFY COLUMN product_name VARCHAR(255) NOT NULL "
            "COMMENT '产品名称（用于提示词中明确推广的产品，防止与对标素材混淆）'"
        )


def downgrade():
    # 获取数据库连接和检查器
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # 检查 template 表是否存在
    tables = inspector.get_table_names()
    if 'template' not in tables:
        return
    
    # 检查 product_name 列是否存在
    columns = [col['name'] for col in inspector.get_columns('template')]
    
    if 'product_name' in columns:
        op.drop_column('template', 'product_name')
