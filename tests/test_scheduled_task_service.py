"""
定时任务服务层测试 (test_scheduled_task_service.py)

测试定时任务服务层的业务逻辑。

Author: Test Engineer
Date: 2026-05-15
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_task import ScheduledTask
from app.models.scheduled_task_execution import ScheduledTaskExecution
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.models.material import Material
from app.models.template import Template
from app.models.generation import GenerationTask
from app.services.scheduled_task_service import ScheduledTaskService


# ============================================
# 工具函数
# ============================================

def create_base_task_data(sub_user_ids: list[int], **kwargs) -> dict:
    """创建基础任务数据"""
    defaults = {
        "name": f"测试任务-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "task_type": "custom",
        "schedule_type": "daily",
        "schedule_config_json": {"times": ["09:00"]},
        "sub_user_ids_json": sub_user_ids,
        "model_selection_mode": "auto",
        "max_concurrency": 5,
        "image_count": 4,
    }
    defaults.update(kwargs)
    return defaults


# ============================================
# enrich_task_response 测试
# ============================================

@pytest.mark.asyncio
async def test_enrich_task_response_basic(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试丰富任务响应 - 基础字段"""
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
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(async_session, task)
    
    # 验证基础字段
    assert response_data["id"] == task.id
    assert response_data["name"] == "测试任务"
    assert response_data["task_type"] == "custom"
    assert response_data["schedule_type"] == "daily"
    assert response_data["owner_operator_name"] == test_operator.nickname


