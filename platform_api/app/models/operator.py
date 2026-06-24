"""
创作管理员模型 (operator.py)

Author: Claude Code
Date: 2025
"""

from sqlalchemy.orm import relationship
from app.models.user_base import UserBase


class Operator(UserBase):
    """
    创作管理员表

    按角色分表，物理隔离，从数据库层面防止越权访问。
    继承 UserBase 确保与其他用户表结构一致。
    """
    __tablename__ = "operator"

    # 关联关系
    generation_tasks = relationship("GenerationTask", back_populates="owner_operator", foreign_keys="GenerationTask.owner_operator_id")
    generation_items = relationship("GenerationItem", back_populates="owner_operator", foreign_keys="GenerationItem.owner_operator_id")
    operation_logs = relationship("OperationLog", back_populates="operator", foreign_keys="OperationLog.operator_id")
    scheduled_tasks = relationship("ScheduledTask", foreign_keys="ScheduledTask.owner_operator_id", back_populates="owner_operator")
