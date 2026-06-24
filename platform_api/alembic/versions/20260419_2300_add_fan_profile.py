"""
添加粉丝画像字段 (fan_profile)

Revision ID: 20260419_2300
Revises: 20260419_1200
Create Date: 2026-04-19 23:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260419_2300"
down_revision = "20260419_1200"
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
    # 为三个用户表添加 fan_profile 字段（幂等：已存在则跳过）
    # super_admin 表
    if not column_exists('super_admin', 'fan_profile'):
        op.add_column("super_admin", sa.Column("fan_profile", sa.String(500), nullable=True, comment="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）"))
    # operator 表
    if not column_exists('operator', 'fan_profile'):
        op.add_column("operator", sa.Column("fan_profile", sa.String(500), nullable=True, comment="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）"))
    # sub_user 表
    if not column_exists('sub_user', 'fan_profile'):
        op.add_column("sub_user", sa.Column("fan_profile", sa.String(500), nullable=True, comment="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）"))


def downgrade() -> None:
    # 删除三个用户表的 fan_profile 字段（幂等：已存在才删除）
    if column_exists('sub_user', 'fan_profile'):
        op.drop_column("sub_user", "fan_profile")
    if column_exists('operator', 'fan_profile'):
        op.drop_column("operator", "fan_profile")
    if column_exists('super_admin', 'fan_profile'):
        op.drop_column("super_admin", "fan_profile")