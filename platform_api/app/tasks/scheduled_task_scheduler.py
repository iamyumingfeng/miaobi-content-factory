"""
定时任务调度器 (scheduled_task_scheduler.py)

使用 Celery Beat 定时扫描并执行定时任务。

Author: Claude Code
Date: 2025
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.scheduled_task import ScheduledTask
from app.services.scheduled_task_service import ScheduledTaskService

logger = logging.getLogger(__name__)

# 配置
settings = get_settings()

# 数据库 URL：将异步驱动 (aiomysql) 转换为同步驱动 (pymysql)
# 因为 Celery 任务是同步执行的
_sync_db_url = settings.database_url
if _sync_db_url.startswith("mysql+aiomysql"):
    _sync_db_url = _sync_db_url.replace("mysql+aiomysql", "mysql+pymysql")
    logger.info("[ScheduledTaskScheduler] 数据库驱动已转换: aiomysql → pymysql")


@shared_task(
    bind=True,
    name="app.tasks.scheduled_task_scheduler.check_and_execute_scheduled_tasks",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def check_and_execute_scheduled_tasks(self):
    """
    检查并执行定时任务

    Celery Beat 定时任务，每分钟执行一次。
    扫描所有到期的定时任务，创建对应的 GenerationTask。

    重试策略：
    - 最多重试3次
    - 重试延迟：60秒起，指数退避（最大10分钟）
    - 自动重试所有 Exception 类型的异常
    """
    logger.info("[ScheduledTaskScheduler] 开始扫描定时任务")

    engine = None
    db = None

    try:
        # 创建同步数据库会话（Celery 任务中使用）
        engine = create_engine(
            _sync_db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 获取待执行的任务
        pending_tasks = ScheduledTaskService.get_pending_tasks_sync(db)

        logger.info(f"[ScheduledTaskScheduler] 发现 {len(pending_tasks)} 个待执行任务")

        # 执行每个任务
        for task in pending_tasks:
            try:
                # 执行任务（Service 方法会负责创建执行记录）
                success, generation_task_id, error = (
                    ScheduledTaskService.execute_scheduled_task_sync(db, task.id)
                )

                if success:
                    logger.info(
                        f"[ScheduledTaskScheduler] 任务执行成功 | "
                        f"scheduled_task_id={task.id} | generation_task_id={generation_task_id}"
                    )
                else:
                    logger.error(
                        f"[ScheduledTaskScheduler] 任务执行失败 | "
                        f"scheduled_task_id={task.id} | error={error}"
                    )
                    # 抛出异常触发重试
                    raise Exception(f"任务执行失败: {error}")

            except Exception as e:
                logger.error(
                    f"[ScheduledTaskScheduler] 任务执行异常 | "
                    f"scheduled_task_id={task.id if task else 'unknown'} | error={str(e)}",
                    exc_info=True,
                )
                # 重新抛出异常，触发任务重试
                raise
            finally:
                # 确保每次任务执行后都提交
                try:
                    db.commit()
                except Exception as commit_err:
                    logger.error(
                        f"[ScheduledTaskScheduler] 提交失败 | error={str(commit_err)}",
                        exc_info=True,
                    )
                    db.rollback()

        logger.info("[ScheduledTaskScheduler] 扫描完成")

    except Exception as e:
        logger.error(
            f"[ScheduledTaskScheduler] 扫描异常 | error={str(e)}", exc_info=True
        )
        # 重试整个扫描任务
        raise self.retry(exc=e)

    finally:
        # 确保数据库连接被关闭
        if db:
            try:
                db.close()
                logger.debug("[ScheduledTaskScheduler] 数据库连接已关闭")
            except Exception as close_err:
                logger.error(
                    f"[ScheduledTaskScheduler] 关闭数据库连接失败 | error={str(close_err)}"
                )

        if engine:
            try:
                engine.dispose()
                logger.debug("[ScheduledTaskScheduler] 数据库引擎已释放")
            except Exception as dispose_err:
                logger.error(
                    f"[ScheduledTaskScheduler] 释放数据库引擎失败 | error={str(dispose_err)}"
                )


# ============================================
# 同步版本的 Service 方法（供 Celery 任务使用）
# ============================================


def get_pending_tasks_sync(db, limit: int = 100):
    """
    获取待执行的定时任务（同步版本）
    """

    from sqlalchemy import and_, select

    now = datetime.now()

    query = (
        select(ScheduledTask)
        .where(
            and_(
                ScheduledTask.is_active.is_(True),
                ScheduledTask.status == "active",
                ScheduledTask.next_execution_at <= now,
            )
        )
        .limit(limit)
    )

    result = db.execute(query)
    return result.scalars().all()


def execute_scheduled_task_sync(db, task_id: int):
    """
    执行定时任务（同步版本，委托给异步版本统一处理）
    """
    import asyncio

    from app.core.database import async_session_maker
    from app.services.scheduled_task_service import ScheduledTaskService

    async def _execute():
        async with async_session_maker() as async_db:
            return await ScheduledTaskService.execute_scheduled_task(async_db, task_id)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_execute())
        loop.close()
        return result
    except Exception as e:
        logger.error(
            f"[ScheduledTaskService] 执行定时任务失败 | scheduled_task_id={task_id} | error={str(e)}",
            exc_info=True,
        )
        return False, None, str(e)


def calculate_next_execution_at(schedule_type: str, schedule_config: dict):
    """
    计算下次执行时间（同步版本）
    """
    from datetime import timedelta

    now = datetime.now()

    if schedule_type == "daily":
        # 每日执行
        times = schedule_config.get("times", ["09:00"])
        # 找到下一个执行时间
        next_times = []
        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            next_times.append(next_time)

        return min(next_times)

    elif schedule_type == "weekly":
        # 每周执行
        days = schedule_config.get("days", [1])  # 1=周一, 7=周日
        times = schedule_config.get("times", ["09:00"])

        next_times = []
        for day in days:
            for time_str in times:
                hour, minute = map(int, time_str.split(":"))
                # 计算目标星期几（0=周一, 6=周日）
                target_weekday = day - 1
                current_weekday = now.weekday()

                # 计算天数差
                days_ahead = target_weekday - current_weekday
                if days_ahead < 0:
                    days_ahead += 7
                elif days_ahead == 0:
                    # 同一天，检查时间
                    next_time = now.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    if next_time <= now:
                        days_ahead = 7

                next_time = now + timedelta(days=days_ahead)
                next_time = next_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                next_times.append(next_time)

        return min(next_times)

    # 默认：明天同一时间
    return now + timedelta(days=1)


# 添加同步方法到 Service 类
ScheduledTaskService.get_pending_tasks_sync = staticmethod(get_pending_tasks_sync)
ScheduledTaskService.execute_scheduled_task_sync = staticmethod(
    execute_scheduled_task_sync
)
