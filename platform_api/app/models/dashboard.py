"""
仪表盘数据模型 (dashboard.py)

包含仪表盘相关的所有数据模型。

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime

from app.core.database import Base


class DashboardAlertDismissal(Base):
    """
    仪表盘告警清除记录

    记录已清除的失败任务告警（按任务ID，不区分用户）。
    任何人清除某任务的告警后，所有用户都看不到该告警。
    """

    __tablename__ = "dashboard_alert_dismissal"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(
        BigInteger, nullable=False, unique=True, index=True, comment="任务ID"
    )
    dismissed_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="清除时间"
    )

    def __repr__(self):
        return f"<DashboardAlertDismissal(task_id={self.task_id})>"
