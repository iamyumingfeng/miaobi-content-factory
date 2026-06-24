"""
用户标签模型 (user_tag.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserTag(Base):
    """
    用户标签表
    """
    __tablename__ = "user_tag"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="标签名称")
    tag_type = Column(
        Enum("operator_tag", "subuser_tag", name="user_tag_type_enum"),
        nullable=False,
        comment="标签类型：operator_tag（创作管理员标签）/ subuser_tag（创作者标签）"
    )
    description = Column(String(500), nullable=True, comment="描述")
    color = Column(String(20), nullable=True, comment="标签颜色")
    created_by = Column(BigInteger, nullable=False, comment="创建者用户ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    user_tag_rels = relationship("UserTagRel", back_populates="tag", foreign_keys="UserTagRel.tag_id")

    def __repr__(self):
        return f"<UserTag(id={self.id}, name={self.name}, tag_type={self.tag_type})>"


class UserTagRel(Base):
    """
    用户标签关联表
    """
    __tablename__ = "user_tag_rel"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    tag_id = Column(BigInteger, ForeignKey("user_tag.id"), nullable=False, comment="标签ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    tag = relationship("UserTag", back_populates="user_tag_rels", foreign_keys=[tag_id])

    def __repr__(self):
        return f"<UserTagRel(id={self.id}, user_id={self.user_id}, tag_id={self.tag_id})>"
