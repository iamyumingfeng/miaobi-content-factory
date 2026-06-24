"""rebuild user tables with unified structure

Revision ID: 20260415_0100
Revises: 20260414_1400
Create Date: 2026-04-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260415_0100'
down_revision = '20260414_1400'
branch_labels = None
depends_on = None


def drop_table_if_exists(table_name):
    """Helper function to drop table only if it exists"""
    conn = op.get_bind()
    # Check if table exists
    result = conn.execute(sa.text(f"SHOW TABLES LIKE '{table_name}'"))
    if result.fetchone():
        op.drop_table(table_name)


def upgrade():
    # 禁用外键约束
    conn = op.get_bind()
    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 0"))

    # 1. 删除有外键约束的表先
    drop_table_if_exists('user_tag_rel')
    drop_table_if_exists('user_tag')

    # 2. 删除通知和操作日志（它们有用户外键）
    drop_table_if_exists('operation_log')
    drop_table_if_exists('notification')

    # 3. 删除其他关联表
    drop_table_if_exists('material_favorite')
    drop_table_if_exists('material_tag_rel')
    drop_table_if_exists('material_tag')
    drop_table_if_exists('material_attachment')
    drop_table_if_exists('material')

    drop_table_if_exists('template_tag_rel')
    drop_table_if_exists('template_tag')
    drop_table_if_exists('template')
    drop_table_if_exists('template_platform')

    drop_table_if_exists('generation_task_template')
    drop_table_if_exists('generation_task_subuser')
    drop_table_if_exists('generation_task_progress_log')
    drop_table_if_exists('generation_item')
    drop_table_if_exists('generation_task')

    drop_table_if_exists('distribution')
    drop_table_if_exists('publish_account')

    drop_table_if_exists('cleanup_rule')
    drop_table_if_exists('model_config')

    # 4. 删除用户表
    drop_table_if_exists('sub_user')
    drop_table_if_exists('operator')
    drop_table_if_exists('super_admin')

    # 5. 重建用户表 - 结构完全一致
    # super_admin
    op.create_table('super_admin',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('userid', sa.String(length=64), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('wechat_openid', sa.String(length=100), nullable=True),
        sa.Column('wechat_unionid', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('online', 'offline', 'disabled', name='user_status_enum'), nullable=False, server_default='offline'),
        sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('user_positioning', sa.String(length=255), nullable=True),
        sa.Column('user_category', sa.String(length=100), nullable=True),
        sa.Column('content_style', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=True),
        sa.Column('managed_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('userid')
    )
    op.create_index(op.f('ix_super_admin_created_by'), 'super_admin', ['created_by'], unique=False)
    op.create_index(op.f('ix_super_admin_owner_operator_id'), 'super_admin', ['owner_operator_id'], unique=False)
    op.create_index(op.f('ix_super_admin_managed_by'), 'super_admin', ['managed_by'], unique=False)
    op.create_index(op.f('ix_super_admin_status'), 'super_admin', ['status'], unique=False)
    op.create_index(op.f('ix_super_admin_userid'), 'super_admin', ['userid'], unique=True)

    # operator
    op.create_table('operator',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('userid', sa.String(length=64), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('wechat_openid', sa.String(length=100), nullable=True),
        sa.Column('wechat_unionid', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('online', 'offline', 'disabled', name='user_status_enum'), nullable=False, server_default='offline'),
        sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('user_positioning', sa.String(length=255), nullable=True),
        sa.Column('user_category', sa.String(length=100), nullable=True),
        sa.Column('content_style', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=True),
        sa.Column('managed_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('userid'),
        sa.ForeignKeyConstraint(['created_by'], ['super_admin.id'], ),
    )
    op.create_index(op.f('ix_operator_created_by'), 'operator', ['created_by'], unique=False)
    op.create_index(op.f('ix_operator_owner_operator_id'), 'operator', ['owner_operator_id'], unique=False)
    op.create_index(op.f('ix_operator_managed_by'), 'operator', ['managed_by'], unique=False)
    op.create_index(op.f('ix_operator_status'), 'operator', ['status'], unique=False)
    op.create_index(op.f('ix_operator_userid'), 'operator', ['userid'], unique=True)

    # sub_user
    op.create_table('sub_user',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('userid', sa.String(length=64), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('wechat_openid', sa.String(length=100), nullable=True),
        sa.Column('wechat_unionid', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('online', 'offline', 'disabled', name='user_status_enum'), nullable=False, server_default='offline'),
        sa.Column('login_failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('user_positioning', sa.String(length=255), nullable=True),
        sa.Column('user_category', sa.String(length=100), nullable=True),
        sa.Column('content_style', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('managed_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('userid'),
        sa.ForeignKeyConstraint(['created_by'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['managed_by'], ['operator.id'], ),
    )
    op.create_index(op.f('ix_sub_user_created_by'), 'sub_user', ['created_by'], unique=False)
    op.create_index(op.f('ix_sub_user_owner_operator_id'), 'sub_user', ['owner_operator_id'], unique=False)
    op.create_index(op.f('ix_sub_user_managed_by'), 'sub_user', ['managed_by'], unique=False)
    op.create_index(op.f('ix_sub_user_status'), 'sub_user', ['status'], unique=False)
    op.create_index(op.f('ix_sub_user_userid'), 'sub_user', ['userid'], unique=True)

    # 6. 重建其他表
    # user_tag
    op.create_table('user_tag',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('tag_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # user_tag_rel
    op.create_table('user_tag_rel',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('tag_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tag_id'], ['user_tag.id'], ),
    )

    # template_platform
    op.create_table('template_platform',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
    )
    op.create_index(op.f('ix_template_platform_owner_operator_id'), 'template_platform', ['owner_operator_id'], unique=False)

    # template_tag
    op.create_table('template_tag',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # template
    op.create_table('template',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('content_type', sa.Enum('text', 'image_text', 'video_text', name='template_content_type_enum'), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('variables_json', sa.JSON(), nullable=True),
        sa.Column('style_reference', sa.String(length=1000), nullable=True),
        sa.Column('platform_rules_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('enabled', 'disabled', name='template_status_enum'), nullable=False),
        sa.Column('platform_id', sa.BigInteger(), nullable=True),
        sa.Column('original_template_id', sa.BigInteger(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['platform_id'], ['template_platform.id'], ),
        sa.ForeignKeyConstraint(['original_template_id'], ['template.id'], ),
    )
    op.create_index(op.f('ix_template_owner_operator_id'), 'template', ['owner_operator_id'], unique=False)

    # template_tag_rel
    op.create_table('template_tag_rel',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.BigInteger(), nullable=False),
        sa.Column('tag_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tag_id'], ['template_tag.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
    )

    # material_tag
    op.create_table('material_tag',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
    )
    op.create_index(op.f('ix_material_tag_owner_operator_id'), 'material_tag', ['owner_operator_id'], unique=False)

    # material
    op.create_table('material',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_type', sa.Enum('upload', 'link', 'description', name='material_source_type_enum'), nullable=False),
        sa.Column('content_type', sa.Enum('text', 'image_text', 'video_text', 'mix', name='material_content_type_enum'), nullable=False),
        sa.Column('image_count', sa.Integer(), nullable=False),
        sa.Column('video_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('available', 'disabled', name='material_status_enum'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
    )
    op.create_index(op.f('ix_material_owner_operator_id'), 'material', ['owner_operator_id'], unique=False)

    # material_attachment
    op.create_table('material_attachment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('material_id', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.Enum('image', 'video', name='material_attachment_type_enum'), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    )

    # material_tag_rel
    op.create_table('material_tag_rel',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('material_id', sa.BigInteger(), nullable=False),
        sa.Column('tag_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['material_tag.id'], ),
    )

    # material_favorite
    op.create_table('material_favorite',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('material_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    )

    # generation_task
    op.create_table('generation_task',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('material_id', sa.BigInteger(), nullable=True),
        sa.Column('llm_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('image_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('video_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('auto_switch_model', sa.Boolean(), nullable=False),
        sa.Column('deduplication_enabled', sa.Boolean(), nullable=False),
        sa.Column('deduplication_config_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'paused', name='generation_task_status_enum'), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('queued_count', sa.Integer(), nullable=False),
        sa.Column('generating_count', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('paused_count', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
    )
    op.create_index(op.f('ix_generation_task_owner_operator_id'), 'generation_task', ['owner_operator_id'], unique=False)

    # generation_task_template
    op.create_table('generation_task_template',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('template_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['generation_task.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
    )

    # generation_task_subuser
    op.create_table('generation_task_subuser',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['generation_task.id'], ),
    )

    # generation_item
    op.create_table('generation_item',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=False),
        sa.Column('template_id', sa.BigInteger(), nullable=True),
        sa.Column('llm_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('image_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('video_model_config_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('queued', 'generating', 'completed', 'failed', 'paused', name='generation_item_status_enum'), nullable=False),
        sa.Column('distribution_status', sa.Enum('pending', 'distributed', 'published', name='distribution_status_enum'), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('generated_image_urls_json', sa.JSON(), nullable=True),
        sa.Column('generated_video_urls_json', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('queued_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['generation_task.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
    )
    op.create_index(op.f('ix_generation_item_owner_operator_id'), 'generation_item', ['owner_operator_id'], unique=False)

    # generation_task_progress_log
    op.create_table('generation_task_progress_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('queued_count', sa.Integer(), nullable=False),
        sa.Column('generating_count', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('paused_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['generation_task.id'], ),
    )

    # publish_account
    op.create_table('publish_account',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=False),
        sa.Column('platform_name', sa.String(length=100), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_config_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
    )

    # distribution
    op.create_table('distribution',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.BigInteger(), nullable=False),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=False),
        sa.Column('publish_account_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'distributed', 'published', name='distribution_status_enum'), nullable=False),
        sa.Column('distributed_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['item_id'], ['generation_item.id'], ),
        sa.ForeignKeyConstraint(['publish_account_id'], ['publish_account.id'], ),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
    )

    # cleanup_rule
    op.create_table('cleanup_rule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('retention_period', sa.Enum('month', 'quarter', 'year', name='retention_period_enum'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # model_config
    op.create_table('model_config',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('model_type', sa.Enum('llm', 'image', 'video', name='model_type_enum'), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('max_concurrency', sa.Integer(), nullable=False),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', name='model_config_status_enum'), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['super_admin.id'], ),
    )

    # notification
    op.create_table('notification',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('super_admin_id', sa.BigInteger(), nullable=True),
        sa.Column('operator_id', sa.BigInteger(), nullable=True),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=True),
        sa.Column('type', sa.Enum('task_completed', 'task_failed', 'cleanup_reminder', 'content_received', name='notification_type_enum'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('related_id', sa.BigInteger(), nullable=True),
        sa.Column('related_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['operator_id'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
        sa.ForeignKeyConstraint(['super_admin_id'], ['super_admin.id'], ),
    )

    # operation_log
    op.create_table('operation_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('super_admin_id', sa.BigInteger(), nullable=True),
        sa.Column('operator_id', sa.BigInteger(), nullable=True),
        sa.Column('sub_user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('record_id', sa.BigInteger(), nullable=True),
        sa.Column('old_value_json', sa.JSON(), nullable=True),
        sa.Column('new_value_json', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['operator_id'], ['operator.id'], ),
        sa.ForeignKeyConstraint(['sub_user_id'], ['sub_user.id'], ),
        sa.ForeignKeyConstraint(['super_admin_id'], ['super_admin.id'], ),
    )

    # 重新启用外键约束
    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 1"))


def downgrade():
    pass
