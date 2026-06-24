"""
内容生成任务 (generation_tasks.py)

Celery 异步任务定义。

使用三阶段事务架构：
- 阶段1：读取数据（<1秒）→ 关闭连接
- 阶段2：AI 生成（30-90秒）→ 无数据库连接
- 阶段3：保存结果（<1秒）→ 关闭连接

连接持有时间：从 100秒 降到 <2秒
连接利用率提升：50倍

Author: Claude Code
Date: 2026-05-10
"""

import asyncio
import logging

from celery import shared_task

from app.core.database import async_session_maker, _invalidate_process_async_engine
from app.core.exceptions import GenerationItemNotFoundError
from app.core.retry import NonRetryableError
from app.services.generation_service import GenerationService
from app.services.task_queue_manager import task_queue_manager

logger = logging.getLogger(__name__)


# ============================================
# 日志工具函数
# ============================================

def _task_debug(fmt: str, *args, **kwargs):
    """调试日志"""
    logger.debug(f"[Celery] {fmt}", *args, **kwargs)


def _task_info(fmt: str, *args, **kwargs):
    """信息日志"""
    logger.info(f"[Celery] {fmt}", *args, **kwargs)


def _task_warning(fmt: str, *args, **kwargs):
    """警告日志"""
    logger.warning(f"[Celery] {fmt}", *args, **kwargs)


def _task_error(fmt: str, *args, **kwargs):
    """错误日志"""
    logger.error(f"[Celery] {fmt}", *args, **kwargs)


# ============================================
# 队列调度辅助函数
# ============================================

def _dispatch_tasks_from_queue(owner_operator_id: int, max_dispatch: int = 10) -> int:
    """
    从等待队列中调度任务到 Celery
    
    Args:
        owner_operator_id: 创作管理员ID
        max_dispatch: 最大调度数量（防止无限循环）
    
    Returns:
        成功调度的任务数量
    """
    dispatched_count = 0
    
    for _ in range(max_dispatch):
        # 检查是否可以调度新任务
        if not task_queue_manager.can_dispatch():
            _task_info("[PAUSED] 达到最大并发数，暂停调度 | active=%s | max=%s", 
                       task_queue_manager.get_active_count(),
                       task_queue_manager.get_max_concurrent())
            break
        
        # 从队列取出任务
        task_data = task_queue_manager.dequeue_task()
        if not task_data:
            _task_info("[OK] 等待队列已空，调度完成 | dispatched=%s", dispatched_count)
            break
        
        item_id = task_data["item_id"]
        task_owner_id = task_data["owner_operator_id"]
        
        # 分发到 Celery
        try:
            celery_task = process_generation_item_phased.delay(item_id, task_owner_id)
            # 注意：add_active_task 现在由 task_prerun 信号处理器处理
            dispatched_count += 1
            _task_info("[START] 调度任务到Worker | item_id=%s | celery_id=%s",
                       item_id, celery_task.id)
        except Exception as e:
            _task_error("[ERROR] 调度任务失败 | item_id=%s | error=%s", item_id, str(e))
            # 重新入队尾部
            task_queue_manager.enqueue_task(item_id, task_owner_id)
    
    return dispatched_count


# ============================================
# 任务启动
# ============================================

@shared_task(name="app.tasks.generation_tasks.start_generation_task")
def start_generation_task(task_id: int, owner_operator_id: int):
    """
    启动生成任务

    为任务中的所有子任务创建 Celery 任务（使用三阶段架构）。
    """
    _task_info("▶ 启动生成任务 | task_id=%s | owner=%s", task_id, owner_operator_id)

    _invalidate_process_async_engine()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _start_generation_task_async(task_id, owner_operator_id)
        )
        _task_info("✔ 启动任务完成 | task_id=%s | result=%s", task_id, result)
        return result
    finally:
        _invalidate_process_async_engine()
        loop.close()


