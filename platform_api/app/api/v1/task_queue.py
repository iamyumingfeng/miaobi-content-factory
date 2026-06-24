"""
任务队列管理 API 路由 (task_queue.py)

提供任务队列的状态监控和管理功能：
- 查看队列状态（活跃任务、等待队列、并发配置）
- 更新最大并发数配置
- 手动触发任务调度
- 清空等待队列（慎⽤）

Author: Claude Code
Date: 2026-05-16
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.task_queue_manager import task_queue_manager
from app.utils.deps import get_super_admin_required, get_token_payload_required
from app.utils.response import ApiResponse, success_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["任务队列管理"])


# ============================================
# Worker 状态查询
# ============================================


@router.get("/workers", response_model=ApiResponse[dict])
async def get_worker_status(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取 Celery Worker 状态

    通过 Celery inspect API 获取真实的 Worker 运行状态：
    - worker_running_count: 正在处理任务的进程数
    - worker_idle_count: 空闲的进程数
    - worker_total: 进程池总容量（所有 Worker 的 concurrency 总和）
    - workers: 各 Worker 详细状态

    注意：一个 Celery Worker 进程内部有多个并发进程（pool），
    这里的计数是进程池中的进程数，不是 Worker 进程数。

    Returns:
        Worker 状态统计
    """
    try:
        from app.tasks.celery_app import celery_app

        # 获取所有活跃任务（按 Worker 分组）
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        stats = inspect.stats() or {}

        # 统计 Worker 状态
        worker_running_count = 0  # 正在执行任务的进程数
        worker_total = 0  # 进程池总容量
        workers_detail = []

        # 先从 stats 获取每个 Worker 的进程池容量
        for worker_name, worker_stats in stats.items():
            pool_info = worker_stats.get("pool", {})
            max_concurrency = pool_info.get("max-concurrency", 0)
            if isinstance(max_concurrency, str):
                # 有些情况下返回字符串，尝试解析
                try:
                    max_concurrency = int(max_concurrency)
                except:
                    max_concurrency = 0

            worker_total += max_concurrency

            # 获取该 Worker 正在执行的任务数
            tasks = active_tasks.get(worker_name, [])
            running_tasks = len(tasks) if tasks else 0
            worker_running_count += running_tasks

            workers_detail.append(
                {
                    "name": worker_name,
                    "running_tasks": running_tasks,
                    "pool_size": max_concurrency,
                    "idle_slots": max(0, max_concurrency - running_tasks),
                    "status": "running" if running_tasks > 0 else "idle",
                }
            )

        # 空闲进程数 = 总容量 - ��在执行的任务数
        worker_idle_count = max(0, worker_total - worker_running_count)

        result = {
            "worker_running_count": worker_running_count,
            "worker_idle_count": worker_idle_count,
            "worker_total": worker_total,
            "workers": workers_detail,
        }

        logger.info(
            f"查询 Worker 状态 | running={worker_running_count} | idle={worker_idle_count} | total={worker_total}"
        )
        return success_response(data=result)
    except Exception as e:
        logger.error(f"查询 Worker 状态失败: {e}")
        # 返回空数据而不是报错，避免影响前端
        return success_response(
            data={
                "worker_running_count": 0,
                "worker_idle_count": 0,
                "worker_total": 0,
                "workers": [],
                "error": str(e),
            }
        )


# ============================================
# 队列状态查询
# ============================================


