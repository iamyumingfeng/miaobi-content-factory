"""
AIGC看板 API (dashboard.py)

提供AIGC看板相关的 API 端点。

Author: Claude Code
Date: 2025
"""

import logging
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.utils.deps import get_token_payload_required
from app.utils.response import success_response, ApiResponse
from app.schemas.dashboard import (
    DashboardStatsResponse,
    DashboardTrendResponse,
    DashboardRecentTasksResponse,
    DashboardFailedTasksResponse,
    RecentTaskItem,
    FailedTaskItem,
    TrendDataPoint,
    DismissAlertRequest,
    OperatorOption,
)
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_status_text(status: str) -> str:
    """将状态码转换为中文状态文本"""
    status_map = {
        "pending": "排队中",
        "processing": "生成中",
        "completed": "已完成",
        "failed": "失败",
        "cancelled": "已取消",
    }
    return status_map.get(status, status)


@router.get("/stats", response_model=ApiResponse[DashboardStatsResponse])
async def get_dashboard_stats(
    start_date: Optional[str] = Query(None, description="统计开始日期（YYYY-MM-DD），默认当天"),
    end_date: Optional[str] = Query(None, description="统计结束日期（YYYY-MM-DD），默认当天"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（仅超级管理员）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取AIGC看板统计数据

    返回总创作者数、生成数、待发布数、已发布数

    - start_date: 统计开始日期（YYYY-MM-DD），默认当天
    - end_date: 统计结束日期（YYYY-MM-DD），默认当天
    - operator_id: 筛选创作管理员ID（仅超级管理员可用）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    is_sub_user = user_type == "sub_user"
    user_id = int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选，创作管理员忽略该参数
    filter_operator_id = operator_id if is_super_admin and operator_id else None

    logger.info("[Dashboard API] get_dashboard_stats | user_type=%s | user_id=%s | start_date=%s | end_date=%s | filter_operator_id=%s",
               user_type, user_id, parsed_start_date, parsed_end_date, filter_operator_id)

    # 创作者需要按 sub_user_id 筛选，而不是 operator_id
    if is_sub_user:
        stats = await DashboardService.get_sub_user_stats(db, user_id, parsed_start_date, parsed_end_date)
    else:
        owner_operator_id = None if is_super_admin else user_id
        stats = await DashboardService.get_stats(db, owner_operator_id, parsed_start_date, parsed_end_date, filter_operator_id)

    return success_response(
        data=DashboardStatsResponse(**stats),
        message="获取成功"
    )


@router.get("/trend", response_model=ApiResponse[DashboardTrendResponse])
async def get_dashboard_trend(
    days: int = Query(7, ge=7, le=30, description="天数（7/15/30）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取AIGC看板趋势数据

    - days: 天数（默认7天，可选7/15/30）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[Dashboard API] get_dashboard_trend | user_type=%s | owner_operator_id=%s | days=%s", user_type, owner_operator_id, days)

    trend_data = await DashboardService.get_trend_data(db, owner_operator_id, days)

    return success_response(
        data=DashboardTrendResponse(
            data=[TrendDataPoint(**item) for item in trend_data]
        ),
        message="获取成功"
    )


@router.get("/recent-tasks", response_model=ApiResponse[DashboardRecentTasksResponse])
async def get_dashboard_recent_tasks(
    limit: int = Query(10, ge=1, le=50, description="每页数量限制"),
    page: int = Query(1, ge=1, description="页码"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（超级管理员使用）"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取最近的任务列表

    - limit: 每页数量限制（默认10）
    - page: 页码（从1开始）
    - operator_id: 筛选创作管理员ID（仅超级管理员可用）
    - start_date: 开始日期筛选（YYYY-MM-DD格式）
    - end_date: 结束日期筛选（YYYY-MM-DD格式）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选，创作管理员忽略该参数
    filter_operator_id = operator_id if is_super_admin and operator_id else None

    logger.info("[Dashboard API] get_dashboard_recent_tasks | user_type=%s | owner_operator_id=%s | limit=%s | page=%s | filter_operator=%s | start=%s | end=%s",
                user_type, owner_operator_id, limit, page, filter_operator_id, start_date, end_date)

    tasks, total = await DashboardService.get_recent_tasks(
        db, owner_operator_id, limit, page,
        filter_operator_id=filter_operator_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
    )

    recent_tasks = [
        RecentTaskItem(
            id=task.id,
            name=task.name or (task.material.title if task.material else f"任务#{task.id}"),
            status=_get_status_text(task.status),
            # 优先使用实时聚合计数（从 generation_item 表计算），回退到冗余字段
            total_count=getattr(task, '_live_counts', {}).get('total_count', task.total_count or 0),
            queued_count=getattr(task, '_live_counts', {}).get('queued_count', task.queued_count or 0),
            generating_count=getattr(task, '_live_counts', {}).get('generating_count', task.generating_count or 0),
            completed_count=getattr(task, '_live_counts', {}).get('completed_count', task.completed_count or 0),
            failed_count=getattr(task, '_live_counts', {}).get('failed_count', task.failed_count or 0),
            paused_count=getattr(task, '_live_counts', {}).get('paused_count', task.paused_count or 0),
            pending_publish_count=getattr(task, '_live_counts', {}).get('pending_publish_count', task.pending_publish_count or 0),
            published_count=getattr(task, '_live_counts', {}).get('published_count', task.published_count or 0),
            owner_admin_id=task.owner_operator.id if task.owner_operator else None,
            owner_admin_name=task.owner_operator.nickname if task.owner_operator else None,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]

    return success_response(
        data=DashboardRecentTasksResponse(tasks=recent_tasks, total=total),
        message="获取成功"
    )


@router.get("/failed-tasks", response_model=ApiResponse[DashboardFailedTasksResponse])
async def get_dashboard_failed_tasks(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取失败任务告警列表

    - limit: 返回数量限制（默认10）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[Dashboard API] get_dashboard_failed_tasks | user_type=%s | owner_operator_id=%s | limit=%s", user_type, owner_operator_id, limit)

    failed_tasks_data = await DashboardService.get_failed_tasks(db, owner_operator_id, limit)

    failed_tasks = [
        FailedTaskItem(
            id=item["id"],
            name=item["name"],
            failed_count=item["failed_count"],
            error=item["error"],
            owner_admin_id=item.get("owner_admin_id"),
            owner_admin_name=item.get("owner_admin_name"),
            latest_failed_at=item["latest_failed_at"],
        )
        for item in failed_tasks_data
    ]

    return success_response(
        data=DashboardFailedTasksResponse(tasks=failed_tasks),
        message="获取成功"
    )


@router.get("/operators", response_model=ApiResponse[List[OperatorOption]])
async def get_operator_list(
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创作管理员列表（仅超级管理员可用，用于筛选下拉框）

    返回所有创作管理员的ID和名称
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if not is_super_admin:
        return success_response(data=[], message="获取成功")

    operators = await DashboardService.get_operator_list(db)

    return success_response(
        data=[OperatorOption(id=op["id"], name=op["name"]) for op in operators],
        message="获取成功"
    )


@router.post("/dismiss-alert", response_model=ApiResponse[dict])
async def dismiss_alert(
    req: DismissAlertRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    清除单条告警（按任务ID，对所有用户生效）

    - task_id: 要清除的任务ID
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    logger.info("[Dashboard API] dismiss_alert | is_super_admin=%s | task_id=%s", is_super_admin, req.task_id)

    await DashboardService.dismiss_alert(db, req.task_id)

    return success_response(message="告警已清除")


@router.post("/dismiss-all-alerts", response_model=ApiResponse[dict])
async def dismiss_all_alerts(
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    清除所有告警（按任务ID，对所有用户生效）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[Dashboard API] dismiss_all_alerts | is_super_admin=%s | owner_operator_id=%s", is_super_admin, owner_operator_id)

    count = await DashboardService.dismiss_all_alerts(db, owner_operator_id)

    return success_response(message=f"已清除 {count} 条告警")