async def _start_generation_task_async(task_id: int, owner_operator_id: int):
    """
    异步启动生成任务
    """
    async with async_session_maker() as db:
        # 检查任务当前状态
        task = await GenerationService.get_generation_task(
            db, task_id, owner_operator_id
        )
        if not task:
            _task_info("✘ 任务不存在 | task_id=%s", task_id)
            raise ValueError(f"Task {task_id} not found")
        if task.status in ("completed", "failed", "cancelled"):
            _task_info("✘ 任务已是终态 | task_id=%s | status=%s", task_id, task.status)
            raise ValueError(f"任务已是终态({task.status})，无法重新启动，请使用重试功能")

        _task_info("▶ 任务状态 pending → processing | task_id=%s | items=%s", task_id, task.total_count)
        # 更新任务状态为处理中
        await GenerationService.update_generation_task_status(
            db, task_id, owner_operator_id, "processing", "开始处理"
        )

        # 获取所有子任务
        page = 1
        all_items = []

        while True:
            items, _ = await GenerationService.list_generation_items(
                db, task_id, owner_operator_id, page=page, limit=100
            )
            if not items:
                break
            all_items.extend(items)
            page += 1

        # 为每个子任务加入等待队列（而不是直接分发）
        queued_count = 0
        for item in all_items:
            if item.status == "queued":
                _task_debug("  子任务入队 | item_id=%s | sub_user_id=%s | template_id=%s",
                            item.id, item.sub_user_id, item.template_id)
                # 加入等待队列
                queue_position = task_queue_manager.enqueue_task(item.id, owner_operator_id)
                queued_count += 1

        _task_info("✔ 子任务入队完成 | task_id=%s | total=%s | queued=%s | queue_position=%s",
                   task_id, len(all_items), queued_count, task_queue_manager.get_queue_length())
        
        # 尝试调度队列中的任务
        _dispatch_tasks_from_queue(owner_operator_id)
        
        logger.info(f"Enqueued {queued_count} items for task {task_id} (phased mode)")
        return {"task_id": task_id, "items_count": len(all_items), "queued_count": queued_count}


# ============================================
# 三阶段事务处理
# ============================================

async def _process_generation_item_phased_async(item_id: int, owner_operator_id: int):
    """
    使用三阶段事务架构处理生成子任务

    架构说明：
    - 阶段1：读取数据（<1秒）→ 关闭连接
    - 阶段2：AI 生成（30-90秒）→ 无数据库连接
    - 阶段3：保存结果（<1秒）→ 关闭连接

    注意：embedding 在阶段2的去重检测中直接异步保存
    """
    from app.services.generation_phases import (
        phase1_load_input_data,
        execute_phase2_generation,
        phase3_save_result,
    )

    _task_info("▶ [Phase/1/3] 开始三阶段处理 | item_id=%s", item_id)

    try:
        # ========== 阶段0：状态守卫 ==========
        async with async_session_maker() as read_db:
            item = await GenerationService.get_generation_item(
                read_db, item_id, owner_operator_id
            )
            if not item:
                _task_info("✘ 子任务不存在 | item_id=%s", item_id)
                raise GenerationItemNotFoundError()

            _task_debug("  [Phase1] 子任务状态 | status=%s", item.status)

            if item.status == "paused":
                _task_info("[SKIPPED] 子任务已被暂停 | item_id=%s", item_id)
                return {"item_id": item_id, "status": "paused", "skipped": True}

            # 允许的状态：queued, failed, completed+pending_publish
            can_execute = False
            if item.status == "queued":
                can_execute = True
            elif item.status == "failed":
                can_execute = True
            elif item.status == "completed" and item.distribution_status == "pending_publish":
                can_execute = True

            if not can_execute:
                _task_info("[SKIPPED] 子任务状态不可执行 | status=%s | distribution_status=%s", item.status, item.distribution_status)
                return {"item_id": item_id, "status": item.status, "skipped": True}

            task_id = item.task_id

        # 检查父任务是否存在（防止孤儿 item 无限循环）
        async with async_session_maker() as check_db:
            parent_exists = await GenerationService.check_task_exists(
                check_db, task_id, owner_operator_id
            )
            if not parent_exists:
                _task_error("[ORPHAN] 检测到孤儿子任务，直接删除 | item_id=%s | task_id=%s", item_id, task_id)
                await GenerationService.delete_orphaned_item(check_db, item_id, owner_operator_id)
                return {"item_id": item_id, "status": "deleted", "reason": "orphaned_item"}

        # 状态更新：失败重试或已完成重新生成
        if item.status in ("failed", "completed"):
            _task_info("[RESET] 重置子任务 | item_id=%s | old_status=%s", item_id, item.status)
            async with async_session_maker() as reset_db:
                await GenerationService.reset_item_for_regeneration(
                    reset_db, item_id, owner_operator_id
                )

        # CAS 守卫：queued → generating
        async with async_session_maker() as cas_db:
            updated = await GenerationService.update_generation_item_status(
                cas_db, item_id, owner_operator_id, "generating",
                expected_old_status="queued"
            )
            if updated is None:
                _task_info("[SKIPPED] CAS 守卫失败 | item_id=%s", item_id)
                return {"item_id": item_id, "status": "skipped_by_cas", "skipped": True}

        _task_info("▶ [Phase/2/3] 开始AI生成 | item_id=%s | task_id=%s", item_id, task_id)

        # ========== 阶段1：加载输入数据 ==========
        input_data = await phase1_load_input_data(
            task_id=task_id,
            item_id=item_id,
            owner_operator_id=owner_operator_id,
        )

        # ========== 阶段2：AI 生成（无数据库连接）==========
        # 这一步可能耗时 30-90 秒，但不持有任何数据库连接
        # embedding 在去重检测中直接异步保存
        output_data = await execute_phase2_generation(input_data)

        _task_info("▶ [Phase/3/3] AI生成完成，开始保存 | item_id=%s", item_id)

        # ========== 阶段3：保存结果 ==========
        save_success = await phase3_save_result(output_data, owner_operator_id)

        if save_success:
            _task_info("[OK] 三阶段处理完成 | item_id=%s | success=%s", item_id, output_data.success)
            return {"item_id": item_id, "status": "completed" if output_data.success else "failed"}
        else:
            _task_warning("[ERROR] 结果保存失败 | item_id=%s", item_id)
            return {"item_id": item_id, "status": "save_failed"}

    except Exception as e:
        error_msg = str(e)
        _task_error("[ERROR] 三阶段处理异常 | item_id=%s | error=%s", item_id, error_msg[:300])
        logger.error(f"Phased processing failed for item {item_id}: {error_msg}")

        # 尝试标记失败
        try:
            async with async_session_maker() as fail_db:
                await GenerationService.update_generation_item_status(
                    fail_db, item_id, owner_operator_id, "failed", error_msg[:500]
                )
        except Exception as inner_e:
            _task_error("[ERROR] 标记失败也失败 | item_id=%s | error=%s", item_id, inner_e)

        raise


