"""新增去重配置和current_step字段

Revision ID: 20260421_1600
Revises: 20260421_1530
Create Date: 2026-04-21 16:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260421_1600'
down_revision = '20260421_1530'
branch_labels = None
depends_on = None


def _column_exists(table, column) -> bool:
    """检查列是否已存在"""
    inspector = inspect(op.get_bind())
    return column in [c['name'] for c in inspector.get_columns(table)]


def upgrade() -> None:
    # ============================================
    # GenerationTask 表新增字段（幂等：已存在则跳过）
    # ============================================
    if not _column_exists('generation_task', 'image_count'):
        op.add_column('generation_task', sa.Column('image_count', sa.Integer(), nullable=True, comment='生成图片数量'))
    if not _column_exists('generation_task', 'dedup_enabled'):
        op.add_column('generation_task', sa.Column('dedup_enabled', sa.Boolean(), nullable=True, default=True, comment='去重检测开关'))
    if not _column_exists('generation_task', 'dedup_threshold'):
        op.add_column('generation_task', sa.Column('dedup_threshold', sa.Float(), nullable=True, default=0.8, comment='去重阈值'))
    if not _column_exists('generation_task', 'dedup_retry_count'):
        op.add_column('generation_task', sa.Column('dedup_retry_count', sa.Integer(), nullable=True, default=3, comment='去重失败重试次数'))

    # ============================================
    # GenerationItem 表新增字段（幂等：已存在则跳过）
    # ============================================
    if not _column_exists('generation_item', 'aigc_user_copy_prompt'):
        op.add_column('generation_item', sa.Column('aigc_user_copy_prompt', sa.Text(), nullable=True, comment='AIGC生成的文案用户提示词'))
    if not _column_exists('generation_item', 'aigc_user_image_prompts_json'):
        op.add_column('generation_item', sa.Column('aigc_user_image_prompts_json', sa.JSON(), nullable=True, comment='AIGC生成的图片用户提示词列表'))
    if not _column_exists('generation_item', 'dedup_check_passed'):
        op.add_column('generation_item', sa.Column('dedup_check_passed', sa.Boolean(), nullable=True, comment='去重检测是否通过'))
    if not _column_exists('generation_item', 'dedup_similarity'):
        op.add_column('generation_item', sa.Column('dedup_similarity', sa.Float(), nullable=True, comment='最大相似度'))
    if not _column_exists('generation_item', 'dedup_referenced_items_json'):
        op.add_column('generation_item', sa.Column('dedup_referenced_items_json', sa.JSON(), nullable=True, comment='相似内容引用'))
    if not _column_exists('generation_item', 'dedup_checked_at'):
        op.add_column('generation_item', sa.Column('dedup_checked_at', sa.DateTime(), nullable=True, comment='去重检测时间'))
    if not _column_exists('generation_item', 'generated_image_count'):
        op.add_column('generation_item', sa.Column('generated_image_count', sa.Integer(), nullable=True, comment='实际生成图片数量'))
    if not _column_exists('generation_item', 'current_step'):
        op.add_column('generation_item', sa.Column('current_step', sa.String(50), nullable=True, comment='当前执行步骤'))


def downgrade() -> None:
    # GenerationItem 表字段回退
    op.drop_column('generation_item', 'current_step')
    op.drop_column('generation_item', 'generated_image_count')
    op.drop_column('generation_item', 'dedup_checked_at')
    op.drop_column('generation_item', 'dedup_referenced_items_json')
    op.drop_column('generation_item', 'dedup_similarity')
    op.drop_column('generation_item', 'dedup_check_passed')
    op.drop_column('generation_item', 'aigc_user_image_prompts_json')
    op.drop_column('generation_item', 'aigc_user_copy_prompt')

    # GenerationTask 表字段回退
    op.drop_column('generation_task', 'dedup_retry_count')
    op.drop_column('generation_task', 'dedup_threshold')
    op.drop_column('generation_task', 'dedup_enabled')
    op.drop_column('generation_task', 'image_count')
