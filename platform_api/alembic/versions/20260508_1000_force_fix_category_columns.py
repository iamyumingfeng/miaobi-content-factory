"""
Force fix category columns: properly handle all foreign keys and indexes

Revision ID: 20260508_1000
Revises: 20260508_0020
Create Date: 2026-05-08 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260508_1000'
down_revision = '20260508_0010'
branch_labels = None
depends_on = None


def get_foreign_keys(conn, table_name):
    """获取表上的所有外键约束"""
    result = conn.execute(text("""
        SELECT CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = :table_name
        AND REFERENCED_COLUMN_NAME IS NOT NULL
    """), {'table_name': table_name})
    return [row[0] for row in result]


def get_indexes(conn, table_name):
    """获取表上的所有索引（除了主键）"""
    result = conn.execute(text("""
        SELECT INDEX_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = :table_name
        AND INDEX_NAME != 'PRIMARY'
    """), {'table_name': table_name})
    return list({row[0] for row in result})


def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = :table_name
        AND COLUMN_NAME = :column_name
    """), {'table_name': table_name, 'column_name': column_name}).fetchone()
    return result is not None


def fix_table(conn, table_name, old_column, new_column, reference_table):
    """修复单张表"""
    has_old = column_exists(conn, table_name, old_column)
    has_new = column_exists(conn, table_name, new_column)

    if not has_old and has_new:
        return

    print(f"Fixing {table_name}...")

    if has_old and not has_new:
        op.add_column(table_name, sa.Column(new_column, sa.BigInteger(), nullable=True))
        has_new = True

    if has_old and has_new:
        conn.execute(text(f"""
            UPDATE {table_name}
            SET {new_column} = {old_column}
            WHERE {new_column} IS NULL
        """))

    foreign_keys = get_foreign_keys(conn, table_name)
    for fk in foreign_keys:
        try:
            op.drop_constraint(fk, table_name, type_='foreignkey')
        except Exception:
            pass

    indexes = get_indexes(conn, table_name)
    for idx in indexes:
        try:
            op.drop_index(idx, table_name=table_name)
        except Exception:
            pass

    if has_old:
        try:
            op.drop_column(table_name, old_column)
        except Exception:
            pass

    if has_new:
        try:
            op.alter_column(table_name, new_column, nullable=False)
        except Exception:
            pass

        fk_name = f"fk_{table_name}_{new_column}"
        try:
            op.create_foreign_key(
                fk_name,
                table_name,
                reference_table,
                [new_column],
                ['id']
            )
        except Exception:
            pass

        idx_name = f"ix_{table_name}_{new_column.replace('_', '')[:10]}"
        if len(idx_name) > 64:
            idx_name = f"ix_{table_name}_{new_column.split('_')[-1]}"
        try:
            op.create_index(idx_name, table_name, [new_column])
        except Exception:
            pass

        try:
            op.create_unique_constraint(
                f"uq_{table_name}_owner_name",
                table_name,
                ['owner_operator_id', 'name']
            )
        except Exception:
            pass

        try:
            op.create_index(f"ix_{table_name}_owner", table_name, ['owner_operator_id'])
        except Exception:
            pass


def upgrade():
    conn = op.get_bind()

    fix_table(conn, "template_category", "platform_id", "template_platform_id", "template_platform")
    fix_table(conn, "material_category", "platform_id", "material_platform_id", "material_platform")


def downgrade():
    pass
