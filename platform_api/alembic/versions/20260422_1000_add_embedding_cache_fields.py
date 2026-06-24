"""添加 embedding 缓存字段用于去重优化

Revision ID: 20260422_1000
Revises: 20260421_1730
Create Date: 2026-04-22 10:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260422_1000'
down_revision = '20260421_1730'
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


def upgrade() -> None:
    # 添加 text_embedding 字段（幂等：已存在则跳过）
    if not column_exists('generation_item', 'text_embedding'):
        op.add_column(
            'generation_item',
            sa.Column('text_embedding', sa.JSON(), nullable=True, comment='文案内容的嵌入向量')
        )

    # 添加 image_embeddings 字段（幂等：已存在则跳过）
    if not column_exists('generation_item', 'image_embeddings'):
        op.add_column(
            'generation_item',
            sa.Column('image_embeddings', sa.JSON(), nullable=True, comment='图片内容的嵌入向量列表（多张图片时）')
        )


def downgrade() -> None:
    # 删除 image_embeddings 字段（幂等：已存在才删除）
    if column_exists('generation_item', 'image_embeddings'):
        op.drop_column('generation_item', 'image_embeddings')

    # 删除 text_embedding 字段（幂等：已存在才删除）
    if column_exists('generation_item', 'text_embedding'):
        op.drop_column('generation_item', 'text_embedding')
