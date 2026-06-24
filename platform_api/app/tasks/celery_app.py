"""
Celery 应用配置 (celery_app.py)

配置 Celery 异步任务队列。

Author: Claude Code
Date: 2025
"""

from celery import Celery
from celery.signals import task_postrun, task_prerun, worker_process_init

from app.core.config import get_settings

settings = get_settings()

# 创建 Celery 应用
celery_app = Celery(
    "miaobi_content_factory",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,  # 使用本地时区而不是UTC
    task_track_started=True,
    task_time_limit=3600,  # 单个任务最大执行时间 1 小时
    task_soft_time_limit=3000,  # 软时间限制 50 分钟
    worker_prefetch_multiplier=1,  # 每个 worker 预取任务数量
    worker_max_tasks_per_child=1000,  # 每个 worker 处理 1000 个任务后重启
    # Celery Beat 调度配置
    beat_schedule={
        # 每分钟检查一次定时任务
        "check-scheduled-tasks-every-minute": {
            "task": "app.tasks.scheduled_task_scheduler.check_and_execute_scheduled_tasks",
            "schedule": 60.0,  # 每 60 秒执行一次
        },
        # 每 30 分钟恢复超时任务（防止 Worker 崩溃导致任务卡住）
        "recover-stale-tasks-every-30-minutes": {
            "task": "app.tasks.task_queue_tasks.recover_stale_tasks",
            "schedule": 1800.0,  # 每 30 分钟执行一次
            "kwargs": {"timeout_minutes": 120},  # 超时阈值：2 小时
        },
        # 每 10 分钟清理孤立的活跃任务记录
        "cleanup-orphaned-active-tasks-every-10-minutes": {
            "task": "app.tasks.task_queue_tasks.cleanup_orphaned_active_tasks",
            "schedule": 600.0,  # 每 10 分钟执行一次
        },
        # 每 5 分钟监控队列健康状态
        "monitor-queue-health-every-5-minutes": {
            "task": "app.tasks.task_queue_tasks.monitor_queue_health",
            "schedule": 300.0,  # 每 5 分钟执行一次
        },
    },
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks"])


# ============================================
# Worker 进程初始化信号
# 在每个 Celery worker 子进程启动时执行，
# 关闭从父进程（Celery launcher）继承的 async engine，
# 确保 worker 子进程创建属于自己的独立 engine，
# 避免 aiomysql 连接池事件循环冲突。
# ============================================
@worker_process_init.connect
def on_worker_process_init(**kwargs):
    """
    Celery worker 子进程初始化回调。
    强制关闭从父进程继承的 async engine，
    让当前进程的首次 DB 访问触发全新 engine 创建。
    """
    import logging
    import os

    logger = logging.getLogger(__name__)
    pid = os.getpid()
    try:
        from app.core.database import _invalidate_process_async_engine

        _invalidate_process_async_engine()
        logger.info("[Celery] worker_process_init ok | pid=%s", pid)
    except Exception as e:
        logger.error("[Celery] worker_process_init FAILED | pid=%s | error=%s", pid, e)
        raise


# ============================================
# 任务队列管理信号
# ============================================

# 延迟导入，避免循环导入
_task_queue_manager = None


def _get_task_queue_manager():
    """延迟加载任务队列管理器"""
    global _task_queue_manager
    if _task_queue_manager is None:
        from app.services.task_queue_manager import task_queue_manager

        _task_queue_manager = task_queue_manager
    return _task_queue_manager


@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, **kwargs):
    """
    任务开始执行前触发

    将任务添加到活跃任务集合
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # 只处理 generation 相关的任务
        if task and "generation" in task.name:
            item_id = None
            owner_operator_id = None

            # 从任务参数中提取 item_id
            args = kwargs.get("args", [])
            if args and len(args) > 0:
                item_id = args[0]  # 第一个参数通常是 item_id

            if item_id:
                queue_mgr = _get_task_queue_manager()
                queue_mgr.add_active_task(item_id, task_id)
                logger.info(
                    "[Celery] 任务开始 | item_id=%s | celery_id=%s", item_id, task_id
                )
    except Exception as e:
        logger.error("[Celery] on_task_prerun 失败 | error=%s", e)


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """
    任务执行完成后触发

    从活跃任务集合移除，并尝试调度下一个等待任务
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # 只处理 generation 相关的任务
        if task and "generation" in task.name:
            item_id = None

            # 从任务参数中提取 item_id
            args = kwargs.get("args", [])
            if args and len(args) > 0:
                item_id = args[0]  # 第一个参数通常是 item_id

            if item_id:
                queue_mgr = _get_task_queue_manager()
                queue_mgr.remove_active_task(item_id)
                logger.info(
                    "[Celery] 任务完成 | item_id=%s | celery_id=%s", item_id, task_id
                )

                # 尝试调度下一个等待任务
                from app.tasks.generation_tasks import \
                    _dispatch_tasks_from_queue

                # 使用任务参数中的 owner_operator_id
                owner_operator_id = None
                if args and len(args) > 1:
                    owner_operator_id = args[1]

                if owner_operator_id:
                    _dispatch_tasks_from_queue(owner_operator_id, max_dispatch=1)
    except Exception as e:
        logger.error("[Celery] on_task_postrun 失败 | error=%s", e)


@celery_app.task(bind=True)
def debug_task(self):
    """
    调试任务
    """
    print(f"Request: {self.request!r}")
    return "Debug task completed"
