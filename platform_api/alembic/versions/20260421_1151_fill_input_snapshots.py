"""填充子任务输入快照字段历史数据

Revision ID: 20260421_1151
Revises: 79c638819ac6
Create Date: 2026-04-21 11:51:00

注意：此迁移仅填充空字段，不会覆盖已有数据
"""
from typing import Optional
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON

# revision identifiers
revision = '20260421_1151'
down_revision = '20260421_1045'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    填充 generation_item 表的输入快照字段
    从关联的 sub_user 和 template 表中提取数据
    """
    conn = op.get_bind()

    # 1. 填充子用户相关快照字段
    # 通过 sub_user_id 关联 sub_user 表获取子用户信息
    update_sub_user_sql = """
    UPDATE generation_item gi
    INNER JOIN sub_user su ON gi.sub_user_id = su.id
    SET
        gi.sub_user_name = COALESCE(gi.sub_user_name, NULLIF(CONCAT(IFNULL(su.nickname, ''), IFNULL(su.display_name, ''), ''), '')),
        gi.input_sub_user_profile = COALESCE(gi.input_sub_user_profile, su.fan_profile),
        gi.input_sub_user_positioning = COALESCE(gi.input_sub_user_positioning, su.user_positioning),
        gi.input_sub_user_style = COALESCE(gi.input_sub_user_style, su.content_style)
    WHERE gi.sub_user_id IS NOT NULL
      AND (
        gi.sub_user_name IS NULL
        OR gi.input_sub_user_profile IS NULL
        OR gi.input_sub_user_positioning IS NULL
        OR gi.input_sub_user_style IS NULL
      )
    """
    conn.execute(sa.text(update_sub_user_sql))

    # 2. 填充模板相关快照字段
    # 通过 template_id 关联 template 表获取模板信息
    update_template_sql = """
    UPDATE generation_item gi
    INNER JOIN template t ON gi.template_id = t.id
    SET
        gi.input_prompt_creativity = COALESCE(gi.input_prompt_creativity, t.description),
        gi.input_prompt_instruction = COALESCE(gi.input_prompt_instruction, t.prompt_template),
        gi.input_image_size_ratio = COALESCE(gi.input_image_size_ratio, t.image_size_ratio),
        gi.input_watermark = COALESCE(gi.input_watermark, CASE WHEN t.add_watermark = 1 THEN 1 WHEN t.add_watermark = 0 THEN 0 ELSE NULL END)
    WHERE gi.template_id IS NOT NULL
      AND (
        gi.input_prompt_creativity IS NULL
        OR gi.input_prompt_instruction IS NULL
        OR gi.input_image_size_ratio IS NULL
        OR gi.input_watermark IS NULL
      )
    """
    conn.execute(sa.text(update_template_sql))

    print("[Migration] 子任务输入快照字段填充完成")


def downgrade() -> None:
    """
    回滚：不填充任何字段（downgrade 不做数据回滚）
    """
    pass
