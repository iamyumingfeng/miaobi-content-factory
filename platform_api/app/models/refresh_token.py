"""
刷新令牌模型 (refresh_token.py)

用于管理 JWT refresh token，支持用户状态管理。

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    """
    刷新令牌表

    用于存储 refresh token，支持：
    1. Token 自动刷新
    2. 用户在线状态追踪
    3. 强制用户下线
    """
    __tablename__ = "refresh_token"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")

    # Token 本身
    token = Column(String(512), unique=True, nullable=False, index=True, comment="Refresh Token")
    jti = Column(String(128), unique=True, nullable=False, index=True, comment="JWT ID（用于标识唯一令牌）")

    # 用户信息
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    user_type = Column(
        Enum("super_admin", "operator", "sub_user", name="user_type_enum"),
        nullable=False,
        index=True,
        comment="用户类型：super_admin / operator / sub_user"
    )

    # 时间相关
    issued_at = Column(DateTime, nullable=False, default=datetime.now, comment="签发时间")
    expires_at = Column(DateTime, nullable=False, index=True, comment="过期时间")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")

    # 状态管理
    is_revoked = Column(Boolean, nullable=False, default=False, index=True, comment="是否已撤销")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    revoke_reason = Column(String(255), nullable=True, comment="撤销原因")

    # 设备信息（可选）
    device_info = Column(String(500), nullable=True, comment="设备信息（浏览器/客户端）")
    ip_address = Column(String(50), nullable=True, comment="IP地址")

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 索引
    __table_args__ = (
        Index("idx_user_type_status", "user_id", "user_type", "is_revoked"),
        Index("idx_expires_revoked", "expires_at", "is_revoked"),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, user_type={self.user_type})>"

    def is_expired(self) -> bool:
        """检查 token 是否已过期"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """检查 token 是否有效（未过期且未撤销）"""
        return not self.is_revoked and not self.is_expired()
