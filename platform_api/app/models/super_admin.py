"""
超级管理员模型 (super_admin.py)

Author: Claude Code
Date: 2025
"""

from sqlalchemy.orm import relationship
from app.models.user_base import UserBase


class SuperAdmin(UserBase):
    """
    超级管理员表

    按角色分表，物理隔离，从数据库层面防止越权访问。
    继承 UserBase 确保与其他用户表结构一致。
    """
    __tablename__ = "super_admin"

    # 关联关系
    operation_logs = relationship("OperationLog", back_populates="super_admin", foreign_keys="OperationLog.super_admin_id")
    model_configs = relationship("ModelConfig", back_populates="creator", foreign_keys="ModelConfig.created_by")
