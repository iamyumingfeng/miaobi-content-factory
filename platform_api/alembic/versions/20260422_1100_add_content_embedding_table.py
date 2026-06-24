"""添加独立的 content_embedding 表用于去重优化

Revision ID: 20260422_1100
Revises: 20260422_1000
Create Date: 2026-04-22 11:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260422_1100'
down_revision = '20260422_1000'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return result.fetchone()[0] > 0


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND index_name = :index_name
        """),
        {"table_name": table_name, "index_name": index_name}
    )
    return result.fetchone()[0] > 0


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


def upgrade() -> None:
    # 创建 content_embedding 表（幂等：已存在则跳过）
    if not table_exists('content_embedding'):
        op.create_table(
            'content_embedding',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
            sa.Column('owner_operator_id', sa.BigInteger(), nullable=False, comment='所属运营管理员ID'),
            sa.Column('generation_item_id', sa.BigInteger(), nullable=True, comment='关联的生成项ID'),
            sa.Column('task_id', sa.BigInteger(), nullable=True, comment='关联的任务ID'),
            sa.Column('content_type', sa.String(length=20), nullable=False, comment='内容类型：text / image'),
            sa.Column('content_index', sa.Integer(), nullable=False, server_default='0', comment='内容索引（多张图片时使用'),
            sa.Column('embedding', sa.JSON(), nullable=False, comment='嵌入向量数据'),
            sa.Column('content_preview', sa.String(length=500), nullable=True, comment='内容预览（文案前100字/图片URL'),
            sa.Column('content_hash', sa.String(length=64), nullable=True, comment='内容哈希（用于快速查找重复内容）'),
            sa.Column('used_for_dedup_count', sa.Integer(), nullable=False, server_default='0', comment='用于去重检测的次数'),
            sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
            sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
            sa.PrimaryKeyConstraint('id'),
        )

        # 创建索引（幂等：已存在则跳过）
        indexes = [
            ('ix_content_embedding_owner_operator_id', ['owner_operator_id']),
            ('ix_content_embedding_generation_item_id', ['generation_item_id']),
            ('ix_content_embedding_task_id', ['task_id']),
            ('ix_content_embedding_content_type', ['content_type']),
            ('ix_content_embedding_content_hash', ['content_hash']),
        ]
        for index_name, columns in indexes:
            if not index_exists('content_embedding', index_name):
                op.create_index(index_name, 'content_embedding', columns)

        # 添加外键约束（幂等：已存在则跳过）
        fks = [
            ('fk_content_embedding_owner_operator_id', 'owner_operator_id', 'operator', 'id'),
            ('fk_content_embedding_generation_item_id', 'generation_item_id', 'generation_item', 'id'),
            ('fk_content_embedding_task_id', 'task_id', 'generation_task', 'id'),
        ]
        for fk_name, local_col, ref_table, ref_col in fks:
            if not foreign_key_exists('content_embedding', fk_name):
                op.create_foreign_key(
                    fk_name,
                    'content_embedding',
                    ref_table,
                    [local_col],
                    [ref_col]
                )

    # 删除之前在 generation_item 表中添加的临时字段（幂等：已存在才删除）
    if column_exists('generation_item', 'image_embeddings'):
        op.drop_column('generation_item', 'image_embeddings')
    if column_exists('generation_item', 'text_embedding'):
        op.drop_column('generation_item', 'text_embedding')


def downgrade() -> None:
    # 恢复之前在 generation_item 表中添加的临时字段（幂等：已存在则跳过）
    if not column_exists('generation_item', 'text_embedding'):
        op.add_column(
            'generation_item',
            sa.Column('text_embedding', sa.JSON(), nullable=True, comment='文案内容的嵌入向量')
        )
    if not column_exists('generation_item', 'image_embeddings'):
        op.add_column(
            'generation_item',
            sa.Column('image_embeddings', sa.JSON(), nullable=True, comment='图片内容的嵌入向量列表（多张图片时）')
        )

    # 删除外键约束（幂等：已存在才删除）
    fks = [
        'fk_content_embedding_task_id',
        'fk_content_embedding_generation_item_id',
        'fk_content_embedding_owner_operator_id',
    ]
    for fk_name in fks:
        if foreign_key_exists('content_embedding', fk_name):
            op.drop_constraint(fk_name, 'content_embedding', type_='foreignkey')

    # 删除索引（幂等：已存在才删除）
    indexes = [
        'ix_content_embedding_content_hash',
        'ix_content_embedding_content_type',
        'ix_content_embedding_task_id',
        'ix_content_embedding_generation_item_id',
        'ix_content_embedding_owner_operator_id',
    ]
    for index_name in indexes:
        if index_exists('content_embedding', index_name):
            op.drop_index(index_name, table_name='content_embedding')

    # 删除表（幂等：已存在才删除）
    if table_exists('content_embedding'):
        op.drop_table('content_embedding')
