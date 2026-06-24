"""
任务队列管理器

实现智能的任务队列管理：
1. 当 Worker 队列满时，任务进入等待队列
2. Worker 空闲时按 FIFO 顺序执行
3. 提供队列状态监控
4. 使用分布式锁防止多 Worker 重复调度（防死锁）
"""

import json
import logging
from typing import Any, Dict, Optional

import redis
from redis.exceptions import LockError, RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Redis 键前缀
QUEUE_KEY = "task_queue:waiting"  # 等待队列（List，FIFO）
ACTIVE_KEY = "task_queue:active"  # 活跃任务集合（Set）
MAX_CONCURRENT_KEY = "task_queue:max_concurrent"  # 最大并发数
DISPATCH_LOCK_KEY = "task_queue:dispatch_lock"  # 调度锁（防止多 Worker 重复调度）
LOCK_TIMEOUT = 10  # 锁超时时间（秒），防止死锁


class TaskQueueManager:
    """任务队列管理器（支持分布式锁）"""

    def __init__(self):
        settings = get_settings()
        self.redis_client = redis.Redis.from_url(
            settings.redis_url, db=3, decode_responses=True  # 使用独立的 DB 避免冲突
        )
        # 初始化最大并发数（如果 Redis 中没有）
        self._init_max_concurrent()

    def _init_max_concurrent(self) -> None:
        """初始化最大并发数（从配置读取默认值）"""
        try:
            if not self.redis_client.exists(MAX_CONCURRENT_KEY):
                settings = get_settings()
                default_value = getattr(settings, "task_queue_max_concurrent", 64)
                self.redis_client.set(MAX_CONCURRENT_KEY, default_value)
                logger.info(f"初始化最大并发任务数: {default_value}")
        except RedisError as e:
            logger.error(f"初始化最大并发数失败: {e}")

    def _acquire_lock(self, timeout: int = LOCK_TIMEOUT) -> Optional[redis.lock.Lock]:
        """
        获取分布式锁（带超时，防止死锁）

        Args:
            timeout: 锁超时时间（秒）

        Returns:
            锁对象（如果获取成功），否则返回 None
        """
        try:
            lock = self.redis_client.lock(
                DISPATCH_LOCK_KEY,
                timeout=timeout,  # 锁自动过期时间（防止死锁）
                blocking=False,  # 非阻塞模式，立即返回
            )

            if lock.acquire():
                logger.debug(f"获取调度锁成功 | lock_key={DISPATCH_LOCK_KEY}")
                return lock
            else:
                logger.debug(
                    f"调度锁被占用，跳过本次调度 | lock_key={DISPATCH_LOCK_KEY}"
                )
                return None
        except (RedisError, LockError) as e:
            logger.error(f"获取调度锁失败: {e}")
            return None

    def _release_lock(self, lock: redis.lock.Lock) -> None:
        """
        释放分布式锁（安全释放，避免异常）

        Args:
            lock: 锁对象
        """
        try:
            if lock and lock.locked():
                lock.release()
                logger.debug(f"释放调度锁成功 | lock_key={DISPATCH_LOCK_KEY}")
        except (RedisError, LockError) as e:
            logger.error(f"释放调度锁失败: {e}")

    def set_max_concurrent(self, max_concurrent: int) -> None:
        """设置最大并发任务数"""
        try:
            self.redis_client.set(MAX_CONCURRENT_KEY, max_concurrent)
            logger.info(f"设置最大并发任务数: {max_concurrent}")
        except RedisError as e:
            logger.error(f"设置最大并发数失败: {e}")
            raise

    def get_max_concurrent(self) -> int:
        """获取最大并发任务数"""
        try:
            value = self.redis_client.get(MAX_CONCURRENT_KEY)
            if value:
                return int(value)
            # 如果 Redis 中没有，从 settings 读取默认值
            settings = get_settings()
            return getattr(settings, "task_queue_max_concurrent", 64)
        except (RedisError, ValueError) as e:
            logger.error(f"获取最大并发数失败: {e}")
            return getattr(get_settings(), "task_queue_max_concurrent", 64)

    def enqueue_task(
        self, item_id: int, owner_operator_id: int, priority: int = 0
    ) -> int:
        """
        将任务加入等待队列

        Args:
            item_id: 子任务ID
            owner_operator_id: 创作管理员ID
            priority: 优先级（未使用，保留扩展）

        Returns:
            在队列中的位置（1-based）
        """
        task_data = {
            "item_id": item_id,
            "owner_operator_id": owner_operator_id,
            "priority": priority,
        }

        try:
            # 使用 Redis List 作为队列，RPUSH 入队（FIFO）
            self.redis_client.rpush(QUEUE_KEY, json.dumps(task_data))
            queue_length = self.redis_client.llen(QUEUE_KEY)
            logger.info(f"任务入队: item_id={item_id}, 队列位置={queue_length}")
            return queue_length
        except RedisError as e:
            logger.error(f"任务入队失败: {e}")
            raise

    def dequeue_task(self) -> Optional[Dict[str, Any]]:
        """
        从等待队列取出任务（FIFO）

        Returns:
            任务数据字典，如果队列为空则返回 None
        """
        try:
            # LPOP 出队（FIFO）
            task_data = self.redis_client.lpop(QUEUE_KEY)
            if task_data:
                return json.loads(task_data)
            return None
        except RedisError as e:
            logger.error(f"任务出队失败: {e}")
            raise

    def get_queue_length(self) -> int:
        """获取等待队列长度"""
        try:
            return self.redis_client.llen(QUEUE_KEY)
        except RedisError as e:
            logger.error(f"获取队列长度失败: {e}")
            return 0

    def get_queue_tasks(self, start: int = 0, end: int = -1) -> list:
        """
        获取等待队列中的任务列表

        Args:
            start: 起始位置
            end: 结束位置（-1 表示到末尾）

        Returns:
            任务数据列表
        """
        try:
            tasks = self.redis_client.lrange(QUEUE_KEY, start, end)
            return [json.loads(t) for t in tasks]
        except RedisError as e:
            logger.error(f"获取队列任务失败: {e}")
            return []

    def add_active_task(self, item_id: int, celery_task_id: str) -> None:
        """添加活跃任务"""
        try:
            import datetime

            task_info = {
                "item_id": item_id,
                "celery_task_id": celery_task_id,
                "started_at": datetime.datetime.utcnow().isoformat(),
            }
            self.redis_client.sadd(ACTIVE_KEY, json.dumps(task_info))
            logger.info(
                f"添加活跃任务: item_id={item_id}, celery_task_id={celery_task_id}"
            )
        except RedisError as e:
            logger.error(f"添加活跃任务失败: {e}")
            raise

    def remove_active_task(self, item_id: int) -> None:
        """移除活跃任务"""
        try:
            # 需要遍历集合找到对应的任务
            members = self.redis_client.smembers(ACTIVE_KEY)
            for member in members:
                task_info = json.loads(member)
                if task_info.get("item_id") == item_id:
                    self.redis_client.srem(ACTIVE_KEY, member)
                    logger.info(f"移除活跃任务: item_id={item_id}")
                    break
        except RedisError as e:
            logger.error(f"移除活跃任务失败: {e}")
            raise

    def get_active_tasks(self) -> list:
        """获取所有活跃任务"""
        try:
            members = self.redis_client.smembers(ACTIVE_KEY)
            return [json.loads(m) for m in members]
        except RedisError as e:
            logger.error(f"获取活跃任务失败: {e}")
            return []

    def get_active_count(self) -> int:
        """获取活跃任务数量"""
        try:
            return self.redis_client.scard(ACTIVE_KEY)
        except RedisError as e:
            logger.error(f"获取活跃任务数量失败: {e}")
            return 0

    def can_dispatch(self) -> bool:
        """检查是否可以调度新任务（活跃数 < 最大并发数）"""
        active_count = self.get_active_count()
        max_concurrent = self.get_max_concurrent()
        return active_count < max_concurrent

    def try_dispatch_next(self) -> Optional[Dict[str, Any]]:
        """
        尝试调度下一个等待任务（带分布式锁，防止多 Worker 重复调度）

        Returns:
            被调度的任务数据，如果没有可调度的任务则返回 None
        """
        # 先检查是否可以调度
        if not self.can_dispatch():
            logger.info("已达到最大并发数，暂不调度新任务")
            return None

        # 获取分布式锁（防止多 Worker 重复调度）
        lock = self._acquire_lock()
        if not lock:
            # 锁被占用，跳过本次调度
            return None

        try:
            # 再次检查（双检锁，防止竞态条件）
            if not self.can_dispatch():
                logger.info("双检锁：已达到最大并发数，放弃调度")
                return None

            # 从队列取出任务
            task_data = self.dequeue_task()
            if task_data:
                logger.info(f"调度下一个任务: item_id={task_data['item_id']}")
                return task_data
            else:
                logger.info("等待队列为空，无需调度")
                return None
        finally:
            # 释放锁（必须在 finally 中释放，防止死锁）
            self._release_lock(lock)

    def dispatch_from_queue(
        self, owner_operator_id: int, max_dispatch: int = 10
    ) -> int:
        """
        从等待队列中调度任务到 Celery（带分布式锁）

        Args:
            owner_operator_id: 创作管理员ID
            max_dispatch: 最大调度数量（防止无限循环）

        Returns:
            成功调度的任务数量
        """
        dispatched_count = 0

        for _ in range(max_dispatch):
            # 获取分布式锁
            lock = self._acquire_lock()
            if not lock:
                logger.info("调度锁被占用，暂停调度")
                break

            try:
                # 检查是否可以调度
                if not self.can_dispatch():
                    logger.info(
                        f"⏸ 达到最大并发数，暂停调度 | active={self.get_active_count()} | max={self.get_max_concurrent()}"
                    )
                    break

                # 从队列取出任务
                task_data = self.dequeue_task()
                if not task_data:
                    logger.info(
                        f"✔ 等待队列已空，调度完成 | dispatched={dispatched_count}"
                    )
                    break

                item_id = task_data["item_id"]
                task_owner_id = task_data["owner_operator_id"]

                # 分发到 Celery
                try:

                    from app.tasks.generation_tasks import \
                        process_generation_item_phased

                    celery_task = process_generation_item_phased.delay(
                        item_id, task_owner_id
                    )
                    # 注意：add_active_task 现在由 task_prerun 信号处理器处理
                    dispatched_count += 1
                    logger.info(
                        f"▶ 调度任务到Worker | item_id={item_id} | celery_id={celery_task.id}"
                    )
                except Exception as e:
                    logger.error(f"✘ 调度任务失败 | item_id={item_id} | error={e}")
                    # 重新入队尾部
                    self.enqueue_task(item_id, task_owner_id)

            finally:
                # 释放锁
                self._release_lock(lock)

        return dispatched_count

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态统计"""
        try:
            active_tasks = self.get_active_tasks()
            waiting_tasks = self.get_queue_tasks()

            max_concurrent = self.get_max_concurrent()
            active_count = len(active_tasks)
            idle_count = max(0, max_concurrent - active_count)
            return {
                "max_concurrent": max_concurrent,
                "active_count": active_count,
                "idle_count": idle_count,
                "waiting_count": len(waiting_tasks),
                "active_tasks": active_tasks,
                "waiting_tasks": waiting_tasks[:20],  # 只返回前20条
            }
        except Exception as e:
            logger.error(f"获取队列状态失败: {e}")
            return {
                "max_concurrent": 0,
                "active_count": 0,
                "idle_count": 0,
                "waiting_count": 0,
                "active_tasks": [],
                "waiting_tasks": [],
            }

    def clear_queue(self) -> None:
        """清空等待队列（慎用）"""
        try:
            self.redis_client.delete(QUEUE_KEY)
            logger.warning("已清空等待队列")
        except RedisError as e:
            logger.error(f"清空队列失败: {e}")
            raise

    def recover_stale_tasks(self, timeout_minutes: int = 120) -> Dict[str, Any]:
        """
        恢复超时未完成的活跃任务

        将运行时间超过指定时长的活跃任务重新加入等待队列。
        用于处理 Worker 崩溃等异常情况。

        Args:
            timeout_minutes: 超时时长（分钟，默认120）

        Returns:
            恢复结果字典
        """
        try:
            import datetime

            active_tasks = self.get_active_tasks()
            stale_tasks = []
            current_time = datetime.datetime.utcnow()

            for task_info in active_tasks:
                started_at_str = task_info.get("started_at")
                if not started_at_str:
                    continue

                try:
                    started_at = datetime.datetime.fromisoformat(started_at_str)
                    elapsed = current_time - started_at

                    if elapsed > datetime.timedelta(minutes=timeout_minutes):
                        # 超时任务，重新入队
                        item_id = task_info.get("item_id")
                        owner_operator_id = task_info.get("owner_operator_id", 0)

                        # 从活跃任务中移除
                        self.remove_active_task(item_id)

                        # 重新入队
                        self.enqueue_task(item_id, owner_operator_id)

                        stale_tasks.append(
                            {
                                "item_id": item_id,
                                "celery_task_id": task_info.get("celery_task_id"),
                                "started_at": started_at_str,
                                "elapsed_minutes": int(elapsed.total_seconds() / 60),
                            }
                        )

                except (ValueError, TypeError) as parse_e:
                    logger.error(f"解析任务开始时间失败: {parse_e}")
                    continue

            logger.info(
                f"恢复超时任务 | timeout={timeout_minutes}min | stale_count={len(stale_tasks)}"
            )
            return {
                "timeout_minutes": timeout_minutes,
                "stale_count": len(stale_tasks),
                "stale_tasks": stale_tasks,
            }
        except Exception as e:
            logger.error(f"恢复超时任务失败: {e}")
            raise


# 全局队列管理器实例
task_queue_manager = TaskQueueManager()
