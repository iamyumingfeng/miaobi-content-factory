"""
Add refresh_token table for token management

Revision ID: 20260427_1500
Revises: 20260424_1400
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260427_1500'
down_revision = '20260424_1400'
branch_labels = None
depends_on = None


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


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            AND index_name = :index_name
        """),
        {"table_name": table_name, "index_name": index_name}
    )
    return result.fetchone()[0] > 0


def upgrade():
    # 创建 refresh_token 表（幂等：已存在则跳过）
    if not table_exists('refresh_token'):
        op.create_table(
            'refresh_token',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
            sa.Column('token', sa.String(length=512), nullable=False, comment='Refresh Token'),
            sa.Column('jti', sa.String(length=128), nullable=False, comment='JWT ID（用于标识唯一令牌）'),
            sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户 ID'),
            sa.Column('user_type', sa.Enum('super_admin', 'operator', 'sub_user', name='user_type_enum'), nullable=False, comment='用户类型'),
            sa.Column('issued_at', sa.DateTime(), nullable=False, comment='签发时间'),
            sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
            sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='是否已撤销'),
            sa.Column('revoked_at', sa.DateTime(), nullable=True, comment='撤销时间'),
            sa.Column('revoke_reason', sa.String(length=255), nullable=True, comment='撤销原因'),
            sa.Column('device_info', sa.String(length=500), nullable=True, comment='设备信息（浏览器/客户端）'),
            sa.Column('ip_address', sa.String(length=50), nullable=True, comment='IP地址'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.PrimaryKeyConstraint('id')
        )

        # 创建索引（幂等：已存在则跳过）
        indexes = [
            ('idx_refresh_token_token', ['token']),
            ('idx_refresh_token_jti', ['jti']),
            ('idx_refresh_token_user', ['user_id', 'user_type']),
            ('idx_refresh_token_expires_revoked', ['expires_at', 'is_revoked']),
            ('idx_refresh_token_user_type_status', ['user_id', 'user_type', 'is_revoked']),
        ]
        for index_name, columns in indexes:
            if not index_exists('refresh_token', index_name):
                op.create_index(index_name, 'refresh_token', columns, unique=(index_name in ['idx_refresh_token_token', 'idx_refresh_token_jti']))


def downgrade():
    # 删除索引
    indexes = [
        'idx_refresh_token_user_type_status',
        'idx_refresh_token_expires_revoked',
        'idx_refresh_token_user',
        'idx_refresh_token_jti',
        'idx_refresh_token_token',
    ]
    for index_name in indexes:
        if index_exists('refresh_token', index_name):
            op.drop_index(index_name, table_name='refresh_token')

    # 删除表
    if table_exists('refresh_token'):
        op.drop_table('refresh_token')
