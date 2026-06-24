"""
Fix generation task schema mismatch

Revision ID: 20260415_0200
Revises: 20260415_0100
Create Date: 2025-04-15 12:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '20260415_0200'
down_revision = '20260415_0100'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update generation_task and generation_item tables to match ORM models.
    This is a destructive migration - old data will be lost.
    """
    # Drop foreign key constraints first if they exist
    op.execute("SET FOREIGN_KEY_CHECKS=0")

    # ========================================
    # Fix generation_task table
    # ========================================

    # Drop old columns that are not in the ORM model
    columns_to_drop_task = [
        'llm_model_config_id',
        'image_model_config_id',
        'video_model_config_id',
        'auto_switch_model',
        'deduplication_enabled',
        'deduplication_config_json',
        'name',
        'started_at',
        'completed_at',
    ]
    for col in columns_to_drop_task:
        try:
            op.drop_column('generation_task', col)
        except Exception:
            pass  # Column may not exist

    # Add new columns that are in the ORM model but not in DB
    new_columns_task = [
        ('model_platform', sa.String(100), True, None, '选择的模型平台'),
        ('model_id', sa.String(100), True, None, '选择的具体模型'),
        ('model_selection_mode', sa.Enum('auto', 'manual', name='model_selection_mode_enum'), False, 'auto', '模型选择模式'),
        ('max_concurrency', sa.Integer, False, 5, '本次任务最大并发数'),
        ('variable_values_json', sa.JSON, True, None, '变量值JSON'),
        ('dedup_rules_json', sa.JSON, True, None, '去重规则JSON'),
        ('paused_count', sa.Integer, False, 0, '已暂停数量'),
        ('distributed_count', sa.Integer, False, 0, '已分发数量'),
        ('pending_publish_count', sa.Integer, False, 0, '待发布数量'),
        ('published_count', sa.Integer, False, 0, '已发布数量'),
    ]

    for col_name, col_type, nullable, default, comment in new_columns_task:
        try:
            kwargs = {'nullable': nullable, 'comment': comment}
            if default is not None:
                kwargs['server_default'] = str(default)
            op.add_column('generation_task', sa.Column(col_name, col_type, **kwargs))
        except Exception as e:
            print(f"Warning: Could not add column {col_name}: {e}")

    # Update status enum if needed
    try:
        op.alter_column('generation_task', 'status',
            existing_type=mysql.ENUM('pending', 'processing', 'completed', 'failed', 'paused'),
            type_=mysql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled'),
            existing_nullable=False
        )
    except Exception as e:
        print(f"Warning: Could not update status enum: {e}")

    # ========================================
    # Fix generation_item table
    # ========================================

    # Drop old columns
    columns_to_drop_item = [
        'llm_model_config_id',
        'image_model_config_id',
        'video_model_config_id',
        'text_content',
        'generated_video_urls_json',
    ]
    for col in columns_to_drop_item:
        try:
            op.drop_column('generation_item', col)
        except Exception:
            pass

    # Add new columns
    new_columns_item = [
        ('model_platform', sa.String(100), True, None, '实际使用的模型平台'),
        ('model_id', sa.String(100), True, None, '实际使用的模型'),
        ('generated_title', sa.Text, True, None, '生成的标题'),
        ('generated_text', sa.Text, True, None, '生成的文本内容'),
        ('text_file_url', sa.String(500), True, None, '保存到COS的文案文件URL'),
        ('generated_video_url', sa.String(500), True, None, '生成的视频URL'),
        ('distributed_at', sa.DateTime, True, None, '分发时间'),
        ('confirmed_at', sa.DateTime, True, None, '确认发布时间'),
    ]

    for col_name, col_type, nullable, default, comment in new_columns_item:
        try:
            kwargs = {'nullable': nullable, 'comment': comment}
            if default is not None:
                kwargs['server_default'] = str(default)
            op.add_column('generation_item', sa.Column(col_name, col_type, **kwargs))
        except Exception as e:
            print(f"Warning: Could not add column {col_name}: {e}")

    # Update distribution_status enum
    try:
        op.alter_column('generation_item', 'distribution_status',
            existing_type=mysql.ENUM('pending', 'distributed', 'published'),
            type_=mysql.ENUM('draft', 'ready', 'distributed'),
            existing_nullable=False
        )
    except Exception as e:
        print(f"Warning: Could not update distribution_status enum: {e}")

    # Re-enable foreign key checks
    op.execute("SET FOREIGN_KEY_CHECKS=1")


def downgrade():
    """
    Downgrade is not supported for this migration as it's a schema alignment.
    """
    pass