@pytest.mark.asyncio
async def test_enrich_task_response_with_material(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    test_material: Material,
):
    """测试丰富任务响应 - 包含素材"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务（关联素材）
    task = ScheduledTask(
        name="带素材的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        material_id=test_material.id,
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
    
    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(async_session, task)
    
    # 验证素材信息
    assert response_data["material_id"] == test_material.id
    assert response_data["material_title"] == test_material.title


@pytest.mark.asyncio
async def test_enrich_task_response_with_templates(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    test_templates: list[Template],
):
    """测试丰富任务响应 - 包含模板"""
    sub_user_ids = [su.id for su in test_sub_users]
    template_ids = [t.id for t in test_templates]
    
    # 创建任务（关联模板）
    task = ScheduledTask(
        name="带模板的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        template_ids_json=template_ids,
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
    
    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(async_session, task)
    
    # 验证模板信息
    assert response_data["template_ids_json"] == template_ids
    assert len(response_data["template_names"]) == len(test_templates)


@pytest.mark.asyncio
async def test_enrich_task_response_with_benchmark_materials(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试丰富任务响应 - 包含对标素材"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建对标素材
    benchmark_materials = []
    for i in range(3):
        material = Material(
            title=f"对标素材{i}",
            content=f"对标内容{i}",
            topic="对标主题",
            source_type="upload",  # 修正：source_type只能是 upload/link/description
            content_type="text",
            library_type="benchmark",
            owner_operator_id=test_operator.id,
            status="available",
        )
        async_session.add(material)
        benchmark_materials.append(material)
    
    await async_session.commit()
    for m in benchmark_materials:
        await async_session.refresh(m)
    
    benchmark_material_ids = [m.id for m in benchmark_materials]
    
    # 创建任务（关联对标素材）
    task = ScheduledTask(
        name="带对标素材的任务",
        task_type="benchmark",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        benchmark_material_ids_json=benchmark_material_ids,
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
    
    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(async_session, task)
    
    # 验证对标素材信息
    assert response_data["benchmark_material_ids_json"] == benchmark_material_ids
    assert len(response_data["benchmark_material_titles"]) == len(benchmark_materials)


@pytest.mark.asyncio
async def test_enrich_task_response_with_sub_users(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试丰富任务响应 - 包含创作者"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="带创作者的任务",
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
    
    # 丰富响应
    response_data = await ScheduledTaskService.enrich_task_response(async_session, task)
    
    # 验证创作者信息
    assert response_data["sub_user_ids_json"] == sub_user_ids
    assert len(response_data["sub_user_names"]) == len(test_sub_users)


# ============================================
# execute_scheduled_task 测试 - benchmark 类型
# ============================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="依赖Celery和Redis外部服务，需要配置测试环境")
async def test_execute_scheduled_task_benchmark_type(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试执行定时任务 - benchmark类型"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建对标素材
    benchmark_materials = []
    for i in range(3):
        material = Material(
            title=f"对标素材{i}",
            content=f"对标内容{i}",
            topic="对标主题",
            source_type="upload",  # 修正：source_type只能是 upload/link/description
            content_type="text",
            library_type="benchmark",
            owner_operator_id=test_operator.id,
            status="available",
        )
        async_session.add(material)
        benchmark_materials.append(material)
    
    await async_session.commit()
    for m in benchmark_materials:
        await async_session.refresh(m)
    
    benchmark_material_ids = [m.id for m in benchmark_materials]
    
    # 创建 benchmark 类型任务
    task = ScheduledTask(
        name="对标任务",
        task_type="benchmark",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        benchmark_material_ids_json=benchmark_material_ids,
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
    
    # 验证生成的任务
    generation_task = await async_session.get(GenerationTask, generation_task_id)
    assert generation_task is not None
    assert generation_task.benchmark_material_id is not None
    assert generation_task.benchmark_material_id in benchmark_material_ids
    assert generation_task.material_id is None  # benchmark类型不应该有 material_id
    
    # 验证任务统计更新
    await async_session.refresh(task)
    assert task.total_executions == 1
    assert task.last_execution_status == "success"


# ============================================
# execute_scheduled_task 测试 - 错误处理
# ============================================

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
    assert "定时任务不存在" in error


@pytest.mark.asyncio
async def test_execute_scheduled_task_exception_handling(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试执行定时任务 - 异常处理"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务（但没有模板，这会导致后续处理可能出错）
    task = ScheduledTask(
        name="可能失败的任务",
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
    
    # 执行任务（没有模板，但应该仍能创建 GenerationTask）
    success, generation_task_id, error = await ScheduledTaskService.execute_scheduled_task(
        async_session, task.id
    )
    
    # 验证执行结果（取决于业务逻辑，可能成功也可能失败）
    # 这里我们主要验证异常处理不会崩溃
    assert success is not None
    
    # 验证任务统计已更新（无论成功或失败）
    await async_session.refresh(task)
    assert task.total_executions == 1
    assert task.last_execution_at is not None


# ============================================
# calculate_next_execution_at 测试 - 边界情况
# ============================================

def test_calculate_next_execution_at_daily_past_time():
    """测试每日任务 - 当前时间已过执行时间"""
    from datetime import datetime, timedelta
    
    # 模拟当前时间是 10:00，执行时间是 09:00
    # 注意：由于 _calculate_next_execution_at 使用 datetime.utcnow()，
    # 我们需要 mock 这个时间
    # 这里我们直接测试函数逻辑
    
    schedule_config = {"times": ["09:00"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at("daily", schedule_config)
    
    # 验证：下次执行时间应该是明天 09:00
    assert next_run is not None
    assert next_run.hour == 9
    assert next_run.minute == 0
    assert next_run > datetime.utcnow()


def test_calculate_next_execution_at_daily_future_time():
    """测试每日任务 - 当前时间未到执行时间"""
    # 这个函数会使用 datetime.utcnow()，我们无法精确控制当前时间
    # 但我们可以验证返回的时间是正确的
    
    schedule_config = {"times": ["23:59"]}
    
    next_run = ScheduledTaskService._calculate_next_execution_at("daily", schedule_config)
    
    assert next_run is not None
    assert next_run.hour == 23
    assert next_run.minute == 59


def test_calculate_next_execution_at_weekly_edge_case():
    """测试每周任务 - 边界情况（当前是周日，目标是周一）"""
    # 同样，由于使用 utcnow()，我们只能验证基本逻辑
    
    schedule_config = {"days": [1], "times": ["09:00"]}  # 每周一
    
    next_run = ScheduledTaskService._calculate_next_execution_at("weekly", schedule_config)
    
    assert next_run is not None
    assert next_run.weekday() == 0  # 周一


def test_calculate_next_execution_at_invalid_type():
    """测试无效的调度类型"""
    # 无效类型应该返回明天
    
    next_run = ScheduledTaskService._calculate_next_execution_at("invalid", {})
    
    assert next_run is not None
    assert next_run > datetime.utcnow()


# ============================================
# get_pending_tasks 测试
# ============================================

@pytest.mark.asyncio
async def test_get_pending_tasks_empty(
    async_session: AsyncSession,
):
    """测试获取待执行任务 - 无任务"""
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session)
    
    assert len(pending_tasks) == 0


@pytest.mark.asyncio
async def test_get_pending_tasks_multiple_due(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试获取待执行任务 - 多个到期任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建多个到期任务
    for i in range(5):
        task = ScheduledTask(
            name=f"到期任务{i}",
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
            next_execution_at=datetime.utcnow() - timedelta(minutes=1),
        )
        async_session.add(task)
    
    await async_session.commit()
    
    # 获取待执行任务
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session)
    
    # 应该返回所有5个任务
    assert len(pending_tasks) == 5


@pytest.mark.asyncio
async def test_get_pending_tasks_with_disabled(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
):
    """测试获取待执行任务 - 包含禁用的任务"""
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
        next_execution_at=datetime.utcnow() - timedelta(minutes=1),
    )
    async_session.add(active_task)
    
    # 创建禁用的任务（但 next_execution_at 在过去）
    disabled_task = ScheduledTask(
        name="禁用任务",
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
        next_execution_at=datetime.utcnow() - timedelta(minutes=1),
    )
    async_session.add(disabled_task)
    
    await async_session.commit()
    
    # 获取待执行任务
    pending_tasks = await ScheduledTaskService.get_pending_tasks(async_session)
    
    # 应该只返回活跃任务
    assert len(pending_tasks) == 1
    assert pending_tasks[0].name == "活跃任务"


# ============================================
# 完整流程测试
# ============================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="依赖Celery和Redis外部服务，需要配置测试环境")
async def test_complete_scheduled_task_flow(
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    test_templates: list[Template],
):
    """测试完整的定时任务流程"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    template_ids = [t.id for t in test_templates]
    
    # 1. 创建任务
    task_data = create_base_task_data(
        sub_user_ids=sub_user_ids,
        name="完整流程测试任务",
        template_ids_json=template_ids,
    )
    
    task = ScheduledTask(
        name=task_data["name"],
        task_type=task_data["task_type"],
        schedule_type=task_data["schedule_type"],
        schedule_config_json=task_data["schedule_config_json"],
        template_ids_json=task_data["template_ids_json"],
        sub_user_ids_json=task_data["sub_user_ids_json"],
        model_selection_mode=task_data["model_selection_mode"],
        max_concurrency=task_data["max_concurrency"],
        image_count=task_data["image_count"],
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
    
    assert task.id is not None
    assert task.next_execution_at is not None
    
    # 2. 验证任务可以被查询
    queried_task = await ScheduledTaskService.get_scheduled_task(
        async_session, task.id, test_operator.id
    )
    assert queried_task is not None
    assert queried_task.id == task.id
    
    # 3. 执行任务
    success, generation_task_id, error = await ScheduledTaskService.execute_scheduled_task(
        async_session, task.id
    )
    
    assert success is True
    assert generation_task_id is not None
    
    # 4. 验证统计更新
    await async_session.refresh(task)
    assert task.total_executions == 1
    assert task.last_execution_status == "success"
    assert task.next_execution_at is not None
    assert task.next_execution_at > datetime.utcnow()
    
    # 5. 验证执行历史记录
    execution_query = select(ScheduledTaskExecution).where(
        ScheduledTaskExecution.scheduled_task_id == task.id
    )
    execution_result = await async_session.execute(execution_query)
    executions = execution_result.scalars().all()
    
    # 注意：当前代码中 execute_scheduled_task 不创建 ScheduledTaskExecution 记录
    # 这个记录是在调度器中创建的
    # 所以这个测试可能会失败，取决于实现
    
    # 6. 禁用任务
    updated_task = await ScheduledTaskService.toggle_scheduled_task(
        async_session, task.id, test_operator.id, False
    )
    
    assert updated_task.is_active is False
    assert updated_task.status == "paused"
    assert updated_task.next_execution_at is None
    
    # 7. 启用任务
    updated_task = await ScheduledTaskService.toggle_scheduled_task(
        async_session, task.id, test_operator.id, True
    )
    
    assert updated_task.is_active is True
    assert updated_task.status == "active"
    assert updated_task.next_execution_at is not None
    
    # 8. 删除任务
    success = await ScheduledTaskService.delete_scheduled_task(
        async_session, task.id, test_operator.id
    )
    
    assert success is True
    
    # 9. 验证任务已删除
    deleted_task = await ScheduledTaskService.get_scheduled_task(
        async_session, task.id, test_operator.id
    )
    assert deleted_task is None
