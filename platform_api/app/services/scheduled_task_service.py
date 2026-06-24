"""
定时任务服务层 (scheduled_task_service.py)

处理定时任务的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import Material
from app.models.operator import Operator
from app.models.scheduled_task import ScheduledTask
from app.models.scheduled_task_execution import ScheduledTaskExecution
from app.models.sub_user import SubUser
from app.models.template import Template
from app.schemas.scheduled_task import ScheduledTaskCreate, ScheduledTaskUpdate
from app.services.generation_service import GenerationService

logger = logging.getLogger(__name__)


class ScheduledTaskService:
    """
    定时任务服务类
    """

    @staticmethod
    async def list_scheduled_tasks(
        db: AsyncSession,
        owner_operator_id: int,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[ScheduledTask], int]:
        """
        获取定时任务列表

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID（None 表示查询所有）
            page: 页码
            limit: 每页数量
            status: 状态筛选
            task_type: 任务类型筛选
            keyword: 关键词搜索
            is_active: 是否启用筛选

        Returns:
            Tuple[List[ScheduledTask], int]: 任务列表和总数
        """
        # 构建查询条件
        filters = []
        if owner_operator_id is not None:
            filters.append(ScheduledTask.owner_operator_id == owner_operator_id)

        if status:
            filters.append(ScheduledTask.status == status)

        if task_type:
            filters.append(ScheduledTask.task_type == task_type)

        if is_active is not None:
            filters.append(ScheduledTask.is_active == is_active)

        if keyword:
            filters.append(ScheduledTask.name.like(f"%{keyword}%"))

        # 查询总数
        count_query = select(ScheduledTask).where(and_(*filters))
        count_result = await db.execute(count_query)
        total = len(count_result.all())

        # 查询列表（带关联）
        query = (
            select(ScheduledTask)
            .options(
                selectinload(ScheduledTask.owner_operator),
                selectinload(ScheduledTask.material),
            )
            .where(and_(*filters))
            .order_by(ScheduledTask.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await db.execute(query)
        tasks = result.scalars().all()

        return tasks, total

    @staticmethod
    async def get_scheduled_task(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[ScheduledTask]:
        """
        获取定时任务详情

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_operator_id: 创作管理员ID（None 表示超级管理员，不限制所属者）

        Returns:
            Optional[ScheduledTask]: 任务详情
        """
        # 构建查询条件
        conditions = [ScheduledTask.id == task_id]
        if owner_operator_id is not None:
            conditions.append(ScheduledTask.owner_operator_id == owner_operator_id)

        query = (
            select(ScheduledTask)
            .options(
                selectinload(ScheduledTask.owner_operator),
                selectinload(ScheduledTask.material),
            )
            .where(and_(*conditions))
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_scheduled_task(
        db: AsyncSession,
        task_data: ScheduledTaskCreate,
        owner_operator_id: int,
        created_by: Optional[int] = None,
    ) -> ScheduledTask:
        """
        创建定时任务

        Args:
            db: 数据库会话
            task_data: 任务数据
            owner_operator_id: 创作管理员ID
            created_by: 创建者ID

        Returns:
            ScheduledTask: 创建的任务
        """
        # 计算下次执行时间
        next_execution_at = ScheduledTaskService._calculate_next_execution_at(
            task_data.schedule_type, task_data.schedule_config_json
        )

        # 创建任务
        task = ScheduledTask(
            name=task_data.name,
            task_type=task_data.task_type,
            schedule_type=task_data.schedule_type,
            schedule_config_json=task_data.schedule_config_json,
            material_id=task_data.material_id,
            benchmark_material_ids_json=task_data.benchmark_material_ids_json,
            template_ids_json=task_data.template_ids_json,
            sub_user_ids_json=task_data.sub_user_ids_json,
            model_platform=task_data.model_platform,
            model_id=task_data.model_id,
            image_model_platform=task_data.image_model_platform,
            image_model_id=task_data.image_model_id,
            model_selection_mode=task_data.model_selection_mode,
            max_concurrency=task_data.max_concurrency,
            image_count=task_data.image_count,
            variable_values_json=task_data.variable_values_json,
            dedup_enabled=task_data.dedup_enabled,
            dedup_threshold=task_data.dedup_threshold,
            dedup_retry_count=task_data.dedup_retry_count,
            dedup_scope=task_data.dedup_scope,
            image_dedup_enabled=task_data.image_dedup_enabled,
            image_dedup_threshold=task_data.image_dedup_threshold,
            image_dedup_retry_count=task_data.image_dedup_retry_count,
            image_dedup_scope=task_data.image_dedup_scope,
            benchmark_text_enabled=task_data.benchmark_text_enabled,
            benchmark_image_enabled=task_data.benchmark_image_enabled,
            benchmark_image_reference_options=task_data.benchmark_image_reference_options,
            benchmark_image_roles_json=task_data.benchmark_image_roles_json,
            template_product_mapping_json=task_data.template_product_mapping_json,
            is_active=True,
            status="active",
            next_execution_at=next_execution_at,
            owner_operator_id=owner_operator_id,
            created_by=created_by or owner_operator_id,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(
            f"[ScheduledTaskService] 创建定时任务成功 | id={task.id} | name={task.name} | "
            f"schedule_type={task.schedule_type} | next_execution_at={task.next_execution_at}"
        )

        return task

    @staticmethod
    async def update_scheduled_task(
        db: AsyncSession,
        task_id: int,
        task_data: ScheduledTaskUpdate,
        owner_operator_id: int,
    ) -> Optional[ScheduledTask]:
        """
        更新定时任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            task_data: 更新数据
            owner_operator_id: 创作管理员ID

        Returns:
            Optional[ScheduledTask]: 更新后的任务
        """
        # 查询任务
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            return None

        # 更新字段
        update_data = task_data.model_dump(exclude_unset=True)

        # 如果更新了调度配置，重新计算下次执行时间
        if "schedule_type" in update_data or "schedule_config_json" in update_data:
            schedule_type = update_data.get("schedule_type", task.schedule_type)
            schedule_config = update_data.get(
                "schedule_config_json", task.schedule_config_json
            )
            task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
                schedule_type, schedule_config
            )

        # 更新字段
        for field, value in update_data.items():
            setattr(task, field, value)

        await db.commit()
        await db.refresh(task)

        logger.info(
            f"[ScheduledTaskService] 更新定时任务成功 | id={task.id} | name={task.name}"
        )

        return task

    @staticmethod
    async def delete_scheduled_task(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        删除定时任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_operator_id: 创作管理员ID（None 表示超级管理员，不限制所属者）

        Returns:
            bool: 是否删除成功
        """
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            return False

        await db.delete(task)
        await db.commit()

        logger.info(f"[ScheduledTaskService] 删除定时任务成功 | id={task_id}")

        return True

    @staticmethod
    async def toggle_scheduled_task(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: int,
        is_active: bool,
    ) -> Optional[ScheduledTask]:
        """
        启用/禁用定时任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_operator_id: 创作管理员ID
            is_active: 是否启用

        Returns:
            Optional[ScheduledTask]: 更新后的任务
        """
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            return None

        task.is_active = is_active
        task.status = "active" if is_active else "paused"

        # 如果启用，重新计算下次执行时间
        if is_active:
            task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
                task.schedule_type, task.schedule_config_json
            )
        else:
            task.next_execution_at = None

        await db.commit()
        await db.refresh(task)

        logger.info(
            f"[ScheduledTaskService] {'启用' if is_active else '禁用'}定时任务 | "
            f"id={task.id} | name={task.name}"
        )

        return task

    @staticmethod
    async def get_pending_tasks(
        db: AsyncSession,
        limit: int = 100,
    ) -> List[ScheduledTask]:
        """
        获取待执行的定时任务（供调度器使用）

        Args:
            db: 数据库会话
            limit: 最大返回数量

        Returns:
            List[ScheduledTask]: 待执行的任务列表
        """
        now = datetime.now()

        query = (
            select(ScheduledTask)
            .where(
                and_(
                    ScheduledTask.is_active == True,
                    ScheduledTask.status == "active",
                    ScheduledTask.next_execution_at <= now,
                )
            )
            .limit(limit)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def execute_scheduled_task(
        db: AsyncSession,
        task_id: int,
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        执行定时任务（创建 GenerationTask）

        每次执行时，从 template_ids_json 和 benchmark_material_ids_json 中
        各随机选择一个进行组合生成。

        Args:
            db: 数据库会话
            task_id: 定时任务ID

        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (是否成功, 生成的任务ID, 错误信息)
        """
        try:
            # 查询定时任务
            task = await db.get(ScheduledTask, task_id)
            if not task:
                return False, None, f"定时任务不存在：{task_id}"

            # 随机选择模板（如果配置了多个）
            selected_template_id = None
            if task.template_ids_json and len(task.template_ids_json) > 0:
                selected_template_id = random.choice(task.template_ids_json)

            # 随机选择对标素材（如果配置了对标文案且配置了多个）
            selected_benchmark_material_id = None
            if (
                task.task_type == "benchmark"
                and task.benchmark_material_ids_json
                and len(task.benchmark_material_ids_json) > 0
            ):
                selected_benchmark_material_id = random.choice(
                    task.benchmark_material_ids_json
                )

            # 使用 GenerationService.create_generation_task 创建带 items 的生成任务
            template_ids = [selected_template_id] if selected_template_id else None
            sub_user_ids = (
                task.sub_user_ids_json
                if isinstance(task.sub_user_ids_json, list)
                else None
            )

            generation_task = await GenerationService.create_generation_task(
                db=db,
                owner_operator_id=task.owner_operator_id,
                created_by=task.created_by,
                name=f"{task.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                material_id=task.material_id if task.task_type == "custom" else None,
                benchmark_material_id=(
                    selected_benchmark_material_id
                    if task.task_type == "benchmark"
                    else None
                ),
                model_platform=task.model_platform,
                model_id=task.model_id,
                image_model_platform=task.image_model_platform,
                image_model_id=task.image_model_id,
                model_selection_mode=task.model_selection_mode,
                max_concurrency=task.max_concurrency,
                variable_values_json=task.variable_values_json,
                image_count=task.image_count,
                dedup_enabled=task.dedup_enabled,
                dedup_threshold=task.dedup_threshold,
                dedup_retry_count=task.dedup_retry_count,
                dedup_scope=task.dedup_scope,
                image_dedup_enabled=task.image_dedup_enabled,
                image_dedup_threshold=task.image_dedup_threshold,
                image_dedup_retry_count=task.image_dedup_retry_count,
                image_dedup_scope=task.image_dedup_scope,
                benchmark_text_enabled=task.benchmark_text_enabled,
                benchmark_image_enabled=task.benchmark_image_enabled,
                benchmark_image_reference_options=task.benchmark_image_reference_options,
                benchmark_image_roles=task.benchmark_image_roles_json,
                template_product_mapping=task.template_product_mapping_json,
                template_ids=template_ids,
                sub_user_ids=sub_user_ids,
            )

            # 更新定时任务统计（执行中，不加成功数）
            task.total_executions += 1
            # successful_executions 等 generation_task 完成后由回调更新
            task.last_execution_at = datetime.now()
            task.last_execution_status = "running"

            # 创建执行历史记录（状态：running，等 generation_task 完成后再更新）
            import json

            now = datetime.now()
            sub_user_count = (
                len(task.sub_user_ids_json)
                if isinstance(task.sub_user_ids_json, list)
                else 0
            )
            execution = ScheduledTaskExecution(
                scheduled_task_id=task.id,
                generation_task_id=generation_task.id,
                execution_type="manual",
                scheduled_at=now,
                started_at=now,
                completed_at=None,  # 等 generation_task 完成后才设置
                execution_time=now,
                status="running",
                total_items=generation_task.total_count,
                success_items=0,  # 等完成后更新
                failed_items=0,
                execution_details_json=json.dumps(
                    {
                        "selected_template_id": selected_template_id,
                        "selected_benchmark_material_id": selected_benchmark_material_id,
                        "sub_user_count": sub_user_count,
                    }
                ),
            )
            db.add(execution)

            # 计算下次执行时间
            task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
                task.schedule_type, task.schedule_config_json
            )

            await db.commit()

            logger.info(
                f"[ScheduledTaskService] 执行定时任务成功 | scheduled_task_id={task_id} | "
                f"generation_task_id={generation_task.id} | "
                f"selected_template_id={selected_template_id} | "
                f"selected_benchmark_material_id={selected_benchmark_material_id}"
            )

            # 启动生成任务（创建 generation_item 并分派 Celery 任务）
            from app.tasks.generation_tasks import start_generation_task

            start_generation_task.delay(generation_task.id, task.owner_operator_id)
            logger.info(
                f"[ScheduledTaskService] 已触发生成任务启动 | generation_task_id={generation_task.id}"
            )

            return True, generation_task.id, None

        except Exception as e:
            logger.error(
                f"[ScheduledTaskService] 执行定时任务失败 | scheduled_task_id={task_id} | "
                f"error={str(e)}",
                exc_info=True,
            )

            # 更新失败统计
            task = await db.get(ScheduledTask, task_id)
            if task:
                task.failed_executions += 1
                task.last_execution_at = datetime.now()
                task.last_execution_status = "failed"
                task.next_execution_at = (
                    ScheduledTaskService._calculate_next_execution_at(
                        task.schedule_type, task.schedule_config_json
                    )
                )

            # 创建执行历史记录（失败）
            now = datetime.now()
            execution = ScheduledTaskExecution(
                scheduled_task_id=task.id,
                execution_type="manual",
                scheduled_at=now,
                started_at=now,
                completed_at=now,
                execution_time=now,
                status="failed",
                error_message=str(e),
                total_items=0,
                success_items=0,
                failed_items=0,
            )
            db.add(execution)

            await db.commit()

            return False, None, str(e)

    @staticmethod
    def _calculate_next_execution_at(
        schedule_type: str,
        schedule_config: Dict[str, Any],
    ) -> Optional[datetime]:
        """
        计算下次执行时间

        Args:
            schedule_type: 调度类型（daily/weekly/periodic）
            schedule_config: 调度配置

        Returns:
            Optional[datetime]: 下次执行时间，如果不在周期内返回 None
        """
        now = datetime.now()

        if schedule_type == "daily":
            # 每日执行
            times = schedule_config.get("times", ["09:00"])
            # 找到下一个执行时间
            next_times = []
            for time_str in times:
                hour, minute = map(int, time_str.split(":"))
                next_time = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
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

        elif schedule_type == "periodic":
            # 周期执行：在 [start_date, end_date] 范围内每日执行
            from datetime import datetime as dt

            start_date_str = schedule_config.get("start_date")
            end_date_str = schedule_config.get("end_date")
            times = schedule_config.get("times", ["09:00"])

            if not start_date_str or not end_date_str:
                return None

            start_date = dt.strptime(start_date_str, "%Y-%m-%d")
            end_date = dt.strptime(end_date_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )

            # 如果当前时间已超过结束日期，返回 None（周期已结束）
            if now > end_date:
                return None

            # 找到下一个执行时间
            next_times = []
            current_date = max(now, start_date)

            for time_str in times:
                hour, minute = map(int, time_str.split(":"))
                next_time = current_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # 如果计算出的时间已过，推到明天
                if next_time <= now:
                    next_time += timedelta(days=1)

                # 确保在周期范围内
                if next_time <= end_date:
                    next_times.append(next_time)

            if not next_times:
                return None

            return min(next_times)

        # 默认：明天同一时间
        return now + timedelta(days=1)

    @staticmethod
    async def get_task_executions(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: int,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[ScheduledTaskExecution], int]:
        """
        获取定时任务的执行历史

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_operator_id: 创作管理员ID（用于权限验证）
            page: 页码
            limit: 每页数量

        Returns:
            Tuple[List[ScheduledTaskExecution], int]: 执行历史列表和总数
        """
        # 验证任务存在且属于该创作管理员
        task = await ScheduledTaskService.get_scheduled_task(
            db, task_id, owner_operator_id
        )
        if not task:
            return [], 0

        # 查询总数
        from sqlalchemy import func

        count_query = select(func.count(ScheduledTaskExecution.id)).where(
            ScheduledTaskExecution.scheduled_task_id == task_id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # 查询列表（按执行时间倒序）
        query = (
            select(ScheduledTaskExecution)
            .where(ScheduledTaskExecution.scheduled_task_id == task_id)
            .order_by(ScheduledTaskExecution.execution_time.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await db.execute(query)
        executions = result.scalars().all()

        return executions, total

    @staticmethod
    async def enrich_task_response(
        db: AsyncSession,
        task: ScheduledTask,
    ) -> Dict[str, Any]:
        """
        丰富任务响应信息（添加关联对象名称）

        Args:
            db: 数据库会话
            task: 任务对象

        Returns:
            Dict[str, Any]: 丰富的响应数据
        """
        response_data = {
            "id": task.id,
            "name": task.name,
            "task_type": task.task_type,
            "schedule_type": task.schedule_type,
            "schedule_config_json": task.schedule_config_json,
            "material_id": task.material_id,
            "material_title": None,
            "benchmark_material_ids_json": task.benchmark_material_ids_json,
            "benchmark_material_titles": None,
            "template_ids_json": task.template_ids_json,
            "template_names": None,
            "sub_user_ids_json": task.sub_user_ids_json,
            "sub_user_names": None,
            "model_platform": task.model_platform,
            "model_id": task.model_id,
            "image_model_platform": task.image_model_platform,
            "image_model_id": task.image_model_id,
            "model_selection_mode": task.model_selection_mode,
            "max_concurrency": task.max_concurrency,
            "image_count": task.image_count,
            "variable_values_json": task.variable_values_json,
            "dedup_enabled": task.dedup_enabled,
            "dedup_threshold": task.dedup_threshold,
            "dedup_retry_count": task.dedup_retry_count,
            "dedup_scope": task.dedup_scope,
            "image_dedup_enabled": task.image_dedup_enabled,
            "image_dedup_threshold": task.image_dedup_threshold,
            "image_dedup_retry_count": task.image_dedup_retry_count,
            "image_dedup_scope": task.image_dedup_scope,
            "benchmark_text_enabled": task.benchmark_text_enabled,
            "benchmark_image_enabled": task.benchmark_image_enabled,
            "benchmark_image_reference_options": task.benchmark_image_reference_options,
            "benchmark_image_roles_json": task.benchmark_image_roles_json,
            "template_product_mapping_json": task.template_product_mapping_json,
            "is_active": task.is_active,
            "status": task.status,
            "total_executions": task.total_executions,
            "successful_executions": task.successful_executions,
            "failed_executions": task.failed_executions,
            "last_execution_at": task.last_execution_at,
            "last_execution_status": task.last_execution_status,
            "next_execution_at": task.next_execution_at,
            "owner_operator_id": task.owner_operator_id,
            "owner_operator_name": None,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

        # 添加素材名称
        if task.material_id:
            material = await db.get(Material, task.material_id)
            if material:
                response_data["material_title"] = material.title

        # 添加对标素材标题
        if task.benchmark_material_ids_json:
            query = select(Material.title).where(
                Material.id.in_(task.benchmark_material_ids_json)
            )
            result = await db.execute(query)
            benchmark_material_titles = [row[0] for row in result.all()]
            response_data["benchmark_material_titles"] = benchmark_material_titles

        # 添加模板名称
        if task.template_ids_json:
            query = select(Template.name).where(Template.id.in_(task.template_ids_json))
            result = await db.execute(query)
            template_names = [row[0] for row in result.all()]
            response_data["template_names"] = template_names

        # 添加创作者名称
        if task.sub_user_ids_json:
            query = select(SubUser.nickname).where(
                SubUser.id.in_(task.sub_user_ids_json)
            )
            result = await db.execute(query)
            sub_user_names = [row[0] for row in result.all()]
            response_data["sub_user_names"] = sub_user_names

        # 添加创作管理员名称（使用异步查询避免懒加载）
        if task.owner_operator_id:
            query = select(Operator.nickname).where(
                Operator.id == task.owner_operator_id
            )
            result = await db.execute(query)
            owner_operator_name = result.scalar_one_or_none()
            response_data["owner_operator_name"] = owner_operator_name

        return response_data
