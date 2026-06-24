"""add prompt_template table and generation_item prompt template references

Revision ID: 20260421_1400
Revises: 9d82afa1f5f0
Create Date: 2026-04-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260421_1400'
down_revision: Union[str, None] = '9d82afa1f5f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
    # 1. Create prompt_template table（幂等：已存在则跳过）
    if not table_exists('prompt_template'):
        # MySQL uses ENUM inline in column definitions, not as standalone CREATE TYPE
        op.create_table(
            'prompt_template',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, comment="主键"),
            sa.Column('name', sa.String(200), nullable=False, comment="模板名称"),
            sa.Column(
                'template_type',
                sa.Enum('text_system', 'image_system', 'aigc_prompt_generator', name='prompt_template_type_enum'),
                nullable=False, index=True, comment="提示词类型",
            ),
            sa.Column('applicable_platforms', sa.JSON(), nullable=True, comment="适用平台列表"),
            sa.Column('content', sa.Text(), nullable=False, comment="提示词模板内容"),
            sa.Column('variables_hint', sa.Text(), nullable=True, comment="可用变量说明"),
            sa.Column('description', sa.Text(), nullable=True, comment="模板描述"),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0', comment="是否为默认模板"),
            sa.Column(
                'status',
                sa.Enum('enabled', 'disabled', name='prompt_template_status_enum'),
                nullable=False, server_default='enabled', comment="状态",
            ),
            sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, index=True, comment="所属运营管理员ID"),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.utc_timestamp(), comment="创建时间"),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.utc_timestamp(), onupdate=sa.func.utc_timestamp(), comment="更新时间"),
        )

    # 2. Add prompt template references to generation_item（幂等：已存在则跳过）
    if not column_exists('generation_item', 'text_prompt_template_id'):
        op.add_column(
            'generation_item',
            sa.Column(
                'text_prompt_template_id',
                sa.BigInteger(),
                sa.ForeignKey('prompt_template.id'),
                nullable=True,
                comment="使用的文案系统提示词模板ID",
            ),
        )
    if not column_exists('generation_item', 'image_prompt_template_id'):
        op.add_column(
            'generation_item',
            sa.Column(
                'image_prompt_template_id',
                sa.BigInteger(),
                sa.ForeignKey('prompt_template.id'),
                nullable=True,
                comment="使用的图片系统提示词模板ID",
            ),
        )


def downgrade() -> None:
    # 删除字段（幂等：已存在才删除）
    if column_exists('generation_item', 'image_prompt_template_id'):
        op.drop_column('generation_item', 'image_prompt_template_id')
    if column_exists('generation_item', 'text_prompt_template_id'):
        op.drop_column('generation_item', 'text_prompt_template_id')

    # 删除表（幂等：已存在才删除）
    if table_exists('prompt_template'):
        op.drop_table('prompt_template')

    # MySQL ENUM types are dropped automatically with the table/column,
    # no explicit DROP TYPE needed
