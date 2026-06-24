"""
用户默认模型设置表 (user_default_model.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import (BigInteger, Column, DateTime, Enum, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserDefaultModel(Base):
    """
    用户默认模型设置表

    支持每个用户（创作管理员/超级管理员）独立设置自己的默认模型，
    删除模型时通过外键 ON DELETE SET NULL 自动回退为 "auto"。
    """

    __tablename__ = "user_default_model"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")

    # 用户标识
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    user_type = Column(
        Enum("super_admin", "operator", name="user_type_enum"),
        nullable=False,
        index=True,
        comment="用户类型：super_admin / operator",
    )

    # 模型类型
    model_type = Column(
        Enum("llm", "image", "video", "embedding", name="model_type_enum"),
        nullable=False,
        comment="模型类型：llm / image / video / embedding",
    )

    # 关联的模型配置（NULL 表示自动选择）
    model_config_id = Column(
        BigInteger,
        ForeignKey("model_config.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的模型配置ID，NULL表示自动选择",
    )

    # 时间字段
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 唯一约束：每个用户每种模型类型只能有一个设置
    __table_args__ = (
        UniqueConstraint(
            "user_id", "user_type", "model_type", name="uq_user_model_type"
        ),
    )

    # 关联关系
    model_config = relationship("ModelConfig", foreign_keys=[model_config_id])

    def __repr__(self):
        return f"<UserDefaultModel(id={self.id}, user_id={self.user_id}, model_type={self.model_type})>"
