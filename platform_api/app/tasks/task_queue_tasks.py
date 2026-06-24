"""
任务队列相关的 Celery 定时任务 (task_queue_tasks.py)

提供任务队列的定时维护功能：
1. 自动恢复超时任务（防止 Worker 崩溃导致任务卡住）
2. 定期清理过期的活跃任务记录
"""
import logging
from datetime import datetime, timedelta

from celery import shared_task
from redis.exceptions import RedisError

from app.services.task_queue_manager import task_queue_manager

logger = logging.getLogger(__name__)

# 超时阈值（分钟）
DEFAULT_TIMEOUT_MINUTES = 120  # 2 小时


@shared_task(name="app.tasks.task_queue_tasks.recover_stale_tasks")
def recover_stale_tasks(timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES):
    """
    定期恢复超时任务
    
    将运行时间超过指定时长的活跃任务重新加入等待队列。
    用于处理 Worker 崩溃等异常情况。
    
    Args:
        timeout_minutes: 超时时长（分钟，默认 120）
    
    Returns:
        恢复结果字典
    """
    logger.info(f"▶ 开始恢复超时任务 | timeout={timeout_minutes}min")
    
    try:
        result = task_queue_manager.recover_stale_tasks(timeout_minutes)
        
        stale_count = result.get("stale_count", 0)
        if stale_count > 0:
            logger.warning(f"✔ 恢复超时任务完成 | recovered={stale_count}")
        else:
            logger.info(f"✔ 恢复超时任务完成 | 无超时任务")
        
        return result
    except Exception as e:
        logger.error(f"✘ 恢复超时任务失败: {e}")
        raise


@shared_task(name="app.tasks.task_queue_tasks.cleanup_orphaned_active_tasks")
def cleanup_orphaned_active_tasks():
    """
    清理孤立的活跃任务记录
    
    检查活跃任务集合中的任务是否真的在运行，
    如果任务已完成但记录未清理（如 Worker 崩溃），则清理这些记录。
    """
    logger.info("▶ 开始清理孤立的活跃任务记录")
    
    try:
        active_tasks = task_queue_manager.get_active_tasks()
        orphaned_count = 0
        
        for task_info in active_tasks:
            item_id = task_info.get("item_id")
            celery_task_id = task_info.get("celery_task_id")
            
            if not celery_task_id:
                # 没有 Celery task ID，直接清理
                task_queue_manager.remove_active_task(item_id)
                orphaned_count += 1
                logger.warning(f"清理孤立任务（无Celery ID）: item_id={item_id}")
                continue
            
            # 检查 Celery 任务状态
            try:
                from celery import current_app
                celery_app = current_app
                
                # 查询任务状态
                task_result = celery_app.AsyncResult(celery_task_id)
                
                # 如果任务已完成（成功/失败/取消），但仍在活跃集合中，则清理
                if task_result.ready():
                    task_queue_manager.remove_active_task(item_id)
                    orphaned_count += 1
                    logger.info(f"清理已完成任务记录: item_id={item_id} | status={task_result.status}")
                    
            except Exception as check_e:
                logger.error(f"检查任务状态失败: item_id={item_id} | error={check_e}")
                continue
        
        logger.info(f"✔ 清理孤立任务完成 | cleaned={orphaned_count}")
        return {"orphaned_count": orphaned_count}
        
    except Exception as e:
        logger.error(f"✘ 清理孤立任务失败: {e}")
        raise


@shared_task(name="app.tasks.task_queue_tasks.monitor_queue_health")
def monitor_queue_health():
    """
    监控队列健康状态
    
    检查队列状态，如果发现异常（如等待队列过长、活跃任务数异常），
    记录日志或发送告警（待实现）。
    """
    logger.info("▶ 开始监控队列健康状态")
    
    try:
        status = task_queue_manager.get_queue_status()
        
        max_concurrent = status["max_concurrent"]
        active_count = status["active_count"]
        waiting_count = status["waiting_count"]
        
        # 检查等待队列是否过长
        if waiting_count > 100:
            logger.warning(f"⚠️ 等待队列过长 | waiting={waiting_count}")
            # TODO: 发送告警通知
        
        # 检查活跃任务数是否达到上限
        if active_count >= max_concurrent:
            logger.warning(f"⚠️ 队列已满 | active={active_count} | max={max_concurrent} | waiting={waiting_count}")
            # TODO: 发送告警通知
        
        # 检查是否有超时任务
        current_time = datetime.utcnow()
        stale_count = 0
        for task_info in status["active_tasks"]:
            started_at_str = task_info.get("started_at")
            if not started_at_str:
                continue
            
            try:
                started_at = datetime.fromisoformat(started_at_str)
                elapsed = current_time - started_at
                
                if elapsed > timedelta(minutes=DEFAULT_TIMEOUT_MINUTES):
                    stale_count += 1
            except (ValueError, TypeError):
                continue
        
        if stale_count > 0:
            logger.warning(f"⚠️ 发现超时任务 | stale_count={stale_count}")
            # TODO: 自动触发恢复任务
            # recover_stale_tasks.delay()
        
        logger.info(f"✔ 队列监控完成 | active={active_count} | waiting={waiting_count} | stale={stale_count}")
        
        return {
            "active_count": active_count,
            "waiting_count": waiting_count,
            "stale_count": stale_count,
            "max_concurrent": max_concurrent
        }
        
    except Exception as e:
        logger.error(f"✘ 队列监控失败: {e}")
        raise