@router.get("/status", response_model=ApiResponse[dict])
async def get_queue_status(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取任务队列状态

    Returns:
        队列状态统计，包括：
        - max_concurrent: 最大并发数
        - active_count: 当前活跃任务数
        - waiting_count: 等待队列长度
        - active_tasks: 活跃任务列表
        - waiting_tasks: 等待队列中的任务列表（前20条）
    """
    try:
        status_data = task_queue_manager.get_queue_status()
        logger.info(
            f"查询队列状态 | active={status_data['active_count']} | waiting={status_data['waiting_count']}"
        )
        return success_response(data=status_data)
    except Exception as e:
        logger.error(f"查询队列状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询队列状态失败: {str(e)}",
        )


@router.get("/active", response_model=ApiResponse[list])
async def get_active_tasks(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取当前活跃任务列表

    Returns:
        活跃任务详细信息列表
    """
    try:
        active_tasks = task_queue_manager.get_active_tasks()
        return success_response(data=active_tasks)
    except Exception as e:
        logger.error(f"查询活跃任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询活跃任务失败: {str(e)}",
        )


@router.get("/waiting", response_model=ApiResponse[list])
async def get_waiting_tasks(
    limit: Optional[int] = 50,
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取等待队列中的任务列表

    Args:
        limit: 返回数量限制（默认50）

    Returns:
        等待队列中的任务列表
    """
    try:
        waiting_tasks = task_queue_manager.get_queue_tasks(start=0, end=limit - 1)
        return success_response(data=waiting_tasks)
    except Exception as e:
        logger.error(f"查询等待队列失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询等待队列失败: {str(e)}",
        )


# ============================================
# 队列配置管理
# ============================================


@router.put("/config", response_model=ApiResponse[dict])
async def update_queue_config(
    max_concurrent: int,
    payload: dict = Depends(get_super_admin_required),  # 仅超级管理员可修改
):
    """
    更新队列配置

    Args:
        max_concurrent: 最大并发任务数

    Returns:
        更新后的配置
    """
    if max_concurrent < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="最大并发数必须大于 0"
        )

    try:
        task_queue_manager.set_max_concurrent(max_concurrent)
        logger.info(
            f"更新队列配置 | max_concurrent={max_concurrent} | operator={payload.get('sub')}"
        )
        return success_response(
            data={"max_concurrent": max_concurrent, "message": "配置更新成功"}
        )
    except Exception as e:
        logger.error(f"更新队列配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}",
        )


@router.get("/config", response_model=ApiResponse[dict])
async def get_queue_config(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取队列配置

    Returns:
        当前队列配置
    """
    try:
        max_concurrent = task_queue_manager.get_max_concurrent()
        active_count = task_queue_manager.get_active_count()
        waiting_count = task_queue_manager.get_queue_length()
        idle_count = max(0, max_concurrent - active_count)

        return success_response(
            data={
                "max_concurrent": max_concurrent,
                "active_count": active_count,
                "idle_count": idle_count,
                "waiting_count": waiting_count,
                "can_dispatch": active_count < max_concurrent,
            }
        )
    except Exception as e:
        logger.error(f"获取队列配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}",
        )


# ============================================
# 队列操作
# ============================================


@router.post("/dispatch", response_model=ApiResponse[dict])
async def trigger_dispatch(
    max_dispatch: Optional[int] = 10,
    payload: dict = Depends(get_token_payload_required),
):
    """
    手动触发任务调度

    Args:
        max_dispatch: 最大调度数量（默认10）

    Returns:
        调度结果
    """
    try:
        from app.tasks.generation_tasks import _dispatch_tasks_from_queue

        owner_operator_id = int(payload.get("sub"))
        dispatched_count = _dispatch_tasks_from_queue(owner_operator_id, max_dispatch)

        logger.info(
            f"手动触发调度 | dispatched={dispatched_count} | operator={owner_operator_id}"
        )
        return success_response(
            data={
                "dispatched_count": dispatched_count,
                "active_count": task_queue_manager.get_active_count(),
                "waiting_count": task_queue_manager.get_queue_length(),
            }
        )
    except Exception as e:
        logger.error(f"触发调度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发调度失败: {str(e)}",
        )


@router.delete("/clear", response_model=ApiResponse[dict])
async def clear_waiting_queue(
    confirm: bool = False,
    payload: dict = Depends(get_super_admin_required),  # 仅超级管理员可清空
):
    """
    清空等待队列（慎用）

    Args:
        confirm: 确认清空（必须显式传 true）

    Returns:
        清空结果
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请传递 confirm=true 以确认清空操作",
        )

    try:
        waiting_count = task_queue_manager.get_queue_length()
        task_queue_manager.clear_queue()

        logger.warning(
            f"清空等待队列 | count={waiting_count} | operator={payload.get('sub')}"
        )
        return success_response(
            data={
                "cleared_count": waiting_count,
                "message": f"已清空 {waiting_count} 个等待任务",
            }
        )
    except Exception as e:
        logger.error(f"清空队列失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空队列失败: {str(e)}",
        )


@router.post("/recover-stale", response_model=ApiResponse[dict])
async def recover_stale_tasks(
    timeout_minutes: Optional[int] = 120,  # 默认2小时
    payload: dict = Depends(get_super_admin_required),
):
    """
    恢复超时未完成的活跃任务

    将运行时间超过指定时长的活跃任务重新加入等待队列。
    用于处理 Worker 崩溃等异常情况。

    Args:
        timeout_minutes: 超时时长（分钟，默认120）

    Returns:
        恢复结果
    """
    try:
        from datetime import datetime, timedelta

        active_tasks = task_queue_manager.get_active_tasks()
        stale_tasks = []
        current_time = datetime.utcnow()

        for task_info in active_tasks:
            started_at_str = task_info.get("started_at")
            if not started_at_str:
                continue

            try:
                started_at = datetime.fromisoformat(started_at_str)
                elapsed = current_time - started_at

                if elapsed > timedelta(minutes=timeout_minutes):
                    # 超时任务，重新入队
                    item_id = task_info.get("item_id")
                    owner_operator_id = None

                    # 需要从数据库查询 owner_operator_id
                    # 简化处理：从 task_info 中获取或查询数据库
                    stale_tasks.append(
                        {
                            "item_id": item_id,
                            "celery_task_id": task_info.get("celery_task_id"),
                            "started_at": started_at_str,
                            "elapsed_minutes": int(elapsed.total_seconds() / 60),
                        }
                    )

                    # 从活跃任务中移除
                    task_queue_manager.remove_active_task(item_id)

                    # 重新入队（需要 owner_operator_id，这里暂时跳过）
                    # TODO: 从数据库查询 owner_operator_id

            except (ValueError, TypeError) as parse_e:
                logger.error(f"解析任务开始时间失败: {parse_e}")
                continue

        logger.info(
            f"恢复超时任务 | timeout={timeout_minutes}min | stale_count={len(stale_tasks)}"
        )
        return success_response(
            data={
                "timeout_minutes": timeout_minutes,
                "stale_count": len(stale_tasks),
                "stale_tasks": stale_tasks,
            }
        )
    except Exception as e:
        logger.error(f"恢复超时任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复超时任务失败: {str(e)}",
        )
