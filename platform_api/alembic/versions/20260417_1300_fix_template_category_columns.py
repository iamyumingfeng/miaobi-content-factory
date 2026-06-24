"""
Fix category columns: drop old platform_id, make new platform_id NOT NULL

Revision ID: 20260417_1300
Revises: 20260417_1200
Create Date: 2026-04-17 13:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260417_1300'
down_revision = '20260417_1200'
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


def constraint_exists(conn, table_name, constraint_name):
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = DATABASE() 
        AND table_name = :table_name 
        AND constraint_name = :constraint_name
    """), {'table_name': table_name, 'constraint_name': constraint_name}).fetchone()
    return result is not None


def index_exists(conn, table_name, index_name):
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = :table_name 
        AND index_name = :index_name
    """), {'table_name': table_name, 'index_name': index_name}).fetchone()
    return result is not None


def upgrade():
    conn = op.get_bind()
    
    # ================================================================
    # 修复 template_category 表
    # ================================================================
    
    # 1. 如果 template_platform_id 为 NULL，先复制 platform_id 的值
    if column_exists(conn, 'template_category', 'template_platform_id') and column_exists(conn, 'template_category', 'platform_id'):
        conn.execute(text("""
            UPDATE template_category 
            SET template_platform_id = platform_id 
            WHERE template_platform_id IS NULL
        """))
    
    # 2. 删除旧的外键约束和索引
    if column_exists(conn, 'template_category', 'platform_id'):
        try:
            if constraint_exists(conn, 'template_category', 'fk_template_category_platform'):
                op.drop_constraint('fk_template_category_platform', 'template_category', type_='foreignkey')
        except Exception:
            pass
        try:
            if index_exists(conn, 'template_category', 'ix_template_category_platform'):
                op.drop_index('ix_template_category_platform', table_name='template_category')
        except Exception:
            pass
        
        # 3. 删除旧的 platform_id 列
        try:
            op.drop_column('template_category', 'platform_id')
        except Exception:
            pass
    
    # 4. 将 template_platform_id 设为 NOT NULL
    if column_exists(conn, 'template_category', 'template_platform_id'):
        try:
            op.alter_column('template_category', 'template_platform_id', nullable=False)
        except Exception:
            pass
    
    # ================================================================
    # 修复 material_category 表
    # ================================================================
    
    # 1. 如果 material_platform_id 为 NULL，先复制 platform_id 的值
    if column_exists(conn, 'material_category', 'material_platform_id') and column_exists(conn, 'material_category', 'platform_id'):
        conn.execute(text("""
            UPDATE material_category 
            SET material_platform_id = platform_id 
            WHERE material_platform_id IS NULL
        """))
    
    # 2. 删除旧的外键约束和索引
    if column_exists(conn, 'material_category', 'platform_id'):
        try:
            if constraint_exists(conn, 'material_category', 'fk_material_category_platform'):
                op.drop_constraint('fk_material_category_platform', 'material_category', type_='foreignkey')
        except Exception:
            pass
        try:
            if index_exists(conn, 'material_category', 'ix_material_category_platform'):
                op.drop_index('ix_material_category_platform', table_name='material_category')
        except Exception:
            pass
        
        # 3. 删除旧的 platform_id 列
        try:
            op.drop_column('material_category', 'platform_id')
        except Exception:
            pass
    
    # 4. 将 material_platform_id 设为 NOT NULL
    if column_exists(conn, 'material_category', 'material_platform_id'):
        try:
            op.alter_column('material_category', 'material_platform_id', nullable=False)
        except Exception:
            pass


def downgrade():
    conn = op.get_bind()
    
    # ================================================================
    # 回滚 template_category
    # ================================================================
    if not column_exists(conn, 'template_category', 'platform_id'):
        op.add_column('template_category', sa.Column('platform_id', sa.BigInteger(), nullable=True))
        op.create_index('ix_template_category_platform', 'template_category', ['platform_id'])
    
    if column_exists(conn, 'template_category', 'platform_id') and column_exists(conn, 'template_category', 'template_platform_id'):
        conn.execute(text("UPDATE template_category SET platform_id = template_platform_id"))
        try:
            op.alter_column('template_category', 'platform_id', nullable=False)
        except Exception:
            pass
    
    if column_exists(conn, 'template_category', 'template_platform_id'):
        try:
            op.alter_column('template_category', 'template_platform_id', nullable=True)
        except Exception:
            pass
    
    # ================================================================
    # 回滚 material_category
    # ================================================================
    if not column_exists(conn, 'material_category', 'platform_id'):
        op.add_column('material_category', sa.Column('platform_id', sa.BigInteger(), nullable=True))
        op.create_index('ix_material_category_platform', 'material_category', ['platform_id'])
    
    if column_exists(conn, 'material_category', 'platform_id') and column_exists(conn, 'material_category', 'material_platform_id'):
        conn.execute(text("UPDATE material_category SET platform_id = material_platform_id"))
        try:
            op.alter_column('material_category', 'platform_id', nullable=False)
        except Exception:
            pass
    
    if column_exists(conn, 'material_category', 'material_platform_id'):
        try:
            op.alter_column('material_category', 'material_platform_id', nullable=True)
        except Exception:
            pass
