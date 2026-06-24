"""
添加模板图片尺寸比例和水印设置

Revision ID: 20260420_0100
Revises: 20260419_2300
Create Date: 2026-04-20 01:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260420_0100"
down_revision = "20260419_2300"
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
    # 为 template 表添加图片尺寸比例和水印字段（幂等：已存在则跳过）
    if not column_exists('template', 'image_size_ratio'):
        op.add_column("template", sa.Column("image_size_ratio", sa.String(20), nullable=True, comment="图片尺寸比例：1:1(2048x2048)/4:3(2304x1728)/16:9(2560x1440)/3:4(1728x2304)/9:16(1440x2560)"))
    if not column_exists('template', 'add_watermark'):
        op.add_column("template", sa.Column("add_watermark", sa.Boolean(), nullable=False, default=True, server_default=sa.text("1"), comment="是否添加水印"))


def downgrade() -> None:
    # 删除字段（幂等：已存在才删除）
    if column_exists('template', 'add_watermark'):
        op.drop_column("template", "add_watermark")
    if column_exists('template', 'image_size_ratio'):
        op.drop_column("template", "image_size_ratio")