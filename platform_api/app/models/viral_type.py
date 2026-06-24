"""
爆款类型模型

存储爆款内容类型的配置信息。
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ViralType(Base):
    """
    爆款类型配置表

    存储平台级别的爆款内容类型配置。
    仅超级管理员可管理，创作管理员只读访问。
    """
    __tablename__ = "viral_type"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 类型值（唯一标识）
    value = Column(String(50), unique=True, nullable=False, comment="类型值，如 seeding, review")

    # 显示标签
    label = Column(String(100), nullable=False, comment="显示标签，如 种草安利型")

    # 描述
    description = Column(Text, nullable=True, comment="类型描述")

    # 关键词（JSON 数组字符串）
    keywords = Column(Text, nullable=True, comment="关键词 JSON 数组")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序顺序")

    # 状态
    status = Column(String(20), default='enabled', comment="状态: enabled/disabled")

    # 是否系统预置
    is_system = Column(Boolean, default=False, comment="是否系统预置")

    def __repr__(self):
        return f"<ViralType(id={self.id}, value='{self.value}', label='{self.label}')>"
