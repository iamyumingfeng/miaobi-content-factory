"""
系统管理模型 (system.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Boolean, Column, DateTime, Enum,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import relationship

from app.core.database import Base


class OperationLog(Base):
    """
    操作日志表
    """

    __tablename__ = "operation_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    super_admin_id = Column(
        BigInteger, ForeignKey("super_admin.id"), nullable=True, comment="超级管理员ID"
    )
    operator_id = Column(
        BigInteger, ForeignKey("operator.id"), nullable=True, comment="创作管理员ID"
    )
    sub_user_id = Column(
        BigInteger, ForeignKey("sub_user.id"), nullable=True, comment="创作者ID"
    )
    module = Column(
        String(50),
        nullable=True,
        comment="模块：users/templates/materials/generation/distribution/system",
    )
    action = Column(
        String(100),
        nullable=False,
        comment="操作类型：create / update / delete / distribute / publish / login / logout / cancel / retry",
    )
    description = Column(
        String(500), nullable=True, comment="操作描述，如：创建素材：素材标题"
    )
    table_name = Column(String(100), nullable=True, comment="操作的数据表")
    record_id = Column(BigInteger, nullable=True, comment="操作的记录ID")
    old_value_json = Column(JSON, nullable=True, comment="操作前的旧值（JSON格式）")
    new_value_json = Column(JSON, nullable=True, comment="操作后的新值（JSON格式）")
    extra_data_json = Column(
        JSON, nullable=True, comment="额外参数（JSON格式），如标签列表、操作条件等"
    )
    ip_address = Column(String(50), nullable=True, comment="操作IP地址")
    user_agent = Column(String(500), nullable=True, comment="浏览器/客户端信息")
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="操作时间"
    )

    # 关联
    super_admin = relationship(
        "SuperAdmin", back_populates="operation_logs", foreign_keys=[super_admin_id]
    )
    operator = relationship(
        "Operator", back_populates="operation_logs", foreign_keys=[operator_id]
    )
    sub_user = relationship(
        "SubUser", back_populates="operation_logs", foreign_keys=[sub_user_id]
    )

    def __repr__(self):
        return f"<OperationLog(id={self.id}, action={self.action})>"


class CleanupRule(Base):
    """
    过期清理规则表
    """

    __tablename__ = "cleanup_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    rule_name = Column(String(255), nullable=False, comment="规则名称")
    content_type = Column(String(100), nullable=True, comment="内容类型")
    retention_period = Column(
        Enum("month", "quarter", "year", name="retention_period_enum"),
        nullable=False,
        default="quarter",
        comment="保留期：month / quarter / year",
    )
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    last_executed_at = Column(DateTime, nullable=True, comment="上次执行时间")
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

    def __repr__(self):
        return f"<CleanupRule(id={self.id}, rule_name={self.rule_name})>"


class ModelConfig(Base):
    """
    模型配置表
    """

    __tablename__ = "model_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    platform = Column(
        String(100),
        nullable=False,
        comment="平台：bailian / lingyaai/ zhipu / volcano / jimeng / kling 等",
    )
    model_id = Column(String(255), nullable=False, comment="模型ID")
    model_name = Column(String(255), nullable=False, comment="模型名称")
    model_type = Column(
        Enum("llm", "image", "video", "embedding", name="model_type_enum"),
        nullable=False,
        comment="模型类型：llm / image / video / embedding",
    )
    base_url = Column(String(500), nullable=True, comment="【大语言模型专属】Base URL")
    api_endpoint = Column(String(500), nullable=True, comment="API端点")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认")
    max_concurrency = Column(Integer, nullable=False, default=5, comment="最大并发数")
    config_json = Column(JSON, nullable=True, comment="配置JSON（包含API Key等）")
    status = Column(
        Enum("active", "inactive", name="model_config_status_enum"),
        nullable=False,
        default="active",
        comment="状态：active / inactive",
    )
    is_system = Column(
        Boolean, nullable=False, default=False, comment="是否系统预置模型"
    )
    created_by = Column(
        BigInteger,
        ForeignKey("super_admin.id"),
        nullable=True,
        comment="创建者超级管理员ID",
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

    # 关联
    creator = relationship(
        "SuperAdmin", back_populates="model_configs", foreign_keys=[created_by]
    )

    def __repr__(self):
        return f"<ModelConfig(id={self.id}, platform={self.platform}, model_id={self.model_id})>"
