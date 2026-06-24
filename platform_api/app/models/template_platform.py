"""
模板平台模型 (template_platform.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Column, DateTime, ForeignKey, Index,
                        Integer, String, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TemplatePlatform(Base):
    """
    模板平台表 - 模板库独立平台（3层结构的顶层）

    TemplatePlatform -> TemplateCategory -> TemplateTag -> Template
    """

    __tablename__ = "template_platform"
    __table_args__ = (
        UniqueConstraint(
            "owner_operator_id", "name", name="uq_template_platform_owner_name"
        ),
        Index("ix_template_platform_owner", "owner_operator_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="平台名称")
    description = Column(String(500), nullable=True, comment="平台描述")
    color = Column(String(20), nullable=True, comment="平台颜色")
    platform_code = Column(String(50), nullable=True, comment="平台代码（如 xhs, dy）")
    rules_config_json = Column(JSON, nullable=True, comment="平台规则配置JSON")
    config_json = Column(JSON, nullable=True, comment="平台配置JSON（预留扩展）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重")
    created_by = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=True,
        comment="创建者创作管理员ID",
    )
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=False,
        index=True,
        comment="所属创作管理员ID（数据隔离用）",
    )
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

    # 关联关系
    categories = relationship(
        "TemplateCategory",
        back_populates="platform",
        cascade="all, delete-orphan",
        foreign_keys="TemplateCategory.template_platform_id",
    )

    def __repr__(self):
        return f"<TemplatePlatform(id={self.id}, name={self.name})>"
