"""
AIGC趋势分析服务 (trend_analysis_service.py)

提供趋势分析相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from calendar import monthrange
from sqlalchemy import select, and_, or_, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GenerationTask, GenerationItem, SubUser, Operator

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    """
    趋势分析服务类
    """

    @staticmethod
    def _get_date_range(
        start_date: Optional[date],
        end_date: Optional[date],
        default_days: int = 30
    ) -> Tuple[date, date]:
        """
        获取日期范围

        Args:
            start_date: 开始日期
            end_date: 结束日期
            default_days: 默认天数

        Returns:
            (开始日期, 结束日期)
        """
        today = datetime.utcnow().date()
        if end_date is None:
            end_date = today
        if start_date is None:
            start_date = end_date - timedelta(days=default_days - 1)
        return start_date, end_date

    @staticmethod
    def _build_operator_filter(
        owner_admin_id: Optional[int],
        filter_operator_id: Optional[int],
        is_super_admin: bool
    ) -> List[Any]:
        """
        构建创作管理员过滤条件

        Args:
            owner_admin_id: 当前用户所属创作管理员ID
            filter_operator_id: 筛选的创作管理员ID
            is_super_admin: 是否超级管理员

        Returns:
            过滤条件列表
        """
        if is_super_admin:
            if filter_operator_id is not None:
                return [GenerationItem.owner_operator_id == filter_operator_id]
            return []
        else:
            return [GenerationItem.owner_operator_id == owner_admin_id]

    @staticmethod
    def _calculate_comparison(
        current: int,
        previous: int
    ) -> Dict[str, Any]:
        """
        计算对比数据

        Args:
            current: 当前值
            previous: 上期值

        Returns:
            对比数据字典
        """
        change = current - previous
        change_rate = (change / previous * 100) if previous > 0 else (100.0 if current > 0 else 0.0)
        return {
            "current": current,
            "previous": previous,
            "change": change,
            "change_rate": round(change_rate, 2)
        }

    @staticmethod
    async def get_generation_trend(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        is_super_admin: bool,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        dimension: str = "day",
        compare_type: str = "none",
        content_type: str = "all",
        filter_operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取内容生成趋势

        Args:
            db: 数据库会话
            owner_admin_id: 当前用户所属创作管理员ID
            is_super_admin: 是否超级管理员
            start_date: 开始日期
            end_date: 结束日期
            dimension: 时间维度 (day/week/month)
            compare_type: 对比类型 (none/chain/year)
            content_type: 内容类型 (all/image_text/video)
            filter_operator_id: 筛选的创作管理员ID

        Returns:
            生成趋势数据
        """
        logger.debug("[TrendAnalysisService] get_generation_trend | owner=%s | start=%s | end=%s | dim=%s | compare=%s | content=%s",
                    owner_admin_id, start_date, end_date, dimension, compare_type, content_type)

        start_date, end_date = TrendAnalysisService._get_date_range(start_date, end_date)
        operator_filter = TrendAnalysisService._build_operator_filter(owner_admin_id, filter_operator_id, is_super_admin)

        # 构建基础查询条件
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        base_conditions = operator_filter + [
            GenerationItem.created_at >= range_start,
            GenerationItem.created_at < range_end
        ]

        # 按时间维度聚合
        if dimension == "month":
            # 按月聚合 (MySQL)
            query = select(
                func.date_format(GenerationItem.created_at, '%Y-%m-01').label('period'),
                func.count(GenerationItem.id).label('generated'),
                func.sum(case((GenerationItem.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((GenerationItem.status == 'failed', 1), else_=0)).label('failed')
            ).where(and_(*base_conditions)).group_by(
                func.date_format(GenerationItem.created_at, '%Y-%m-01')
            ).order_by(func.date_format(GenerationItem.created_at, '%Y-%m-01'))

            result = await db.execute(query)
            rows = result.all()

            data = []
            for row in rows:
                period = row.period
                if isinstance(period, datetime):
                    period_str = period.strftime("%Y-%m")
                else:
                    period_str = str(period)[:7]
                generated = row.generated or 0
                completed = row.completed or 0
                failed = row.failed or 0
                success_rate = (completed / generated * 100) if generated > 0 else 0

                data.append({
                    "date": period_str,
                    "generated": generated,
                    "distributed": 0,
                    "published": 0,
                    "success_rate": round(success_rate, 2)
                })

            total = sum(item["generated"] for item in data)
            avg_daily = total / max(len(data), 1)
            max_daily = max((item["generated"] for item in data), default=0)

        elif dimension == "week":
            # 按周聚合 (MySQL: %Y-%u gives year-week format)
            query = select(
                func.date_format(GenerationItem.created_at, '%Y-%u').label('period'),
                func.count(GenerationItem.id).label('generated'),
                func.sum(case((GenerationItem.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((GenerationItem.status == 'failed', 1), else_=0)).label('failed')
            ).where(and_(*base_conditions)).group_by(
                func.date_format(GenerationItem.created_at, '%Y-%u')
            ).order_by(func.date_format(GenerationItem.created_at, '%Y-%u'))

            result = await db.execute(query)
            rows = result.all()

            data = []
            for row in rows:
                period = row.period
                if isinstance(period, datetime):
                    period_str = period.strftime("%Y-W%W")
                else:
                    period_str = str(period)
                generated = row.generated or 0
                completed = row.completed or 0
                success_rate = (completed / generated * 100) if generated > 0 else 0

                data.append({
                    "date": period_str,
                    "generated": generated,
                    "distributed": 0,
                    "published": 0,
                    "success_rate": round(success_rate, 2)
                })

            total = sum(item["generated"] for item in data)
            avg_daily = total / max(len(data), 1)
            max_daily = max((item["generated"] for item in data), default=0)

        else:
            # 按天聚合（优化后 - 单个聚合查询, MySQL）
            query = select(
                func.date(GenerationItem.created_at).label('period'),
                func.count(GenerationItem.id).label('generated'),
                func.sum(case((GenerationItem.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((GenerationItem.status == 'failed', 1), else_=0)).label('failed')
            ).where(and_(*base_conditions)).group_by(
                func.date(GenerationItem.created_at)
            ).order_by(func.date(GenerationItem.created_at))

            result = await db.execute(query)
            rows = result.all()

            # 构建日期到数据的映射
            period_data = {}
            for row in rows:
                period = row.period
                if isinstance(period, datetime):
                    period_str = period.strftime("%Y-%m-%d")
                else:
                    period_str = str(period)[:10]
                generated = row.generated or 0
                completed = row.completed or 0
                success_rate = (completed / generated * 100) if generated > 0 else 0

                period_data[period_str] = {
                    "generated": generated,
                    "completed": completed,
                    "success_rate": round(success_rate, 2)
                }

            # 填充所有日期（包括没有数据的日期）
            data = []
            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                if date_str in period_data:
                    item = period_data[date_str]
                    data.append({
                        "date": date_str,
                        "generated": item["generated"],
                        "distributed": 0,
                        "published": 0,
                        "success_rate": item["success_rate"]
                    })
                else:
                    data.append({
                        "date": date_str,
                        "generated": 0,
                        "distributed": 0,
                        "published": 0,
                        "success_rate": 0
                    })
                current += timedelta(days=1)

            total = sum(item["generated"] for item in data)
            avg_daily = total / max(len(data), 1)
            max_daily = max((item["generated"] for item in data), default=0)

        # 计算对比数据
        compare = None
        if compare_type != "none":
            if compare_type == "year":
                # 同比：去年同期
                prev_start = start_date - timedelta(days=365)
                prev_end = end_date - timedelta(days=365)
            else:
                # 环比：上一周期
                period_days = (end_date - start_date).days + 1
                prev_start = start_date - timedelta(days=period_days)
                prev_end = start_date - timedelta(days=1)

            prev_total = await TrendAnalysisService._get_generation_count(
                db, operator_filter, prev_start, prev_end, dimension
            )
            compare = TrendAnalysisService._calculate_comparison(total, prev_total)

        return {
            "data": data,
            "total": total,
            "avg_daily": round(avg_daily, 2),
            "max_daily": max_daily,
            "compare": compare
        }

    @staticmethod
    async def _get_generation_count(
        db: AsyncSession,
        operator_filter: List[Any],
        start_date: date,
        end_date: date,
        dimension: str
    ) -> int:
        """
        获取指定时间范围内的生成数量

        Args:
            db: 数据库会话
            operator_filter: 创作管理员过滤条件
            start_date: 开始日期
            end_date: 结束日期
            dimension: 时间维度

        Returns:
            生成数量
        """
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        conditions = operator_filter + [
            GenerationItem.created_at >= range_start,
            GenerationItem.created_at < range_end
        ]

        query = select(func.count(GenerationItem.id)).where(and_(*conditions))
        return await db.scalar(query) or 0

    @staticmethod
    async def get_distribution_trend(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        is_super_admin: bool,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        dimension: str = "day",
        compare_type: str = "none",
        content_type: str = "all",
        filter_operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取内容分发趋势

        Args:
            db: 数据库会话
            owner_admin_id: 当前用户所属创作管理员ID
            is_super_admin: 是否超级管理员
            start_date: 开始日期
            end_date: 结束日期
            dimension: 时间维度 (day/week/month)
            compare_type: 对比类型 (none/chain/year)
            content_type: 内容类型 (all/image_text/video)
            filter_operator_id: 筛选的创作管理员ID

        Returns:
            分发趋势数据
        """
        logger.debug("[TrendAnalysisService] get_distribution_trend | owner=%s | start=%s | end=%s | dim=%s | compare=%s",
                    owner_admin_id, start_date, end_date, dimension, compare_type)

        start_date, end_date = TrendAnalysisService._get_date_range(start_date, end_date)
        operator_filter = TrendAnalysisService._build_operator_filter(owner_admin_id, filter_operator_id, is_super_admin)

        # 构建基础查询条件
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        # 分发条件（基于 distributed_at 字段）
        distributed_base_conditions = operator_filter + [
            GenerationItem.distributed_at >= range_start,
            GenerationItem.distributed_at < range_end
        ]

        # 发布条件（基于 confirmed_at 字段）
        published_base_conditions = operator_filter + [
            GenerationItem.confirmed_at >= range_start,
            GenerationItem.confirmed_at < range_end
        ]

        if dimension == "month":
            # 按月聚合 (MySQL)
            distributed_query = select(
                func.date_format(GenerationItem.distributed_at, '%Y-%m-01').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*distributed_base_conditions)).group_by(
                func.date_format(GenerationItem.distributed_at, '%Y-%m-01')
            ).order_by(func.date_format(GenerationItem.distributed_at, '%Y-%m-01'))

            published_query = select(
                func.date_format(GenerationItem.confirmed_at, '%Y-%m-01').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_base_conditions)).group_by(
                func.date_format(GenerationItem.confirmed_at, '%Y-%m-01')
            ).order_by(func.date_format(GenerationItem.confirmed_at, '%Y-%m-01'))

            distributed_result = await db.execute(distributed_query)
            published_result = await db.execute(published_query)

            distributed_by_period = {row.period.strftime("%Y-%m") if isinstance(row.period, datetime) else str(row.period)[:7]: row.count for row in distributed_result.all()}
            published_by_period = {row.period.strftime("%Y-%m") if isinstance(row.period, datetime) else str(row.period)[:7]: row.count for row in published_result.all()}

            data = []
            current = start_date.replace(day=1)
            while current <= end_date:
                period_str = current.strftime("%Y-%m")
                distributed = distributed_by_period.get(period_str, 0)
                published = published_by_period.get(period_str, 0)

                data.append({
                    "date": period_str,
                    "generated": 0,
                    "distributed": distributed,
                    "published": published,
                    "success_rate": round((published / distributed * 100) if distributed > 0 else 0, 2)
                })

                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        elif dimension == "week":
            # 按周聚合 (MySQL: %Y-%u gives year-week format)
            distributed_query = select(
                func.date_format(GenerationItem.distributed_at, '%Y-%u').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*distributed_base_conditions)).group_by(
                func.date_format(GenerationItem.distributed_at, '%Y-%u')
            ).order_by(func.date_format(GenerationItem.distributed_at, '%Y-%u'))

            published_query = select(
                func.date_format(GenerationItem.confirmed_at, '%Y-%u').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_base_conditions)).group_by(
                func.date_format(GenerationItem.confirmed_at, '%Y-%u')
            ).order_by(func.date_format(GenerationItem.confirmed_at, '%Y-%u'))

            distributed_result = await db.execute(distributed_query)
            published_result = await db.execute(published_query)

            distributed_by_period = {str(row.period): row.count for row in distributed_result.all()}
            published_by_period = {str(row.period): row.count for row in published_result.all()}

            data = []
            current = start_date - timedelta(days=start_date.weekday())
            while current <= end_date:
                period_str = current.strftime("%Y-%u")
                distributed = distributed_by_period.get(period_str, 0)
                published = published_by_period.get(period_str, 0)

                data.append({
                    "date": period_str,
                    "generated": 0,
                    "distributed": distributed,
                    "published": published,
                    "success_rate": round((published / distributed * 100) if distributed > 0 else 0, 2)
                })

                current += timedelta(days=7)

        else:
            # 按天聚合（优化后 - 单个聚合查询, MySQL）
            distributed_query = select(
                func.date(GenerationItem.distributed_at).label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*distributed_base_conditions)).group_by(
                func.date(GenerationItem.distributed_at)
            ).order_by(func.date(GenerationItem.distributed_at))

            published_query = select(
                func.date(GenerationItem.confirmed_at).label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_base_conditions)).group_by(
                func.date(GenerationItem.confirmed_at)
            ).order_by(func.date(GenerationItem.confirmed_at))

            distributed_result = await db.execute(distributed_query)
            published_result = await db.execute(published_query)

            distributed_by_period = {}
            for row in distributed_result.all():
                if isinstance(row.period, datetime):
                    period_str = row.period.strftime("%Y-%m-%d")
                else:
                    period_str = str(row.period)[:10]
                distributed_by_period[period_str] = row.count

            published_by_period = {}
            for row in published_result.all():
                if isinstance(row.period, datetime):
                    period_str = row.period.strftime("%Y-%m-%d")
                else:
                    period_str = str(row.period)[:10]
                published_by_period[period_str] = row.count

            # 填充所有日期
            data = []
            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                distributed = distributed_by_period.get(date_str, 0)
                published = published_by_period.get(date_str, 0)

                data.append({
                    "date": date_str,
                    "generated": 0,
                    "distributed": distributed,
                    "published": published,
                    "success_rate": round((published / distributed * 100) if distributed > 0 else 0, 2)
                })

                current += timedelta(days=1)

        total_distributed = sum(item["distributed"] for item in data)
        total_published = sum(item["published"] for item in data)
        distribution_rate = (total_published / total_distributed * 100) if total_distributed > 0 else 0

        # 计算对比数据
        distributed_compare = None
        published_compare = None

        if compare_type != "none":
            if compare_type == "year":
                prev_start = start_date - timedelta(days=365)
                prev_end = end_date - timedelta(days=365)
            else:
                period_days = (end_date - start_date).days + 1
                prev_start = start_date - timedelta(days=period_days)
                prev_end = start_date - timedelta(days=1)

            prev_distributed, prev_published = await TrendAnalysisService._get_distribution_stats(
                db, operator_filter,
                datetime.combine(prev_start, datetime.min.time()),
                datetime.combine(prev_end, datetime.max.time())
            )

            distributed_compare = TrendAnalysisService._calculate_comparison(total_distributed, prev_distributed)
            published_compare = TrendAnalysisService._calculate_comparison(total_published, prev_published)

        return {
            "data": data,
            "total_distributed": total_distributed,
            "total_published": total_published,
            "distribution_rate": round(distribution_rate, 2),
            "publish_rate": round((total_published / total_distributed * 100) if total_distributed > 0 else 0, 2),
            "distributed_compare": distributed_compare,
            "published_compare": published_compare
        }

    @staticmethod
    async def _get_distribution_stats(
        db: AsyncSession,
        operator_filter: List[Any],
        start: datetime,
        end: datetime
    ) -> Tuple[int, int]:
        """
        获取指定时间范围内的分发和发布统计

        Args:
            db: 数据库会话
            operator_filter: 创作管理员过滤条件
            start: 开始时间
            end: 结束时间

        Returns:
            (分发数量, 发布数量)
        """
        # 分发数量
        distributed_conditions = operator_filter + [
            GenerationItem.distributed_at >= start,
            GenerationItem.distributed_at <= end
        ]
        distributed_query = select(func.count(GenerationItem.id)).where(and_(*distributed_conditions))
        distributed = await db.scalar(distributed_query) or 0

        # 发布数量
        published_conditions = operator_filter + [
            GenerationItem.confirmed_at >= start,
            GenerationItem.confirmed_at <= end
        ]
        published_query = select(func.count(GenerationItem.id)).where(and_(*published_conditions))
        published = await db.scalar(published_query) or 0

        return distributed, published

    @staticmethod
    async def get_operator_trend(
        db: AsyncSession,
        owner_admin_id: Optional[int],
        is_super_admin: bool,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filter_operator_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取各创作管理员的生成趋势

        Args:
            db: 数据库会话
            owner_admin_id: 当前用户所属创作管理员ID
            is_super_admin: 是否超级管理员
            start_date: 开始日期
            end_date: 结束日期
            filter_operator_id: 筛选的创作管理员ID

        Returns:
            各创作管理员趋势数据列表
        """
        logger.debug("[TrendAnalysisService] get_operator_trend | owner=%s | start=%s | end=%s",
                    owner_admin_id, start_date, end_date)

        start_date, end_date = TrendAnalysisService._get_date_range(start_date, end_date)
        operator_filter = TrendAnalysisService._build_operator_filter(owner_admin_id, filter_operator_id, is_super_admin)

        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        # 按创作管理员聚合
        query = (
            select(
                GenerationItem.owner_operator_id,
                func.count(GenerationItem.id).label('generated'),
                func.sum(case((GenerationItem.distributed_at.isnot(None), 1), else_=0)).label('distributed'),
                func.sum(case((GenerationItem.confirmed_at.isnot(None), 1), else_=0)).label('published')
            )
            .where(and_(
                *operator_filter,
                GenerationItem.created_at >= range_start,
                GenerationItem.created_at < range_end
            ))
            .group_by(GenerationItem.owner_operator_id)
            .order_by(desc('generated'))
        )

        result = await db.execute(query)
        rows = result.all()

        # 获取创作管理员名称
        operator_ids = [row.owner_operator_id for row in rows if row.owner_operator_id]
        operators_query = select(Operator.id, Operator.nickname).where(Operator.id.in_(operator_ids))
        operators_result = await db.execute(operators_query)
        operator_names = {row.id: row.nickname for row in operators_result.all()}

        data = []
        for row in rows:
            data.append({
                "operator_id": row.owner_operator_id,
                "operator_name": operator_names.get(row.owner_operator_id, f"管理员{row.owner_operator_id}"),
                "generated": row.generated or 0,
                "distributed": row.distributed or 0,
                "published": row.published or 0
            })

        return data

    @staticmethod
    async def get_publish_trend(
        db: AsyncSession,
        user_type: str,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        dimension: str = "day",
        compare_type: str = "none",
        filter_operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取内容发布趋势（合并生成和发布）

        管理员视角：按 owner_operator_id 统计生成和发布
        创作者视角：按 sub_user_id 统计接收和发布

        Args:
            db: 数据库会话
            user_type: 用户类型 (super_admin/operator/sub_user)
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            dimension: 时间维度 (day/week/month)
            compare_type: 对比类型 (none/chain/year)
            filter_operator_id: 筛选的创作管理员ID（仅超级管理员）

        Returns:
            发布趋势数据
        """
        logger.debug("[TrendAnalysisService] get_publish_trend | user_type=%s | user_id=%s | start=%s | end=%s | dim=%s",
                    user_type, user_id, start_date, end_date, dimension)

        start_date, end_date = TrendAnalysisService._get_date_range(start_date, end_date)

        # 构建基础查询条件
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        # 根据用户类型构建过滤条件
        if user_type == "sub_user":
            # 创作者：按 sub_user_id 过滤
            base_filter = [GenerationItem.sub_user_id == user_id]
        elif user_type == "super_admin":
            # 超级管理员：可选按 filter_operator_id 过滤，否则全部
            if filter_operator_id:
                base_filter = [GenerationItem.owner_operator_id == filter_operator_id]
            else:
                base_filter = []
        else:
            # 创作管理员：按 owner_operator_id 过滤
            base_filter = [GenerationItem.owner_operator_id == user_id]

        # 生成条件（基于 created_at，创作者视角实际是"接收"时间）
        generated_conditions = base_filter + [
            GenerationItem.created_at >= range_start,
            GenerationItem.created_at < range_end
        ]

        # 发布条件（基于 confirmed_at）
        published_conditions = base_filter + [
            GenerationItem.confirmed_at >= range_start,
            GenerationItem.confirmed_at < range_end,
            GenerationItem.confirmed_at.isnot(None)
        ]

        if dimension == "month":
            # 按月聚合 (MySQL)
            generated_query = select(
                func.date_format(GenerationItem.created_at, '%Y-%m-01').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*generated_conditions)).group_by(
                func.date_format(GenerationItem.created_at, '%Y-%m-01')
            ).order_by(func.date_format(GenerationItem.created_at, '%Y-%m-01'))

            published_query = select(
                func.date_format(GenerationItem.confirmed_at, '%Y-%m-01').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_conditions)).group_by(
                func.date_format(GenerationItem.confirmed_at, '%Y-%m-01')
            ).order_by(func.date_format(GenerationItem.confirmed_at, '%Y-%m-01'))

            generated_result = await db.execute(generated_query)
            published_result = await db.execute(published_query)

            generated_by_period = {}
            for row in generated_result.all():
                period = row.period
                if isinstance(period, datetime):
                    period_str = period.strftime("%Y-%m")
                else:
                    period_str = str(period)[:7]
                generated_by_period[period_str] = row.count

            published_by_period = {}
            for row in published_result.all():
                period = row.period
                if isinstance(period, datetime):
                    period_str = period.strftime("%Y-%m")
                else:
                    period_str = str(period)[:7]
                published_by_period[period_str] = row.count

            # 构建数据
            data = []
            current = start_date.replace(day=1)
            while current <= end_date:
                period_str = current.strftime("%Y-%m")
                generated = generated_by_period.get(period_str, 0)
                published = published_by_period.get(period_str, 0)
                success_rate = (published / generated * 100) if generated > 0 else 0

                data.append({
                    "date": period_str,
                    "generated": generated,
                    "distributed": 0,
                    "published": published,
                    "success_rate": round(success_rate, 2)
                })

                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        elif dimension == "week":
            # 按周聚合 (MySQL: %Y-%u)
            generated_query = select(
                func.date_format(GenerationItem.created_at, '%Y-%u').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*generated_conditions)).group_by(
                func.date_format(GenerationItem.created_at, '%Y-%u')
            ).order_by(func.date_format(GenerationItem.created_at, '%Y-%u'))

            published_query = select(
                func.date_format(GenerationItem.confirmed_at, '%Y-%u').label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_conditions)).group_by(
                func.date_format(GenerationItem.confirmed_at, '%Y-%u')
            ).order_by(func.date_format(GenerationItem.confirmed_at, '%Y-%u'))

            generated_result = await db.execute(generated_query)
            published_result = await db.execute(published_query)

            generated_by_period = {str(row.period): row.count for row in generated_result.all()}
            published_by_period = {str(row.period): row.count for row in published_result.all()}

            # 构建数据
            data = []
            current = start_date - timedelta(days=start_date.weekday())
            while current <= end_date:
                period_str = current.strftime("%Y-%u")
                generated = generated_by_period.get(period_str, 0)
                published = published_by_period.get(period_str, 0)
                success_rate = (published / generated * 100) if generated > 0 else 0

                data.append({
                    "date": period_str,
                    "generated": generated,
                    "distributed": 0,
                    "published": published,
                    "success_rate": round(success_rate, 2)
                })

                current += timedelta(days=7)

        else:
            # 按天聚合
            generated_query = select(
                func.date(GenerationItem.created_at).label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*generated_conditions)).group_by(
                func.date(GenerationItem.created_at)
            ).order_by(func.date(GenerationItem.created_at))

            published_query = select(
                func.date(GenerationItem.confirmed_at).label('period'),
                func.count(GenerationItem.id).label('count')
            ).where(and_(*published_conditions)).group_by(
                func.date(GenerationItem.confirmed_at)
            ).order_by(func.date(GenerationItem.confirmed_at))

            generated_result = await db.execute(generated_query)
            published_result = await db.execute(published_query)

            generated_by_period = {}
            for row in generated_result.all():
                if isinstance(row.period, datetime):
                    period_str = row.period.strftime("%Y-%m-%d")
                else:
                    period_str = str(row.period)[:10]
                generated_by_period[period_str] = row.count

            published_by_period = {}
            for row in published_result.all():
                if isinstance(row.period, datetime):
                    period_str = row.period.strftime("%Y-%m-%d")
                else:
                    period_str = str(row.period)[:10]
                published_by_period[period_str] = row.count

            # 填充所有日期
            data = []
            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                generated = generated_by_period.get(date_str, 0)
                published = published_by_period.get(date_str, 0)
                success_rate = (published / generated * 100) if generated > 0 else 0

                data.append({
                    "date": date_str,
                    "generated": generated,
                    "distributed": 0,
                    "published": published,
                    "success_rate": round(success_rate, 2)
                })

                current += timedelta(days=1)

        total_generated = sum(item["generated"] for item in data)
        total_published = sum(item["published"] for item in data)
        success_rate = (total_published / total_generated * 100) if total_generated > 0 else 0

        # 计算对比数据
        generated_compare = None
        published_compare = None

        if compare_type != "none":
            if compare_type == "year":
                prev_start = start_date - timedelta(days=365)
                prev_end = end_date - timedelta(days=365)
            else:
                period_days = (end_date - start_date).days + 1
                prev_start = start_date - timedelta(days=period_days)
                prev_end = start_date - timedelta(days=1)

            prev_generated, prev_published = await TrendAnalysisService._get_publish_stats(
                db, base_filter,
                datetime.combine(prev_start, datetime.min.time()),
                datetime.combine(prev_end, datetime.max.time())
            )

            generated_compare = TrendAnalysisService._calculate_comparison(total_generated, prev_generated)
            published_compare = TrendAnalysisService._calculate_comparison(total_published, prev_published)

        return {
            "data": data,
            "total_generated": total_generated,
            "total_published": total_published,
            "success_rate": round(success_rate, 2),
            "generated_compare": generated_compare,
            "published_compare": published_compare
        }

    @staticmethod
    async def _get_publish_stats(
        db: AsyncSession,
        base_filter: List[Any],
        start: datetime,
        end: datetime
    ) -> Tuple[int, int]:
        """
        获取指定时间范围内的生成和发布统计

        Args:
            db: 数据库会话
            base_filter: 基础过滤条件
            start: 开始时间
            end: 结束时间

        Returns:
            (生成数量, 发布数量)
        """
        # 生成数量
        generated_conditions = base_filter + [
            GenerationItem.created_at >= start,
            GenerationItem.created_at <= end
        ]
        generated_query = select(func.count(GenerationItem.id)).where(and_(*generated_conditions))
        generated = await db.scalar(generated_query) or 0

        # 发布数量
        published_conditions = base_filter + [
            GenerationItem.confirmed_at >= start,
            GenerationItem.confirmed_at <= end,
            GenerationItem.confirmed_at.isnot(None)
        ]
        published_query = select(func.count(GenerationItem.id)).where(and_(*published_conditions))
        published = await db.scalar(published_query) or 0

        return generated, published

    @staticmethod
    async def get_filter_options(
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取筛选选项

        Args:
            db: 数据库会话

        Returns:
            筛选选项
        """
        # 获取创作管理员列表
        operators_query = select(Operator.id, Operator.nickname).where(Operator.status != 'disabled').order_by(Operator.id)
        operators_result = await db.execute(operators_query)
        operators = [{"id": row.id, "name": row.nickname} for row in operators_result.all()]

        return {
            "operators": operators,
            "content_types": [
                {"value": "all", "label": "全部"},
                {"value": "image_text", "label": "图文"},
                {"value": "video", "label": "视频"}
            ],
            "dimensions": [
                {"value": "day", "label": "按天"},
                {"value": "week", "label": "按周"},
                {"value": "month", "label": "按月"}
            ]
        }