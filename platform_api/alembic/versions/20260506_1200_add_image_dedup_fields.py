"""add image dedup detection config fields

Revision ID: 20260506_1200
Revises: 20260506_1100
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260506_1200'
down_revision = '20260506_1100'
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


def add_column_if_not_exists(table_name: str, column_name: str, column: sa.Column) -> None:
    """Add a column if it doesn't exist."""
    if not column_exists(table_name, column_name):
        op.add_column(table_name, column)


def upgrade():
    """添加图片去重检测配置字段（幂等：已存在则跳过）"""

    # ========== GenerationTask 表：添加图片去重配置字段 ==========
    add_column_if_not_exists(
        'generation_task',
        'image_dedup_enabled',
        sa.Column(
            'image_dedup_enabled',
            sa.Boolean(),
            nullable=True,
            server_default=sa.text('1'),
            comment='图片去重检测开关'
        )
    )

    add_column_if_not_exists(
        'generation_task',
        'image_dedup_threshold',
        sa.Column(
            'image_dedup_threshold',
            sa.Float(),
            nullable=True,
            server_default=sa.text('0.8'),
            comment='图片相似度阈值（高于此值认为相似）'
        )
    )

    add_column_if_not_exists(
        'generation_task',
        'image_dedup_retry_count',
        sa.Column(
            'image_dedup_retry_count',
            sa.Integer(),
            nullable=True,
            server_default=sa.text('3'),
            comment='图片去重失败重试次数'
        )
    )

    add_column_if_not_exists(
        'generation_task',
        'image_dedup_scope',
        sa.Column(
            'image_dedup_scope',
            sa.JSON(),
            nullable=True,
            server_default=sa.text('JSON_ARRAY("subuser_image_history")'),
            comment='图片去重范围：subuser_image_history/current_task_images/all_image_history'
        )
    )

    # ========== GenerationItem 表：添加图片去重检测结果字段 ==========
    add_column_if_not_exists(
        'generation_item',
        'image_dedup_passed',
        sa.Column(
            'image_dedup_passed',
            sa.Boolean(),
            nullable=True,
            comment='图片去重检测是否通过（整批图片）'
        )
    )

    add_column_if_not_exists(
        'generation_item',
        'image_dedup_max_similarity',
        sa.Column(
            'image_dedup_max_similarity',
            sa.Float(),
            nullable=True,
            comment='图片最高相似度'
        )
    )

    add_column_if_not_exists(
        'generation_item',
        'image_dedup_similarities_json',
        sa.Column(
            'image_dedup_similarities_json',
            sa.JSON(),
            nullable=True,
            comment='每张图片的相似度列表'
        )
    )

    add_column_if_not_exists(
        'generation_item',
        'image_dedup_referenced_images_json',
        sa.Column(
            'image_dedup_referenced_images_json',
            sa.JSON(),
            nullable=True,
            comment='相似图片引用'
        )
    )

    add_column_if_not_exists(
        'generation_item',
        'image_dedup_checked_at',
        sa.Column(
            'image_dedup_checked_at',
            sa.DateTime(),
            nullable=True,
            comment='图片去重检测时间'
        )
    )

    add_column_if_not_exists(
        'generation_item',
        'image_dedup_retry_count',
        sa.Column(
            'image_dedup_retry_count',
            sa.Integer(),
            nullable=True,
            server_default=sa.text('0'),
            comment='图片去重实际重试次数'
        )
    )


def downgrade():
    """回滚：移除图片去重检测配置字段"""

    # 移除 GenerationTask 表字段
    for col in ['image_dedup_scope', 'image_dedup_retry_count', 'image_dedup_threshold', 'image_dedup_enabled']:
        if column_exists('generation_task', col):
            op.drop_column('generation_task', col)

    # 移除 GenerationItem 表字段
    for col in ['image_dedup_retry_count', 'image_dedup_checked_at', 'image_dedup_referenced_images_json',
                 'image_dedup_similarities_json', 'image_dedup_max_similarity', 'image_dedup_passed']:
        if column_exists('generation_item', col):
            op.drop_column('generation_item', col)
