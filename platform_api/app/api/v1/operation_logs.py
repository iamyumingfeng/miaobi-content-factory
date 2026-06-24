"""
操作日志 API 路由 (operation_logs.py)

提供操作日志的记录和查询接口。

Author: Claude Code
Date: 2026
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any, Dict
from datetime import datetime

from app.core.database import get_async_db
from app.utils.response import success_response, ApiResponse
from app.schemas import PaginatedResponse
from app.utils.deps import get_optional_current_user, get_current_super_admin
from app.models import SuperAdmin, Operator, SubUser
from typing import Tuple, Union
from app.services.operation_log_service import (
    OperationLogService,
    MODULE_USERS,
    MODULE_TEMPLATES,
    MODULE_MATERIALS,
    MODULE_GENERATION,
    MODULE_DISTRIBUTION,
    MODULE_SYSTEM,
    MODULE_SCHEDULED_TASKS,
)

router = APIRouter()


class OperationLogCreateRequest:
    """操作日志创建请求"""
    def __init__(
        self,
        module: Optional[str] = None,
        action: str = ...,
        description: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        self.module = module
        self.action = action
        self.description = description
        self.table_name = table_name
        self.record_id = record_id
        self.old_value = old_value
        self.new_value = new_value
        self.extra_data = extra_data


class OperationLogResponse:
    """操作日志响应"""
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.super_admin_id = data.get("super_admin_id")
        self.operator_id = data.get("operator_id")
        self.sub_user_id = data.get("sub_user_id")
        self.module = data.get("module")
        self.action = data.get("action")
        self.description = data.get("description")
        self.table_name = data.get("table_name")
        self.record_id = data.get("record_id")
        self.old_value_json = data.get("old_value_json")
        self.new_value_json = data.get("new_value_json")
        self.extra_data_json = data.get("extra_data_json")
        self.ip_address = data.get("ip_address")
        self.user_agent = data.get("user_agent")
        self.created_at = data.get("created_at")


def _extract_client_info(request: Request) -> tuple:
    """从请求中提取客户端信息"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", None)
    return ip_address, user_agent


@router.post("", response_model=ApiResponse[dict])
async def create_operation_log(
    request_body: dict,
    request: Request,
    user_info: Optional[Tuple[Union[SuperAdmin, Operator, SubUser], str]] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建操作日志

    - 任何登录用户都可以记录操作日志
    - 自动从请求上下文获取用户身份和客户端信息
    """
    ip_address, user_agent = _extract_client_info(request)

    # 从用户信息元组中提取 user_id 和 user_type
    user_id = None
    user_type = None
    if user_info:
        user_obj, user_type = user_info
        user_id = getattr(user_obj, 'id', None)

    log = await OperationLogService.create(
        db=db,
        action=request_body.get("action"),
        module=request_body.get("module"),
        description=request_body.get("description"),
        table_name=request_body.get("table_name"),
        record_id=request_body.get("record_id"),
        old_value=request_body.get("old_value"),
        new_value=request_body.get("new_value"),
        extra_data=request_body.get("extra_data"),
        user_id=user_id,
        user_type=user_type,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await db.commit()

    return success_response(
        data={"id": log.id, "created_at": log.created_at.isoformat() if log.created_at else None},
        message="日志记录成功"
    )


@router.get("", response_model=ApiResponse[PaginatedResponse[dict]])
async def list_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    module: Optional[str] = Query(None, description="模块筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    user_type: Optional[str] = Query(None, description="用户类型筛选"),
    table_name: Optional[str] = Query(None, description="数据表筛选"),
    record_id: Optional[int] = Query(None, description="记录ID筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间筛选"),
    end_date: Optional[datetime] = Query(None, description="结束时间筛选"),
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    查询操作日志列表（仅超级管理员可访问）

    支持分页和条件筛选
    """
    logs, total = await OperationLogService.list_logs(
        db=db,
        page=page,
        limit=limit,
        module=module,
        action=action,
        user_id=user_id,
        user_type=user_type,
        table_name=table_name,
        record_id=record_id,
        start_date=start_date,
        end_date=end_date,
    )

    # 收集所有需要查询的用户ID
    operator_ids = list(set(log.operator_id for log in logs if log.operator_id))
    sub_user_ids = list(set(log.sub_user_id for log in logs if log.sub_user_id))

    # 批量查询操作者昵称
    operator_names = {}
    sub_user_names = {}

    if operator_ids:
        from sqlalchemy import select
        op_result = await db.execute(
            select(Operator.id, Operator.nickname).where(Operator.id.in_(operator_ids))
        )
        operator_names = {row[0]: row[1] for row in op_result.fetchall()}

    if sub_user_ids:
        from sqlalchemy import select
        sub_result = await db.execute(
            select(SubUser.id, SubUser.nickname).where(SubUser.id.in_(sub_user_ids))
        )
        sub_user_names = {row[0]: row[1] for row in sub_result.fetchall()}

    # 转换为响应格式
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "super_admin_id": log.super_admin_id,
            "operator_id": log.operator_id,
            "operator_name": operator_names.get(log.operator_id) if log.operator_id else None,
            "sub_user_id": log.sub_user_id,
            "sub_user_name": sub_user_names.get(log.sub_user_id) if log.sub_user_id else None,
            "module": log.module,
            "action": log.action,
            "description": log.description,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "old_value_json": log.old_value_json,
            "new_value_json": log.new_value_json,
            "extra_data_json": log.extra_data_json,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return success_response(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total > 0 else 0,
        ),
        message="获取成功"
    )


@router.get("/{log_id}", response_model=ApiResponse[dict])
async def get_operation_log(
    log_id: int,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取操作日志详情（仅超级管理员可访问）
    """
    log = await OperationLogService.get_log_by_id(db, log_id)
    if not log:
        return success_response(data=None, message="日志不存在")

    # 查询操作者昵称
    operator_name = None
    sub_user_name = None

    if log.operator_id:
        from sqlalchemy import select
        op_result = await db.execute(
            select(Operator.nickname).where(Operator.id == log.operator_id)
        )
        operator_name = op_result.scalar_one_or_none()

    if log.sub_user_id:
        from sqlalchemy import select
        sub_result = await db.execute(
            select(SubUser.nickname).where(SubUser.id == log.sub_user_id)
        )
        sub_user_name = sub_result.scalar_one_or_none()

    return success_response(
        data={
            "id": log.id,
            "super_admin_id": log.super_admin_id,
            "operator_id": log.operator_id,
            "operator_name": operator_name,
            "sub_user_id": log.sub_user_id,
            "sub_user_name": sub_user_name,
            "module": log.module,
            "action": log.action,
            "description": log.description,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "old_value_json": log.old_value_json,
            "new_value_json": log.new_value_json,
            "extra_data_json": log.extra_data_json,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        },
        message="获取成功"
    )
