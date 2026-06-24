"""
Add benchmark_material_id to generation_task

Revision ID: 20260419_1000
Revises: 20260418_1400
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = '20260419_1000'
down_revision = '20260418_1400'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.fetchone()[0] > 0


def foreign_key_exists(table_name: str, fk_name: str) -> bool:
    """Check if a foreign key exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.table_constraints
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND constraint_name = :fk_name
            AND constraint_type = 'FOREIGN KEY'
        """),
        {"table_name": table_name, "fk_name": fk_name}
    )
    return result.fetchone()[0] > 0


def upgrade():
    # 添加字段（幂等：已存在则跳过）
    if not column_exists('generation_task', 'benchmark_material_id'):
        op.add_column(
            'generation_task',
            sa.Column('benchmark_material_id', sa.BigInteger(), nullable=True, comment='素材对标(对标库素材)')
        )

    # 添加外键（幂等：已存在则跳过）
    if not foreign_key_exists('generation_task', 'fk_generation_task_benchmark_material_id'):
        try:
            op.create_foreign_key(
                'fk_generation_task_benchmark_material_id',
                'generation_task', 'material',
                ['benchmark_material_id'], ['id']
            )
        except Exception:
            pass


def downgrade():
    # 删除外键（幂等：已存在才删除）
    if foreign_key_exists('generation_task', 'fk_generation_task_benchmark_material_id'):
        try:
            op.drop_constraint('fk_generation_task_benchmark_material_id', 'generation_task', type_='foreignkey')
        except Exception:
            pass

    # 删除字段（幂等：已存在才删除）
    if column_exists('generation_task', 'benchmark_material_id'):
        op.drop_column('generation_task', 'benchmark_material_id')