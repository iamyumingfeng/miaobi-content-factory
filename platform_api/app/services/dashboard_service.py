"""
AIGC看板服务 (dashboard_service.py)

提供AIGC看板相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy import select, and_, or_, func, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.models import GenerationTask, GenerationItem, SubUser, Material, DashboardAlertDismissal, Operator


class DashboardService:
    """
    AIGC看板服务类
    """

    @staticmethod
    async def get_stats(
        db: AsyncSession, 
        owner_admin_id: Optional[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filter_operator_id: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        获取AIGC看板统计数据

        Args:
            db: 数据库会话
            owner_admin_id: 创作管理员ID，None表示获取所有数据（超级管理员）
            start_date: 统计开始日期，None表示当天
            end_date: 统计结束日期，None表示当天
            filter_operator_id: 筛选的创作管理员ID（超级管理员使用）

        Returns:
            统计数据字典
        """
        logger.debug("[DashboardService] get_stats | owner=%s | start_date=%s | end_date=%s | filter_operator_id=%s", owner_admin_id, start_date, end_date, filter_operator_id)

        # 确定最终的管理员筛选ID
        effective_operator_id = filter_operator_id if filter_operator_id is not None else owner_admin_id

        # 构建基础条件
        sub_user_filter = [] if effective_operator_id is None else [SubUser.owner_operator_id == effective_operator_id]
        gen_item_filter = [] if effective_operator_id is None else [GenerationItem.owner_operator_id == effective_operator_id]

        # 确定统计日期范围
        today = datetime.utcnow().date()
        if start_date is None:
            start_date = today
        if end_date is None:
            end_date = today
        
        # 构建日期范围条件
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # 包含结束日期当天

        # 总创作者数（不依赖日期）
        sub_users_query = select(func.count(SubUser.id))
        if sub_user_filter:
            sub_users_query = sub_users_query.where(and_(*sub_user_filter))
        sub_users_count = await db.scalar(sub_users_query)

        # 生成内容数：统计周期内创建的所有子任务
        gen_query = select(func.count(GenerationItem.id)).where(
            and_(
                *gen_item_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end
            )
        ) if gen_item_filter else select(func.count(GenerationItem.id)).where(
            and_(
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end
            )
        )
        generated_count = await db.scalar(gen_query)

        # 待发布内容数：统计周期内创建的、已分发但未发布的内容
        # distribution_status 为 'distributed' 或 'pending_publish' 都算待发布
        pending_pub_query = select(func.count(GenerationItem.id)).where(
            and_(
                *gen_item_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status.in_(['distributed', 'pending_publish'])
            )
        ) if gen_item_filter else select(func.count(GenerationItem.id)).where(
            and_(
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status.in_(['distributed', 'pending_publish'])
            )
        )
        pending_publish = await db.scalar(pending_pub_query)

        # 已发布内容数：统计周期内创建的、已确认发布的内容
        published_query = select(func.count(GenerationItem.id)).where(
            and_(
                *gen_item_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status == 'published'
            )
        ) if gen_item_filter else select(func.count(GenerationItem.id)).where(
            and_(
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status == 'published'
            )
        )
        published = await db.scalar(published_query)

        return {
            "total_sub_users": sub_users_count or 0,
            "today_generated": generated_count or 0,
            "pending_publish": pending_publish or 0,
            "published": published or 0,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    @staticmethod
    async def get_sub_user_stats(
        db: AsyncSession,
        sub_user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, int]:
        """
        获取创作者的看板统计数据

        Args:
            db: 数据库会话
            sub_user_id: 创作者ID
            start_date: 统计开始日期，None表示当天
            end_date: 统计结束日期，None表示当天

        Returns:
            统计数据字典
        """
        logger.debug("[DashboardService] get_sub_user_stats | sub_user_id=%s | start_date=%s | end_date=%s", sub_user_id, start_date, end_date)

        # 确定统计日期范围
        today = datetime.utcnow().date()
        if start_date is None:
            start_date = today
        if end_date is None:
            end_date = today

        # 构建日期范围条件
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # 包含结束日期当天

        # 创作者只看自己的内容
        base_filter = [GenerationItem.sub_user_id == sub_user_id]

        # 生成内容数：统计周期内创建的子任务
        gen_query = select(func.count(GenerationItem.id)).where(
            and_(
                *base_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end
            )
        )
        generated_count = await db.scalar(gen_query)

        # 待发布内容数：已分发但未发布的内容
        pending_pub_query = select(func.count(GenerationItem.id)).where(
            and_(
                *base_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status.in_(['distributed', 'pending_publish'])
            )
        )
        pending_publish = await db.scalar(pending_pub_query)

        # 已发布内容数
        published_query = select(func.count(GenerationItem.id)).where(
            and_(
                *base_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end,
                GenerationItem.distribution_status == 'published'
            )
        )
        published = await db.scalar(published_query)

        return {
            "total_sub_users": 0,  # 创作者看不到这个指标
            "today_generated": generated_count or 0,
            "pending_publish": pending_publish or 0,
            "published": published or 0,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    @staticmethod
    async def get_trend_data(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据（最近N天）

        Args:
            db: 数据库会话
            owner_admin_id: 创作管理员ID，None表示获取所有数据
            days: 天数（默认7天）

        Returns:
            趋势数据列表
        """
        logger.debug("[DashboardService] get_trend_data | owner=%s | days=%s", owner_admin_id, days)

        result = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(days - 1, -1, -1):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            # 构建过滤条件
            base_filter = [] if owner_admin_id is None else [GenerationItem.owner_operator_id == owner_admin_id]

            # 该天的生成数量
            generated_query = select(func.count(GenerationItem.id)).where(
                and_(
                    *base_filter,
                    GenerationItem.created_at >= day_start,
                    GenerationItem.created_at < day_end,
                    GenerationItem.status.in_(['completed', 'generating'])
                )
            ) if base_filter else select(func.count(GenerationItem.id)).where(
                and_(
                    GenerationItem.created_at >= day_start,
                    GenerationItem.created_at < day_end,
                    GenerationItem.status.in_(['completed', 'generating'])
                )
            )
            generated = await db.scalar(generated_query)

            # 该天的分发数量（distributed_at 在该天内）
            distributed_query = select(func.count(GenerationItem.id)).where(
                and_(
                    *base_filter,
                    GenerationItem.distributed_at >= day_start,
                    GenerationItem.distributed_at < day_end
                )
            ) if base_filter else select(func.count(GenerationItem.id)).where(
                and_(
                    GenerationItem.distributed_at >= day_start,
                    GenerationItem.distributed_at < day_end
                )
            )
            distributed = await db.scalar(distributed_query)

            # 该天的发布数量（confirmed_at 在该天内）
            published_query = select(func.count(GenerationItem.id)).where(
                and_(
                    *base_filter,
                    GenerationItem.confirmed_at >= day_start,
                    GenerationItem.confirmed_at < day_end
                )
            ) if base_filter else select(func.count(GenerationItem.id)).where(
                and_(
                    GenerationItem.confirmed_at >= day_start,
                    GenerationItem.confirmed_at < day_end
                )
            )
            published_count = await db.scalar(published_query)

            result.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "generated": generated or 0,
                "distributed": distributed or 0,
                "published": published_count or 0
            })

        return result

    @staticmethod
    async def get_recent_tasks(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        limit: int = 10,
        page: int = 1,
        filter_operator_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[GenerationTask], int]:
        """
        获取最近的任务列表

        Args:
            db: 数据库会话
            owner_admin_id: 创作管理员ID，None表示获取所有数据
            limit: 每页数量限制
            page: 页码（从1开始）
            filter_operator_id: 筛选的创作管理员ID（超级管理员使用）
            start_date: 开始日期筛选
            end_date: 结束日期筛选

        Returns:
            (任务列表, 总数量)
        """
        logger.debug("[DashboardService] get_recent_tasks | owner=%s | limit=%s | page=%s | filter_operator=%s | start=%s | end=%s", 
                    owner_admin_id, limit, page, filter_operator_id, start_date, end_date)

        # 构建基础查询
        base_query = select(GenerationTask).options(
            selectinload(GenerationTask.material),
            selectinload(GenerationTask.owner_operator)
        )

        # 超级管理员可以按创作管理员筛选
        if filter_operator_id is not None:
            base_query = base_query.where(GenerationTask.owner_operator_id == filter_operator_id)
        elif owner_admin_id is not None:
            base_query = base_query.where(GenerationTask.owner_operator_id == owner_admin_id)

        # 日期筛选
        if start_date:
            base_query = base_query.where(GenerationTask.created_at >= start_date)
        if end_date:
            # 结束日期包含当天，所以加一天
            end_datetime = end_date + timedelta(days=1)
            base_query = base_query.where(GenerationTask.created_at < end_datetime)

        # 先获取总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await db.scalar(count_query) or 0

        # 分页查询
        offset = (page - 1) * limit
        paginated_query = base_query.order_by(desc(GenerationTask.created_at)).offset(offset).limit(limit)

        result = await db.execute(paginated_query)
        tasks = result.scalars().all()

        # 实时从 generation_item 表聚合各状态计数（不依赖冗余字段）
        if tasks:
            task_ids = [t.id for t in tasks]
            count_stmt = (
                select(
                    GenerationItem.task_id,
                    func.count().label("total"),
                    func.sum(func.cast(GenerationItem.status == "queued", Integer)).label("queued"),
                    func.sum(func.cast(GenerationItem.status == "generating", Integer)).label("generating"),
                    func.sum(func.cast(GenerationItem.status == "completed", Integer)).label("completed"),
                    func.sum(func.cast(GenerationItem.status == "failed", Integer)).label("failed"),
                    func.sum(func.cast(GenerationItem.status == "paused", Integer)).label("paused"),
                    func.sum(func.cast(GenerationItem.distribution_status == "pending_publish", Integer)).label("pending_publish"),
                    func.sum(func.cast(GenerationItem.distribution_status == "published", Integer)).label("published"),
                )
                .where(GenerationItem.task_id.in_(task_ids))
                .group_by(GenerationItem.task_id)
            )
            count_result = await db.execute(count_stmt)
            count_map = {row.task_id: row for row in count_result.all()}

            for task in tasks:
                counts = count_map.get(task.id)
                if counts:
                    task._live_counts = {
                        "total_count": int(counts.total or 0),
                        "queued_count": int(counts.queued or 0),
                        "generating_count": int(counts.generating or 0),
                        "completed_count": int(counts.completed or 0),
                        "failed_count": int(counts.failed or 0),
                        "paused_count": int(counts.paused or 0),
                        "pending_publish_count": int(counts.pending_publish or 0),
                        "published_count": int(counts.published or 0),
                    }
                else:
                    task._live_counts = {
                        "total_count": 0, "queued_count": 0, "generating_count": 0,
                        "completed_count": 0, "failed_count": 0, "paused_count": 0,
                        "pending_publish_count": 0, "published_count": 0,
                    }

        return tasks, total

    @staticmethod
    async def get_failed_tasks(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取有失败子任务的任务列表

        Args:
            db: 数据库会话
            owner_admin_id: 创作管理员ID，None表示获取所有数据
            limit: 返回数量限制

        Returns:
            有失败子任务的任务列表（包含失败详情）
        """
        logger.debug("[DashboardService] get_failed_tasks | owner=%s | limit=%s", owner_admin_id, limit)

        # 构建基础查询
        query = select(GenerationTask).where(
            and_(
                GenerationTask.failed_count > 0,
                GenerationTask.status.notin_(['completed', 'cancelled'])
            )
        )

        if owner_admin_id is not None:
            query = query.where(GenerationTask.owner_operator_id == owner_admin_id)

        query = query.options(
            selectinload(GenerationTask.material),
            selectinload(GenerationTask.owner_operator)
        ).order_by(desc(GenerationTask.updated_at)).limit(limit)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 获取每个任务的最新失败子任务的错误信息
        failed_tasks = []
        for task in tasks:
            # 获取该任务下最新失败的一个子任务
            base_filter = [] if owner_admin_id is None else [GenerationItem.owner_operator_id == owner_admin_id]

            failed_item_query = (
                select(GenerationItem)
                .where(
                    and_(
                        GenerationItem.task_id == task.id,
                        GenerationItem.status == 'failed',
                        *base_filter
                    )
                )
                .order_by(desc(GenerationItem.updated_at))
                .limit(1)
            )
            failed_result = await db.execute(failed_item_query)
            failed_item = failed_result.scalar_one_or_none()

            error_msg = failed_item.error_message if failed_item and failed_item.error_message else "未知错误"
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."

            # 获取所属管理员名称
            owner_name = None
            owner_id = None
            if task.owner_operator:
                owner_name = task.owner_operator.nickname
                owner_id = task.owner_operator.id

            failed_tasks.append({
                "id": task.id,
                "name": task.name or (task.material.title if task.material else f"任务#{task.id}"),
                "failed_count": task.failed_count,
                "error": error_msg,
                "owner_admin_id": owner_id,
                "owner_admin_name": owner_name,
                "latest_failed_at": failed_item.updated_at if failed_item else None
            })

        # 过滤掉已清除的告警（按 task_id 过滤，对所有用户生效）
        dismissed_query = select(DashboardAlertDismissal.task_id)
        dismissed_result = await db.execute(dismissed_query)
        dismissed_task_ids = set(dismissed_result.scalars().all())
        if dismissed_task_ids:
            failed_tasks = [t for t in failed_tasks if t["id"] not in dismissed_task_ids]

        return failed_tasks

    @staticmethod
    async def dismiss_alert(
        db: AsyncSession,
        task_id: int
    ) -> bool:
        """
        清除单条告警

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            是否成功
        """
        logger.debug("[DashboardService] dismiss_alert | task_id=%s", task_id)

        # 检查是否已存在
        existing = await db.execute(
            select(DashboardAlertDismissal).where(
                DashboardAlertDismissal.task_id == task_id
            )
        )
        existing_record = existing.scalar_one_or_none()

        if existing_record:
            # 已存在，无需重复插入
            return True

        # 创建新记录
        dismissal = DashboardAlertDismissal(task_id=task_id)
        db.add(dismissal)
        await db.commit()
        return True

    @staticmethod
    async def dismiss_all_alerts(
        db: AsyncSession,
        owner_admin_id: Optional[int] = None
    ) -> int:
        """
        清除所有告警

        Args:
            db: 数据库会话
            owner_admin_id: 创作管理员ID，None表示所有失败任务

        Returns:
            清除的告警数量
        """
        logger.debug("[DashboardService] dismiss_all_alerts | owner_admin_id=%s", owner_admin_id)

        # 获取所有失败任务ID
        tasks_query = select(GenerationTask.id).where(
            and_(
                GenerationTask.failed_count > 0,
                GenerationTask.status.notin_(['completed', 'cancelled'])
            )
        )
        if owner_admin_id is not None:
            tasks_query = tasks_query.where(GenerationTask.owner_operator_id == owner_admin_id)

        tasks_result = await db.execute(tasks_query)
        task_ids = tasks_result.scalars().all()

        if not task_ids:
            return 0

        # 批量插入已清除的记录（忽略已存在的）
        for tid in task_ids:
            existing = await db.execute(
                select(DashboardAlertDismissal).where(
                    DashboardAlertDismissal.task_id == tid
                )
            )
            if not existing.scalar_one_or_none():
                db.add(DashboardAlertDismissal(task_id=tid))

        await db.commit()
        return len(task_ids)

    @staticmethod
    async def get_operator_list(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        获取创作管理员列表（用于超级管理员筛选下拉框）

        Args:
            db: 数据库会话

        Returns:
            创作管理员列表
        """
        logger.debug("[DashboardService] get_operator_list")

        query = select(Operator).where(Operator.status != 'disabled').order_by(Operator.id)
        result = await db.execute(query)
        operators = result.scalars().all()

        return [
            {"id": op.id, "name": op.nickname}
            for op in operators
        ]