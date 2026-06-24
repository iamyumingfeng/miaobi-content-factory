"""add scheduled_task table

Revision ID: 20260515_1000
Revises: 20260514_1300
Create Date: 2026-05-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260515_1000'
down_revision = '20260514_1300'
branch_labels = None
depends_on = None


def upgrade():
    """创建定时任务表"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    # 如果表已存在，跳过
    if 'scheduled_task' in tables:
        return

    op.create_table(
        'scheduled_task',
        # 主键
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
        
        # 基本信息
        sa.Column('name', sa.String(200), nullable=False, comment='定时任务名称'),
        
        # 调度配置
        sa.Column(
            'schedule_type',
            sa.Enum('daily', 'weekly', name='schedule_type_enum'),
            nullable=False,
            comment='调度类型：daily(每日) / weekly(每周)'
        ),
        sa.Column(
            'schedule_config_json',
            sa.JSON(),
            nullable=False,
            comment="调度配置JSON。daily格式: {'times': ['09:00', '18:00']}; weekly格式: {'days': [1,3,5], 'times': ['09:00']}"
        ),
        
        # 任务类型配置
        sa.Column(
            'task_type',
            sa.Enum('custom', 'benchmark', name='scheduled_task_type_enum'),
            nullable=False,
            server_default='custom',
            comment='任务类型：custom(自定义文案) / benchmark(对标文案)'
        ),
        
        # 素材和模板配置
        sa.Column('material_id', sa.BigInteger(), nullable=True, comment='素材ID'),
        sa.Column('template_ids_json', sa.JSON(), nullable=True, comment='模板ID列表JSON [1, 2, 3]'),
        sa.Column('sub_user_ids_json', sa.JSON(), nullable=False, comment='目标子用户ID列表JSON [1, 2, 3]'),
        
        # 模型配置
        sa.Column('model_platform', sa.String(100), nullable=True, comment='选择的文本模型平台'),
        sa.Column('model_id', sa.String(100), nullable=True, comment='选择的文本模型ID'),
        sa.Column('image_model_platform', sa.String(100), nullable=True, comment='选择的图片模型平台'),
        sa.Column('image_model_id', sa.String(100), nullable=True, comment='选择的图片模型ID'),
        sa.Column(
            'model_selection_mode',
            sa.Enum('auto', 'manual', name='scheduled_model_selection_mode_enum'),
            nullable=False,
            server_default='auto',
            comment='模型选择模式：auto（自动选择）/ manual（手动指定）'
        ),
        sa.Column('max_concurrency', sa.Integer(), nullable=False, server_default='5', comment='本次任务最大并发数'),
        sa.Column('image_count', sa.Integer(), nullable=True, server_default='4', comment='生成图片数量'),
        
        # 变量值和去重配置
        sa.Column('variable_values_json', sa.JSON(), nullable=True, comment='变量值JSON'),
        
        # 文案去重配置
        sa.Column('dedup_enabled', sa.Boolean(), nullable=True, comment='文案去重检测开关'),
        sa.Column('dedup_threshold', sa.Integer(), nullable=True, comment='文案去重阈值（0-100）'),
        sa.Column('dedup_retry_count', sa.Integer(), nullable=True, comment='文案去重失败重试次数'),
        sa.Column('dedup_scope', sa.JSON(), nullable=True, comment='文案去重范围配置'),
        
        # 图片去重配置
        sa.Column('image_dedup_enabled', sa.Boolean(), nullable=True, comment='图片去重检测开关'),
        sa.Column('image_dedup_threshold', sa.Integer(), nullable=True, comment='图片相似度阈值（0-100）'),
        sa.Column('image_dedup_retry_count', sa.Integer(), nullable=True, comment='图片去重失败重试次数'),
        sa.Column('image_dedup_scope', sa.JSON(), nullable=True, comment='图片去重范围'),
        
        # 对标配置
        sa.Column('benchmark_text_enabled', sa.Boolean(), nullable=True, comment='文案对标开关'),
        sa.Column('benchmark_image_enabled', sa.Boolean(), nullable=True, comment='图片对标开关'),
        sa.Column('benchmark_image_reference_options', sa.JSON(), nullable=True, comment='图片参考选项'),
        sa.Column('benchmark_image_roles_json', sa.JSON(), nullable=True, comment='对标图角色配置'),
        sa.Column('template_product_mapping_json', sa.JSON(), nullable=True, comment='模板产品映射'),
        
        # 任务状态
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
        sa.Column(
            'status',
            sa.Enum('active', 'paused', 'disabled', name='scheduled_task_status_enum'),
            nullable=False,
            server_default='active',
            comment='任务状态：active(活跃) / paused(暂停) / disabled(禁用)'
        ),
        
        # 执行统计
        sa.Column('total_executions', sa.Integer(), nullable=False, server_default='0', comment='总执行次数'),
        sa.Column('successful_executions', sa.Integer(), nullable=False, server_default='0', comment='成功执行次数'),
        sa.Column('failed_executions', sa.Integer(), nullable=False, server_default='0', comment='失败执行次数'),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True, comment='最后执行时间'),
        sa.Column('last_execution_status', sa.String(50), nullable=True, comment='最后执行状态'),
        
        # 下次执行时间
        sa.Column('next_run_at', sa.DateTime(), nullable=True, comment='下次执行时间'),
        
        # 多租户隔离
        sa.Column('owner_operator_id', sa.BigInteger(), nullable=False, comment='所属运营管理员ID'),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='创建者运营管理员ID'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        # 主键约束
        sa.PrimaryKeyConstraint('id'),
        
        # 外键约束
        sa.ForeignKeyConstraint(['material_id'], ['material.id']),
        sa.ForeignKeyConstraint(['owner_operator_id'], ['operator.id']),
        sa.ForeignKeyConstraint(['created_by'], ['operator.id']),
    )
    
    # 创建索引
    op.create_index('ix_scheduled_task_owner_operator_id', 'scheduled_task', ['owner_operator_id'])
    op.create_index('ix_scheduled_task_next_run_at', 'scheduled_task', ['next_run_at'])
    op.create_index('ix_scheduled_task_status_active', 'scheduled_task', ['is_active', 'status', 'next_run_at'])


def downgrade():
    """删除定时任务表"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'scheduled_task' in tables:
        op.drop_index('ix_scheduled_task_status_active', table_name='scheduled_task')
        op.drop_index('ix_scheduled_task_next_run_at', table_name='scheduled_task')
        op.drop_index('ix_scheduled_task_owner_operator_id', table_name='scheduled_task')
        op.drop_table('scheduled_task')