@shared_task(bind=True, max_retries=3, name="app.tasks.generation_tasks.process_generation_item_phased")
def process_generation_item_phased(self, item_id: int, owner_operator_id: int):
    """
    Celery 任务入口：使用三阶段事务架构处理生成子任务

    Args:
        item_id: 子任务ID
        owner_operator_id: 创作管理员ID

    Returns:
        处理结果字典
    """
    _task_info("[START] 启动三阶段生成任务 | item_id=%s | owner=%s | celery_id=%s", 
               item_id, owner_operator_id, self.request.id)

    _invalidate_process_async_engine()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _process_generation_item_phased_async(item_id, owner_operator_id)
        )
        _task_info("[OK] 三阶段任务完成 | item_id=%s | result=%s", item_id, result)
        return result
    except NonRetryableError as e:
        # 数据孤儿问题，不应重试
        _task_error("[ERROR] 不可重试错误 | item_id=%s | error=%s", item_id, str(e)[:200])
        # 直接返回失败结果，不触发重试
        return {"item_id": item_id, "status": "failed", "error": str(e)}
    except Exception as e:
        _task_error("[ERROR] 三阶段任务失败 | item_id=%s | error=%s", item_id, str(e)[:200])
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    finally:
        # 从活跃任务中移除
        try:
            task_queue_manager.remove_active_task(item_id)
            _task_info("[OK] 从活跃任务移除 | item_id=%s | active=%s", 
                       item_id, task_queue_manager.get_active_count())
        except Exception as rm_e:
            _task_error("[ERROR] 移除活跃任务失败 | item_id=%s | error=%s", item_id, str(rm_e))
        
        # 尝试调度下一个等待任务
        try:
            _dispatch_tasks_from_queue(owner_operator_id, max_dispatch=1)
        except Exception as dispatch_e:
            _task_error("[ERROR] 调度下一个任务失败 | error=%s", str(dispatch_e))
        
        _invalidate_process_async_engine()
        loop.close()
