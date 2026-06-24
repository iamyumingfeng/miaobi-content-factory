"""
AIGC看板 Schema (dashboard.py)

包含AIGC看板相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseSchema


class DashboardStatsResponse(BaseModel):
    """
    AIGC看板统计数据响应
    """
    total_sub_users: int = Field(..., description="总创作者数")
    today_generated: int = Field(..., description="生成内容数")
    pending_publish: int = Field(..., description="待发出内容数")
    published: int = Field(..., description="已发出内容数")
    start_date: Optional[str] = Field(default=None, description="统计开始日期（YYYY-MM-DD）")
    end_date: Optional[str] = Field(default=None, description="统计结束日期（YYYY-MM-DD）")


class TrendDataPoint(BaseModel):
    """
    趋势数据点
    """
    date: str = Field(..., description="日期 YYYY-MM-DD")
    generated: int = Field(..., description="生成数量")
    distributed: int = Field(..., description="分发数量")
    published: int = Field(..., description="发布数量")


class DashboardTrendResponse(BaseModel):
    """
    AIGC看板趋势数据响应
    """
    data: List[TrendDataPoint] = Field(..., description="趋势数据点列表")


class RecentTaskItem(BaseModel):
    """
    最近任务项
    """
    id: int = Field(..., description="任务ID")
    name: Optional[str] = Field(default=None, description="任务名称")
    status: str = Field(..., description="任务状态")
    total_count: int = Field(..., description="总数")
    queued_count: int = Field(..., description="排队中数")
    generating_count: int = Field(..., description="生成中数")
    completed_count: int = Field(0, description="已完成数")
    failed_count: int = Field(..., description="失败数")
    paused_count: int = Field(0, description="已暂停数")
    pending_publish_count: int = Field(..., description="待发布数")
    published_count: int = Field(..., description="已发布数")
    owner_admin_id: Optional[int] = Field(default=None, description="所属创作管理员ID")
    owner_admin_name: Optional[str] = Field(default=None, description="所属创作管理员名称")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最近更新时间")


class DashboardRecentTasksResponse(BaseModel):
    """
    AIGC看板最近任务响应
    """
    tasks: List[RecentTaskItem] = Field(..., description="最近任务列表")
    total: int = Field(..., description="总数量")


class FailedTaskItem(BaseModel):
    """
    失败任务告警项
    """
    id: int = Field(..., description="任务ID")
    name: Optional[str] = Field(default=None, description="任务名称")
    failed_count: int = Field(..., description="失败数量")
    error: str = Field(..., description="错误信息摘要")
    owner_admin_id: Optional[int] = Field(default=None, description="所属创作管理员ID")
    owner_admin_name: Optional[str] = Field(default=None, description="所属创作管理员名称")
    latest_failed_at: Optional[datetime] = Field(default=None, description="最近失败时间")


class DashboardFailedTasksResponse(BaseModel):
    """
    AIGC看板失败任务告警响应
    """
    tasks: List[FailedTaskItem] = Field(..., description="失败任务列表")


class DismissAlertRequest(BaseModel):
    """
    清除单条告警请求
    """
    task_id: int = Field(..., description="任务ID")


class OperatorOption(BaseModel):
    """
    创作管理员选项（用于筛选下拉框）
    """
    id: int = Field(..., description="管理员ID")
    name: str = Field(..., description="管理员名称")


class DashboardResponse(BaseModel):
    """
    AIGC看板完整响应
    """
    stats: DashboardStatsResponse = Field(..., description="统计数据")
    recent_tasks: List[RecentTaskItem] = Field(..., description="最近任务")
    failed_tasks: List[FailedTaskItem] = Field(..., description="失败任务告警")