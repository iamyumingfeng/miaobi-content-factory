"""
Add missing columns to template_tag and material_tag tables

Revision ID: 20260508_0010
Revises: 20260507_2327
Create Date: 2026-05-08 00:10:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260508_0010'
down_revision = '20260507_2000'
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

    # ============================================
    # 1. Add is_system to template_tag
    # ============================================
    if not column_exists(conn, 'template_tag', 'is_system'):
        op.add_column(
            'template_tag',
            sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='是否系统默认标签')
        )

    # ============================================
    # 2. Add owner_operator_id to template_tag (if missing)
    # ============================================
    if not column_exists(conn, 'template_tag', 'owner_operator_id'):
        op.add_column(
            'template_tag',
            sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='所属运营管理员ID')
        )
        op.create_index('ix_template_tag_owner', 'template_tag', ['owner_operator_id'])

        # 从 template_category 表复制 owner_operator_id
        conn.execute(text("""
            UPDATE template_tag t
            JOIN template_category c ON t.category_id = c.id
            SET t.owner_operator_id = c.owner_operator_id
            WHERE t.owner_operator_id IS NULL
        """))

        # 如果没有 category_id，从 created_by 推断或者设置为 1
        conn.execute(text("""
            UPDATE template_tag
            SET owner_operator_id = COALESCE(created_by, 1)
            WHERE owner_operator_id IS NULL
        """))

        # 现在设置为 NOT NULL
        op.alter_column('template_tag', 'owner_operator_id', nullable=False)

    # ============================================
    # 3. Add is_system to material_tag (if missing)
    # ============================================
    if not column_exists(conn, 'material_tag', 'is_system'):
        op.add_column(
            'material_tag',
            sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='是否系统默认标签')
        )

    # ============================================
    # 4. Ensure owner_operator_id exists on material_tag
    # ============================================
    if not column_exists(conn, 'material_tag', 'owner_operator_id'):
        op.add_column(
            'material_tag',
            sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='所属运营管理员ID')
        )
        op.create_index('ix_material_tag_owner', 'material_tag', ['owner_operator_id'])

        # 从 material_category 表复制 owner_operator_id
        conn.execute(text("""
            UPDATE material_tag t
            JOIN material_category c ON t.category_id = c.id
            SET t.owner_operator_id = c.owner_operator_id
            WHERE t.owner_operator_id IS NULL
        """))

        # 如果没有 category_id，从 created_by 推断或者设置为 1
        conn.execute(text("""
            UPDATE material_tag
            SET owner_operator_id = COALESCE(created_by, 1)
            WHERE owner_operator_id IS NULL
        """))

        # 现在设置为 NOT NULL
        op.alter_column('material_tag', 'owner_operator_id', nullable=False)


def downgrade():
    conn = op.get_bind()

    # Drop template_tag columns
    if column_exists(conn, 'template_tag', 'is_system'):
        op.drop_column('template_tag', 'is_system')
    if column_exists(conn, 'template_tag', 'owner_operator_id'):
        op.drop_index('ix_template_tag_owner', table_name='template_tag')
        op.drop_column('template_tag', 'owner_operator_id')

    # Drop material_tag columns (if we added them)
    if column_exists(conn, 'material_tag', 'is_system'):
        op.drop_column('material_tag', 'is_system')
