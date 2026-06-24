"""add_input_snapshots_output_prompts_and_execution_tracking_to_generation_item

Revision ID: 79c638819ac6
Revises: 20260420_1930
Create Date: 2026-04-21 10:20:13.953028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '79c638819ac6'
down_revision: Union[str, None] = '20260420_1930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('generation_item')]

    def add_if_missing(col_name, col_def):
        if col_name not in columns:
            op.add_column('generation_item', col_def)

    # 输入内容快照字段
    add_if_missing('sub_user_name', sa.Column('sub_user_name', sa.String(100), nullable=True, comment='子用户名称快照（昵称）'))
    add_if_missing('input_prompt_creativity', sa.Column('input_prompt_creativity', sa.Text(), nullable=True, comment='模板提示词创意（description）'))
    add_if_missing('input_prompt_instruction', sa.Column('input_prompt_instruction', sa.Text(), nullable=True, comment='模板提示词指令（prompt_template）'))
    add_if_missing('input_template_images_json', sa.Column('input_template_images_json', sa.JSON(), nullable=True, comment='模板图片URL列表'))
    add_if_missing('input_image_size_ratio', sa.Column('input_image_size_ratio', sa.String(20), nullable=True, comment='输出图片尺寸比例（如 16:9）'))
    add_if_missing('input_watermark', sa.Column('input_watermark', sa.Integer(), nullable=True, comment='输出图片水印开关（1=开 0=关）'))
    add_if_missing('input_benchmark_title', sa.Column('input_benchmark_title', sa.String(200), nullable=True, comment='素材对标标题'))
    add_if_missing('input_benchmark_content', sa.Column('input_benchmark_content', sa.Text(), nullable=True, comment='素材对标内容'))
    add_if_missing('input_benchmark_topic', sa.Column('input_benchmark_topic', sa.String(200), nullable=True, comment='素材对标话题'))
    add_if_missing('input_benchmark_images_json', sa.Column('input_benchmark_images_json', sa.JSON(), nullable=True, comment='素材对标图片URL列表'))
    add_if_missing('input_sub_user_profile', sa.Column('input_sub_user_profile', sa.Text(), nullable=True, comment='子用户粉丝画像'))
    add_if_missing('input_sub_user_positioning', sa.Column('input_sub_user_positioning', sa.String(500), nullable=True, comment='子用户账号定位'))
    add_if_missing('input_sub_user_style', sa.Column('input_sub_user_style', sa.String(500), nullable=True, comment='子用户内容风格'))

    # 输出内容字段
    add_if_missing('output_system_text_prompt', sa.Column('output_system_text_prompt', sa.Text(), nullable=True, comment='AIGC文案系统提示词'))
    add_if_missing('output_user_text_prompt', sa.Column('output_user_text_prompt', sa.Text(), nullable=True, comment='AIGC文案用户提示词'))
    add_if_missing('output_system_image_prompt', sa.Column('output_system_image_prompt', sa.Text(), nullable=True, comment='图片系统提示词'))
    add_if_missing('output_user_image_prompt', sa.Column('output_user_image_prompt', sa.Text(), nullable=True, comment='图片用户提示词'))
    add_if_missing('output_topics', sa.Column('output_topics', sa.String(500), nullable=True, comment='输出话题'))

    # 执行情况字段
    add_if_missing('execution_started_at', sa.Column('execution_started_at', sa.DateTime(), nullable=True, comment='子任务执行开始时间'))
    add_if_missing('execution_ended_at', sa.Column('execution_ended_at', sa.DateTime(), nullable=True, comment='子任务执行结束时间'))
    add_if_missing('execution_result', sa.Column('execution_result', sa.String(20), nullable=True, comment='执行结果：success / failed / partial'))


def downgrade() -> None:
    op.drop_column('generation_item', 'execution_result')
    op.drop_column('generation_item', 'execution_ended_at')
    op.drop_column('generation_item', 'execution_started_at')
    op.drop_column('generation_item', 'output_topics')
    op.drop_column('generation_item', 'output_user_image_prompt')
    op.drop_column('generation_item', 'output_system_image_prompt')
    op.drop_column('generation_item', 'output_user_text_prompt')
    op.drop_column('generation_item', 'output_system_text_prompt')
    op.drop_column('generation_item', 'input_sub_user_style')
    op.drop_column('generation_item', 'input_sub_user_positioning')
    op.drop_column('generation_item', 'input_sub_user_profile')
    op.drop_column('generation_item', 'input_benchmark_images_json')
    op.drop_column('generation_item', 'input_benchmark_topic')
    op.drop_column('generation_item', 'input_benchmark_content')
    op.drop_column('generation_item', 'input_watermark')
    op.drop_column('generation_item', 'input_image_size_ratio')
    op.drop_column('generation_item', 'input_template_images_json')
    op.drop_column('generation_item', 'input_prompt_instruction')
    op.drop_column('generation_item', 'input_prompt_creativity')
    op.drop_column('generation_item', 'sub_user_name')
