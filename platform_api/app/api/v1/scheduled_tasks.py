"""
定时任务 API 路由 (scheduled_tasks.py)

提供定时任务的 RESTful API 接口。

Author: Claude Code
Date: 2025
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.scheduled_task import ScheduledTask
from app.schemas import PaginatedResponse
from app.schemas.scheduled_task import (ScheduledTaskBrief,
                                        ScheduledTaskCreate,
                                        ScheduledTaskExecutionLog,
                                        ScheduledTaskResponse,
                                        ScheduledTaskUpdate)
from app.services.operation_log_service import (ACTION_CREATE, ACTION_DELETE,
                                                ACTION_TOGGLE, ACTION_UPDATE,
                                                MODULE_SCHEDULED_TASKS,
                                                OperationLogService)
from app.services.scheduled_task_service import ScheduledTaskService
from app.utils.deps import get_token_payload_required
from app.utils.response import ApiResponse, success_response

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 定时任务管理
# ============================================


@router.get("", response_model=ApiResponse[PaginatedResponse[ScheduledTaskBrief]])
async def list_scheduled_tasks(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(
        None, description="状态筛选：active / paused / disabled"
    ),
    task_type: Optional[str] = Query(
        None, description="任务类型筛选：custom / benchmark"
    ),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    operator_id: Optional[int] = Query(
        None, description="创作管理员ID（仅超级管理员使用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取定时任务列表

    - 创作管理员只能查看自己创建的任务
    - 超级管理员可以查看所有任务（可指定 operator_id 筛选）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 确定查询的 owner_operator_id
    if is_super_admin:
        # 超级管理员：可以指定 operator_id 筛选，也可以不指定（查看所有）
        owner_operator_id = operator_id  # None 表示查看所有
    else:
        # 创作管理员：只能查看自己的任务
        owner_operator_id = int(payload.get("sub"))

    tasks, total = await ScheduledTaskService.list_scheduled_tasks(
        db,
        owner_operator_id=owner_operator_id,
        page=page,
        limit=limit,
        status=status,
        task_type=task_type,
        keyword=keyword,
        is_active=is_active,
    )

    # 构建响应
    response_items = []
    for task in tasks:
        response_items.append(
            ScheduledTaskBrief(
                id=task.id,
                name=task.name,
                task_type=task.task_type,
                schedule_type=task.schedule_type,
                schedule_config_json=task.schedule_config_json,
                status=task.status,
                is_active=task.is_active,
                total_executions=task.total_executions,
                successful_executions=task.successful_executions,
                failed_executions=task.failed_executions,
                next_execution_at=task.next_execution_at,
                last_execution_at=task.last_execution_at,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
        )

    return success_response(
        data=PaginatedResponse(
            items=response_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total > 0 else 0,
        ),
        message="获取成功",
    )


@router.post("", response_model=ApiResponse[ScheduledTaskResponse])
async def create_scheduled_task(
    request: ScheduledTaskCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建定时任务

    - 仅创作管理员可新建定时任务
    """
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能新建定时任务，请切换为创作管理员操作",
        )

    owner_operator_id = int(payload.get("sub"))
    created_by = owner_operator_id

    logger.info(
        f"[API] 开始创建定时任务 | owner={owner_operator_id} | name={request.name} | "
        f"schedule_type={request.schedule_type}"
    )
    logger.info(
        f"[API] 创建请求数据 | sub_user_ids={request.sub_user_ids_json} | "
        f"model_selection_mode={request.model_selection_mode} | "
        f"model_platform={request.model_platform} | model_id={request.model_id} | "
        f"image_model_platform={request.image_model_platform} | image_model_id={request.image_model_id} | "
        f"benchmark_text_enabled={request.benchmark_text_enabled} | "
        f"benchmark_image_enabled={request.benchmark_image_enabled} | "
        f"task_type={request.task_type}"
    )

    # 创建任务
    task = await ScheduledTaskService.create_scheduled_task(
        db,
        request,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
    )

    # 记录操作日志
    await OperationLogService.create(
        db,
        action=ACTION_CREATE,
        module=MODULE_SCHEDULED_TASKS,
        description=f"创建定时任务：{task.name}",
        table_name="scheduled_task",
        record_id=task.id,
        new_value={
            "name": task.name,
            "task_type": task.task_type,
            "schedule_type": task.schedule_type,
            "schedule_config": task.schedule_config_json,
            "is_active": task.is_active,
            "sub_user_ids": task.sub_user_ids_json,
            "template_ids": task.template_ids_json,
            "model_selection_mode": task.model_selection_mode,
            "model_platform": task.model_platform,
            "model_id": task.model_id,
        },
        user_id=owner_operator_id,
        user_type="operator",
    )

    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(db, task)

    logger.info(f"[API] 创建定时任务成功 | id={task.id} | name={task.name}")

    return success_response(
        data=ScheduledTaskResponse(**response_data), message="创建成功"
    )


