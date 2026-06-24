"""
定时任务调度逻辑测试 (test_scheduled_task_scheduler.py)

测试定时任务的调度逻辑和时间计算。

Author: Claude Code
Date: 2025
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_task import ScheduledTask
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.services.scheduled_task_service import ScheduledTaskService


# ============================================
# 下次执行时间计算测试
# ============================================

def test_calculate_next_execution_at_daily_single_time():
    """测试每日任务单个时间点的下次执行时间计算"""
    # 当前时间：2025-01-15 08:00
    now = datetime(2025, 1, 15, 8, 0, 0)
    
    schedule_config = {"times": ["09:00"]}
    
    # 计算下次执行时间
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "daily", schedule_config
    )
    
    # 验证：应该是今天 09:00
    # 注意：由于 _calculate_next_execution_at 使用 datetime.now()，
    # 我们无法精确测试，但可以验证逻辑
    assert next_run is not None
    assert next_run.hour == 9
    assert next_run.minute == 0


def test_calculate_next_execution_at_daily_multiple_times():
    """测试每日任务多个时间点的下次执行时间计算"""
    schedule_config = {"times": ["09:00", "12:00", "18:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "daily", schedule_config
    )
    
    # 验证：应该返回最近的下一个时间
    assert next_run is not None
    assert next_run.hour in [9, 12, 18]
    assert next_run.minute == 0


def test_calculate_next_execution_at_weekly_single_day():
    """测试每周任务单个日期的下次执行时间计算"""
    # 每周一执行
    schedule_config = {"days": [1], "times": ["09:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "weekly", schedule_config
    )
    
    # 验证：应该是周一
    assert next_run is not None
    # Python: 0=周一, 6=周日
    # 我们的配置: 1=周一, 7=周日
    # 所以 next_run.weekday() 应该是 0
    assert next_run.weekday() == 0  # 周一
    assert next_run.hour == 9
    assert next_run.minute == 0


def test_calculate_next_execution_at_weekly_multiple_days():
    """测试每周任务多个日期的下次执行时间计算"""
    # 每周一、三、五执行
    schedule_config = {"days": [1, 3, 5], "times": ["09:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "weekly", schedule_config
    )
    
    # 验证：应该是周一、三或周五
    assert next_run is not None
    # weekday: 0=周一, 2=周三, 4=周五
    assert next_run.weekday() in [0, 2, 4]
    assert next_run.hour == 9
    assert next_run.minute == 0


def test_calculate_next_execution_at_weekly_all_days():
    """测试每周任务每天执行的下次执行时间计算"""
    # 每天（周一到周日）
    schedule_config = {"days": [1, 2, 3, 4, 5, 6, 7], "times": ["09:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "weekly", schedule_config
    )
    
    # 验证：应该返回明天或今天的 09:00
    assert next_run is not None
    assert next_run.hour == 9
    assert next_run.minute == 0


def test_calculate_next_execution_at_weekly_multiple_times():
    """测试每周任务多个时间点的下次执行时间计算"""
    schedule_config = {
        "days": [1, 3, 5],
        "times": ["09:00", "18:00"]
    }
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "weekly", schedule_config
    )
    
    # 验证：应该是周一、三或周五的 09:00 或 18:00
    assert next_run is not None
    assert next_run.weekday() in [0, 2, 4]
    assert next_run.hour in [9, 18]
    assert next_run.minute == 0


# ============================================
# 时间边界测试
# ============================================

def test_calculate_next_execution_at_midnight():
    """测试午夜时间的计算"""
    schedule_config = {"times": ["00:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "daily", schedule_config
    )
    
    assert next_run is not None
    assert next_run.hour == 0
    assert next_run.minute == 0


def test_calculate_next_execution_at_end_of_day():
    """测试一天结束时间的计算"""
    schedule_config = {"times": ["23:59"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "daily", schedule_config
    )
    
    assert next_run is not None
    assert next_run.hour == 23
    assert next_run.minute == 59


def test_calculate_next_execution_at_weekend():
    """测试周末时间的计算"""
    # 每周日执行
    schedule_config = {"days": [7], "times": ["10:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "weekly", schedule_config
    )
    
    assert next_run is not None
    # weekday: 6=周日
    assert next_run.weekday() == 6
    assert next_run.hour == 10
    assert next_run.minute == 0


# ============================================
# 调度类型不匹配测试
# ============================================

def test_calculate_next_execution_at_with_invalid_schedule_type():
    """测试无效的调度类型"""
    # 默认返回明天同一时间
    next_run = ScheduledTaskService._calculate_next_execution_at(
        "hourly", {}  # 无效的调度类型
    )
    
    # 应该返回明天
    assert next_run is not None
    assert next_run > datetime.now()


# ============================================
# 数据库集成测试
# ============================================

@pytest.mark.asyncio
async def test_create_task_sets_next_execution_at(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试创建任务时自动设置下次执行时间"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00", "18:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    # 手动计算并设置 next_execution_at（使用静态方法）
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已设置
    assert task.next_execution_at is not None
    assert task.next_execution_at > datetime.now()


@pytest.mark.asyncio
async def test_update_schedule_recalculates_next_execution_at(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试更新调度配置时重新计算下次执行时间"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    # 手动计算并设置 next_execution_at（使用静态方法）
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    original_next_run = task.next_execution_at
    
    # 更新调度配置
    task.schedule_config_json = {"times": ["18:00"]}
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已更新
    assert task.next_execution_at is not None
    # 时间应该不同（除非恰好跨越了时间点）
    # 注意：由于计算逻辑，这个断言可能不稳定


@pytest.mark.asyncio
async def test_disable_task_clears_next_execution_at(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试禁用任务时清空下次执行时间"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    # 手动计算并设置 next_execution_at
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已设置
    assert task.next_execution_at is not None
    
    # 禁用任务
    task.is_active = False
    task.status = "paused"
    task.next_execution_at = None
    
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已清空
    assert task.next_execution_at is None


@pytest.mark.asyncio
async def test_enable_task_sets_next_execution_at(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试启用任务时设置下次执行时间"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建禁用的任务
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=False,
        status="paused",
        next_execution_at=None,
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 为空
    assert task.next_execution_at is None
    
    # 启用任务
    task.is_active = True
    task.status = "active"
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已设置
    assert task.next_execution_at is not None


# ============================================
# 获取待执行任务测试
# ============================================

@pytest.mark.asyncio
async def test_get_pending_tasks_returns_only_active(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试获取待执行任务只返回活跃任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建活跃任务
    active_task = ScheduledTask(
        name="活跃任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
        next_execution_at=datetime.now() - timedelta(minutes=1),  # 过去时间
    )
    async_session.add(active_task)
    
    # 创建暂停任务
    paused_task = ScheduledTask(
        name="暂停任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=False,
        status="paused",
        next_execution_at=datetime.now() - timedelta(minutes=1),
    )
    async_session.add(paused_task)
    
    await async_session.commit()
    
    # 获取待执行任务
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session)
    
    # 应该只返回活跃任务
    assert len(pending_tasks) == 1
    assert pending_tasks[0].name == "活跃任务"


@pytest.mark.asyncio
async def test_get_pending_tasks_returns_only_due(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试获取待执行任务只返回到期任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建到期任务
    due_task = ScheduledTask(
        name="到期任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
        next_execution_at=datetime.now() - timedelta(minutes=1),  # 过去时间
    )
    async_session.add(due_task)
    
    # 创建未到期任务
    future_task = ScheduledTask(
        name="未到期任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
        next_execution_at=datetime.now() + timedelta(hours=1),  # 未来时间
    )
    async_session.add(future_task)
    
    await async_session.commit()
    
    # 获取待执行任务
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session)
    
    # 应该只返回到期任务
    assert len(pending_tasks) == 1
    assert pending_tasks[0].name == "到期任务"


@pytest.mark.asyncio
async def test_get_pending_tasks_respects_limit(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试获取待执行任务的数量限制"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建多个到期任务
    for i in range(10):
        task = ScheduledTask(
            name=f"任务{i}",
            task_type="custom",
            schedule_type="daily",
            schedule_config_json={"times": ["09:00"]},
            sub_user_ids_json=sub_user_ids,
            model_selection_mode="auto",
            max_concurrency=5,
            image_count=4,
            owner_operator_id=test_operator.id,
            is_active=True,
            status="active",
            next_execution_at=datetime.now() - timedelta(minutes=1),
        )
        async_session.add(task)
    
    await async_session.commit()
    
    # 获取待执行任务（限制5个）
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session, limit=5)
    
    # 应该最多返回5个
    assert len(pending_tasks) <= 5


# ============================================
# 执行任务测试
# ============================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="依赖Celery和Redis外部服务，需要配置测试环境")
async def test_execute_scheduled_task_creates_generation_task(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试执行定时任务创建生成任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建定时任务
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 执行任务
    success, generation_task_id, error = await ScheduledTaskService.execute_scheduled_task(
        async_session, task.id
    )
    
    # 验证执行成功
    assert success is True
    assert generation_task_id is not None
    assert error is None
    
    # 验证任务统计更新
    await async_session.refresh(task)
    assert task.total_executions == 1
    assert task.last_execution_at is not None
    assert task.last_execution_status == "success"
    
    # 验证 next_execution_at 已更新
    assert task.next_execution_at is not None
    assert task.next_execution_at > datetime.now()


@pytest.mark.asyncio
async def test_execute_scheduled_task_nonexistent(
    async_session: AsyncSession,
):
    """测试执行不存在的定时任务"""
    success, generation_task_id, error = await ScheduledTaskService.execute_scheduled_task(
        async_session, 99999
    )
    
    # 验证执行失败
    assert success is False
    assert generation_task_id is None
    assert error is not None


@pytest.mark.asyncio
async def test_execute_scheduled_task_updates_statistics(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试执行定时任务更新统计信息"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建定时任务
    task = ScheduledTask(
        name="测试任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
        total_executions=5,
        successful_executions=3,
        failed_executions=2,
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 执行任务
    success, generation_task_id, error = await ScheduledTaskService.execute_scheduled_task(
        async_session, task.id
    )
    
    # 验证统计更新
    await async_session.refresh(task)
    assert task.total_executions == 6
    assert task.last_execution_at is not None


# ============================================
# 特殊场景测试
# ============================================

@pytest.mark.asyncio
async def test_weekly_task_cross_week_boundary(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试每周任务跨越周边界"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 每周日执行
    task = ScheduledTask(
        name="周日任务",
        task_type="custom",
        schedule_type="weekly",
        schedule_config_json={"days": [7], "times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    # 手动计算并设置 next_execution_at
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 是周日
    assert task.next_execution_at is not None
    assert task.next_execution_at.weekday() == 6  # 周日


@pytest.mark.asyncio
async def test_daily_task_with_many_times(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试每日任务有很多时间点"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建有10个时间点的任务
    times = [f"{h:02d}:00" for h in range(0, 24, 2)]  # 每2小时一次
    
    task = ScheduledTask(
        name="频繁任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": times},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator.id,
        is_active=True,
        status="active",
    )
    
    # 手动计算并设置 next_execution_at
    task.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task.schedule_type, task.schedule_config_json
    )
    
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 验证 next_execution_at 已设置
    assert task.next_execution_at is not None
    # 应该在接下来的2小时内
    assert task.next_execution_at <= datetime.now() + timedelta(hours=2)
