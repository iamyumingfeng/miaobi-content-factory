"""
定时任务执行历史模型 (scheduled_task_execution.py)

记录每次定时任务的执行历史，包括执行时间、状态、错误信息等。

Author: Claude Code
Date: 2026-05-15
"""

from datetime import datetime

from sqlalchemy import (BigInteger, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScheduledTaskExecution(Base):
    """
    定时任务执行历史表

    记录每次定时任务的执行详情，用于审计和故障排查。
    """

    __tablename__ = "scheduled_task_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    scheduled_task_id = Column(
        BigInteger,
        ForeignKey("scheduled_task.id"),
        nullable=False,
        index=True,
        comment="定时任务ID",
    )
    generation_task_id = Column(
        BigInteger,
        ForeignKey("generation_task.id"),
        nullable=True,
        comment="生成的任务ID",
    )

    # ============================================
    # 执行类型
    # ============================================
    execution_type = Column(
        String(50),
        nullable=False,
        default="scheduled",
        comment="执行类型：scheduled(定时) / manual(手动)",
    )

    # ============================================
    # 执行时间线
    # ============================================
    scheduled_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="计划执行时间"
    )
    started_at = Column(DateTime, nullable=True, comment="实际开始执行时间")
    completed_at = Column(DateTime, nullable=True, comment="执行完成时间")

    # ============================================
    # 执行信息（兼容旧字段）
    # ============================================
    execution_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="执行时间（兼容字段，等价于 scheduled_at）",
    )
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        comment="执行状态：pending(排队中) / running(执行中) / completed(完成) / failed(失败) / partial(部分成功) / cancelled(已取消)",
    )
    error_message = Column(Text, nullable=True, comment="错误信息")

    # ============================================
    # 执行结果统计
    # ============================================
    total_items = Column(Integer, nullable=True, default=0, comment="总生成项数")
    success_items = Column(Integer, nullable=True, default=0, comment="成功项数")
    failed_items = Column(Integer, nullable=True, default=0, comment="失败项数")

    # ============================================
    # 执行详情（JSON 格式）
    # ============================================
    execution_details_json = Column(
        String(2000),
        nullable=True,
        comment="执行详情JSON（包含选中的模板、素材等信息）",
    )

    # ============================================
    # 时间戳
    # ============================================
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    # 关联关系
    scheduled_task = relationship("ScheduledTask", back_populates="executions")
    generation_task = relationship("GenerationTask")

    def __repr__(self):
        return f"<ScheduledTaskExecution(id={self.id}, scheduled_task_id={self.scheduled_task_id}, status={self.status})>"