@router.get("/{task_id}", response_model=ApiResponse[ScheduledTaskResponse])
async def get_scheduled_task(
    task_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取定时任务详情
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 超级管理员可以查看所有任务
    if is_super_admin:
        task = await db.get(ScheduledTask, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在"
            )
    else:
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
            )

    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(db, task)

    return success_response(
        data=ScheduledTaskResponse(**response_data), message="获取成功"
    )


@router.put("/{task_id}", response_model=ApiResponse[ScheduledTaskResponse])
async def update_scheduled_task(
    task_id: int,
    request: ScheduledTaskUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新定时任务
    """
    owner_operator_id = int(payload.get("sub"))

    logger.info(f"[API] 开始更新定时任务 | id={task_id} | owner={owner_operator_id}")

    # 获取旧任务数据（用于记录操作日志）
    old_task = await ScheduledTaskService.get_scheduled_task(
        db, task_id, owner_operator_id
    )
    if not old_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 记录旧值
    old_value = {
        "name": old_task.name,
        "task_type": old_task.task_type,
        "schedule_type": old_task.schedule_type,
        "schedule_config": old_task.schedule_config_json,
        "is_active": old_task.is_active,
        "status": old_task.status,
        "sub_user_ids": old_task.sub_user_ids_json,
        "template_ids": old_task.template_ids_json,
        "model_selection_mode": old_task.model_selection_mode,
        "model_platform": old_task.model_platform,
        "model_id": old_task.model_id,
    }

    # 更新任务
    task = await ScheduledTaskService.update_scheduled_task(
        db,
        task_id,
        request,
        owner_operator_id,
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 记录新值
    new_value = {
        "name": task.name,
        "task_type": task.task_type,
        "schedule_type": task.schedule_type,
        "schedule_config": task.schedule_config_json,
        "is_active": task.is_active,
        "status": task.status,
        "sub_user_ids": task.sub_user_ids_json,
        "template_ids": task.template_ids_json,
        "model_selection_mode": task.model_selection_mode,
        "model_platform": task.model_platform,
        "model_id": task.model_id,
    }

    # 记录操作日志
    await OperationLogService.create(
        db,
        action=ACTION_UPDATE,
        module=MODULE_SCHEDULED_TASKS,
        description=f"更新定时任务：{task.name}",
        table_name="scheduled_task",
        record_id=task.id,
        old_value=old_value,
        new_value=new_value,
        user_id=owner_operator_id,
        user_type="operator",
    )

    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(db, task)

    logger.info(f"[API] 更新定时任务成功 | id={task.id} | name={task.name}")

    return success_response(
        data=ScheduledTaskResponse(**response_data), message="更新成功"
    )


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除定时任务

    - 超级管理员可删除任何定时任务
    - 创作管理员只能删除自己的定时任务
    """
    user_type = payload.get("user_type")
    owner_operator_id = int(payload.get("sub"))

    logger.info(
        f"[API] 开始删除定时任务 | id={task_id} | user_type={user_type} | owner={owner_operator_id}"
    )

    # 获取任务信息（用于记录操作日志）
    if user_type == "super_admin":
        task = await db.get(ScheduledTask, task_id)
    else:
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 记录被删除的任务信息
    deleted_task_info = {
        "name": task.name,
        "task_type": task.task_type,
        "schedule_type": task.schedule_type,
        "schedule_config": task.schedule_config_json,
        "status": task.status,
        "is_active": task.is_active,
        "total_executions": task.total_executions,
        "successful_executions": task.successful_executions,
        "failed_executions": task.failed_executions,
    }

    # 超级管理员可以删除任何任务，创作管理员只能删除自己的任务
    if user_type == "super_admin":
        # 超级管理员：不限制 owner_operator_id
        success = await ScheduledTaskService.delete_scheduled_task(
            db,
            task_id,
            owner_operator_id=None,  # 超级管理员不限制所属者
        )
    else:
        # 创作管理员：只能删除自己的任务
        success = await ScheduledTaskService.delete_scheduled_task(
            db,
            task_id,
            owner_operator_id,
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 记录操作日志
    await OperationLogService.create(
        db,
        action=ACTION_DELETE,
        module=MODULE_SCHEDULED_TASKS,
        description=f"删除定时任务：{deleted_task_info['name']}",
        table_name="scheduled_task",
        record_id=task_id,
        old_value=deleted_task_info,
        user_id=owner_operator_id,
        user_type=user_type,
    )

    logger.info(f"[API] 删除定时任务成功 | id={task_id}")

    return success_response(message="删除成功")


@router.post("/{task_id}/toggle", response_model=ApiResponse[ScheduledTaskResponse])
async def toggle_scheduled_task(
    task_id: int,
    is_active: bool = Query(..., description="是否启用"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    启用/禁用定时任务
    """
    user_type = payload.get("user_type")
    owner_operator_id = int(payload.get("sub"))

    logger.info(
        f"[API] {'启用' if is_active else '禁用'}定时任务 | id={task_id} | owner={owner_operator_id}"
    )

    # 获取旧任务数据（用于记录操作日志）
    old_task = await ScheduledTaskService.get_scheduled_task(
        db, task_id, owner_operator_id
    )
    if not old_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 切换状态
    task = await ScheduledTaskService.toggle_scheduled_task(
        db,
        task_id,
        owner_operator_id,
        is_active,
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 记录操作日志
    await OperationLogService.create(
        db,
        action=ACTION_TOGGLE,
        module=MODULE_SCHEDULED_TASKS,
        description=f"{'启用' if is_active else '禁用'}定时任务：{task.name}",
        table_name="scheduled_task",
        record_id=task.id,
        old_value={"is_active": old_task.is_active, "status": old_task.status},
        new_value={"is_active": task.is_active, "status": task.status},
        extra_data={"toggle_to": "启用" if is_active else "禁用"},
        user_id=owner_operator_id,
        user_type=user_type,
    )

    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(db, task)

    return success_response(
        data=ScheduledTaskResponse(**response_data),
        message=f"已{'启用' if is_active else '禁用'}",
    )


@router.post("/{task_id}/execute", response_model=ApiResponse[dict])
async def execute_scheduled_task_now(
    task_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    立即执行定时任务（测试用）
    """
    owner_operator_id = int(payload.get("sub"))

    logger.info(f"[API] 立即执行定时任务 | id={task_id} | owner={owner_operator_id}")

    # 验证权限
    task = await ScheduledTaskService.get_scheduled_task(db, task_id, owner_operator_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
        )

    # 执行任务
    success, generation_task_id, error_message = (
        await ScheduledTaskService.execute_scheduled_task(db, task_id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行失败：{error_message}",
        )

    logger.info(
        f"[API] 立即执行定时任务成功 | scheduled_task_id={task_id} | "
        f"generation_task_id={generation_task_id}"
    )

    return success_response(
        data={
            "generation_task_id": generation_task_id,
            "message": "任务已创建，请查看生成任务列表",
        },
        message="执行成功",
    )


# ============================================
# 执行历史
# ============================================


@router.get(
    "/{task_id}/executions",
    response_model=ApiResponse[PaginatedResponse[ScheduledTaskExecutionLog]],
)
async def get_task_executions(
    task_id: int,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取定时任务执行历史

    - 创作管理员只能查看自己任务的执行历史
    - 超级管理员可以查看所有任务的执行历史
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 验证任务存在和权限
    if is_super_admin:
        task = await db.get(ScheduledTask, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在"
            )
        # 超级管理员使用任务的 owner_operator_id
        owner_operator_id = task.owner_operator_id
    else:
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在或无权访问"
            )

    logger.info(
        f"[API] 获取定时任务执行历史 | task_id={task_id} | "
        f"owner={owner_operator_id} | page={page}"
    )

    # 获取执行历史
    executions, total = await ScheduledTaskService.get_task_executions(
        db, task_id, owner_operator_id, page, limit
    )

    # 构建响应
    response_items = [
        ScheduledTaskExecutionLog(
            id=exec.id,
            scheduled_task_id=exec.scheduled_task_id,
            generation_task_id=exec.generation_task_id,
            execution_type=exec.execution_type,
            scheduled_at=exec.scheduled_at,
            started_at=exec.started_at,
            completed_at=exec.completed_at,
            execution_time=exec.execution_time,
            status=exec.status,
            error_message=exec.error_message,
            total_items=exec.total_items,
            success_items=exec.success_items,
            failed_items=exec.failed_items,
            created_at=exec.created_at,
        )
        for exec in executions
    ]

    logger.info(
        f"[API] 获取执行历史成功 | task_id={task_id} | "
        f"total={total} | returned={len(response_items)}"
    )

    return success_response(
        data=PaginatedResponse(
            items=response_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total > 0 else 0,
        ),
        message="获取成功",
    )
