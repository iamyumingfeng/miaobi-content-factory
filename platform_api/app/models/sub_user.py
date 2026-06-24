"""
创作者模型 (sub_user.py)

Author: Claude Code
Date: 2025
"""

from sqlalchemy.orm import relationship
from app.models.user_base import UserBase


class SubUser(UserBase):
    """
    创作者表

    按角色分表,物理隔离,从数据库层面防止越权访问。
    继承 UserBase 确保与其他用户表结构一致。
    """
    __tablename__ = "sub_user"

    # 关联关系
    generation_task_subusers = relationship("GenerationTaskSubuser", back_populates="sub_user", foreign_keys="GenerationTaskSubuser.sub_user_id")
    generation_items = relationship("GenerationItem", back_populates="sub_user", foreign_keys="GenerationItem.sub_user_id")
    distributions = relationship("Distribution", back_populates="sub_user", foreign_keys="Distribution.sub_user_id")
    publish_accounts = relationship("PublishAccount", back_populates="sub_user", foreign_keys="PublishAccount.sub_user_id")
    operation_logs = relationship("OperationLog", back_populates="sub_user", foreign_keys="OperationLog.sub_user_id")
