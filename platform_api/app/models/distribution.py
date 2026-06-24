"""
内容分发模型 (distribution.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import (BigInteger, Column, DateTime, Enum, ForeignKey,
                        String)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Distribution(Base):
    """
    分发记录表
    """

    __tablename__ = "distribution"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_id = Column(
        BigInteger,
        ForeignKey("generation_task.id"),
        nullable=False,
        index=True,
        comment="任务ID",
    )
    generation_item_id = Column(
        BigInteger,
        ForeignKey("generation_item.id"),
        nullable=False,
        comment="分发的内容项",
    )
    sub_user_id = Column(
        BigInteger,
        ForeignKey("sub_user.id"),
        nullable=False,
        index=True,
        comment="接收的创作者ID",
    )
    publish_status = Column(
        Enum("distributed", "pending_publish", "published", name="publish_status_enum"),
        nullable=False,
        default="distributed",
        comment="发布状态：distributed / pending_publish / published",
    )
    distributed_at = Column(DateTime, nullable=True, comment="分发时间")
    confirmed_at = Column(DateTime, nullable=True, comment="确认发布时间")
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    # 关联
    task = relationship(
        "GenerationTask", back_populates="distributions", foreign_keys=[task_id]
    )
    generation_item = relationship(
        "GenerationItem",
        back_populates="distributions",
        foreign_keys=[generation_item_id],
    )
    sub_user = relationship(
        "SubUser", back_populates="distributions", foreign_keys=[sub_user_id]
    )

    def __repr__(self):
        return f"<Distribution(id={self.id}, task_id={self.task_id}, sub_user_id={self.sub_user_id})>"


class PublishAccount(Base):
    """
    发布账号表

    创作者配置的自媒体平台账号。
    """

    __tablename__ = "publish_account"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    sub_user_id = Column(
        BigInteger, ForeignKey("sub_user.id"), nullable=False, comment="创作者ID"
    )
    platform = Column(String(100), nullable=False, comment="平台名称")
    account_name = Column(String(255), nullable=False, comment="账号名称")
    account_id = Column(String(255), nullable=True, comment="账号ID")
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

    # 关联
    sub_user = relationship(
        "SubUser", back_populates="publish_accounts", foreign_keys=[sub_user_id]
    )

    def __repr__(self):
        return f"<PublishAccount(id={self.id}, sub_user_id={self.sub_user_id}, platform={self.platform})>"
