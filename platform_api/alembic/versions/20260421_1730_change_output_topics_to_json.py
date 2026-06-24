"""修改 output_topics 字段为 JSON 类型

Revision ID: 20260421_1730
Revises: 20260421_1700
Create Date: 2026-04-21 17:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '20260421_1730'
down_revision = '20260421_1700'
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


def get_column_type(table_name: str, column_name: str) -> str | None:
    """Get the data type of a column."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT DATA_TYPE
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    row = result.fetchone()
    return row[0] if row else None


def upgrade() -> None:
    # 检查字段是否存在且类型不是 JSON
    if column_exists('generation_item', 'output_topics'):
        current_type = get_column_type('generation_item', 'output_topics')
        if current_type and current_type.lower() != 'json':
            # 先将现有非空数据设置为 NULL
            conn = op.get_bind()
            conn.execute(text("UPDATE generation_item SET output_topics = NULL WHERE output_topics IS NOT NULL"))

            # 修改 output_topics 字段从 String(500) 改为 JSON
            op.alter_column(
                'generation_item',
                'output_topics',
                existing_type=sa.String(500),
                type_=sa.JSON(),
                existing_nullable=True,
                existing_comment='输出话题'
            )


def downgrade() -> None:
    # 检查字段是否存在且类型是 JSON
    if column_exists('generation_item', 'output_topics'):
        current_type = get_column_type('generation_item', 'output_topics')
        if current_type and current_type.lower() == 'json':
            # 先将现有非空数据设置为 NULL
            conn = op.get_bind()
            conn.execute(text("UPDATE generation_item SET output_topics = NULL WHERE output_topics IS NOT NULL"))

            # 回退为 String(500)
            op.alter_column(
                'generation_item',
                'output_topics',
                existing_type=sa.JSON(),
                type_=sa.String(500),
                existing_nullable=True,
                existing_comment='输出话题'
            )