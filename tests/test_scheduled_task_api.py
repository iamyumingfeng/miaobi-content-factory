"""
定时任务 API 测试 (test_scheduled_task_api.py)

测试定时任务的所有 API 接口。

Author: Claude Code
Date: 2025
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_task import ScheduledTask
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.models.material import Material
from app.models.template import Template


# ============================================
# 工具函数（本地定义，避免导入问题）
# ============================================

def get_auth_headers(token: str) -> dict:
    """获取认证 headers"""
    return {"Authorization": f"Bearer {token}"}


def create_task_data(
    sub_user_ids: list[int],
    schedule_type: str = "daily",
    schedule_config: dict = None,
    material_id: int = None,
    template_ids: list[int] = None,
    benchmark_material_ids: list[int] = None,
) -> dict:
    """创建定时任务数据"""
    from datetime import datetime
    
    if schedule_config is None:
        if schedule_type == "daily":
            schedule_config = {"times": ["09:00", "18:00"]}
        else:
            schedule_config = {"days": [1, 3, 5], "times": ["09:00"]}
    
    data = {
        "name": f"测试定时任务-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "task_type": "custom",
        "schedule_type": schedule_type,
        "schedule_config_json": schedule_config,
        "sub_user_ids_json": sub_user_ids,
        "model_selection_mode": "auto",
        "max_concurrency": 5,
        "image_count": 4,
    }
    
    if material_id is not None:
        data["material_id"] = material_id
    
    if template_ids is not None:
        data["template_ids_json"] = template_ids
    
    if benchmark_material_ids is not None:
        data["benchmark_material_ids_json"] = benchmark_material_ids
    
    return data


# ============================================
# 创建定时任务测试
# ============================================

@pytest.mark.asyncio
async def test_create_scheduled_task_success(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试成功创建定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    task_data = create_task_data(sub_user_ids)
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # 验证返回数据
    assert data["name"] == task_data["name"]
    assert data["task_type"] == "custom"
    assert data["schedule_type"] == "daily"
    assert data["is_active"] is True
    assert data["status"] == "active"
    assert data["total_executions"] == 0
    assert data["next_execution_at"] is not None
    
    # 验证数据库
    task = await async_session.get(ScheduledTask, data["id"])
    assert task is not None
    assert task.name == task_data["name"]
    assert task.owner_operator_id == test_operator.id


@pytest.mark.asyncio
async def test_create_scheduled_task_with_material_and_templates(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    test_material: Material,
    test_templates: list[Template],
    operator_token: str,
):
    """测试创建带素材和模板的定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    template_ids = [t.id for t in test_templates]
    
    task_data = create_task_data(
        sub_user_ids=sub_user_ids,
        material_id=test_material.id,
        template_ids=template_ids,
    )
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["material_id"] == test_material.id
    assert data["material_title"] == test_material.title
    assert data["template_ids_json"] == template_ids
    assert len(data["template_names"]) == len(test_templates)


@pytest.mark.asyncio
async def test_create_weekly_scheduled_task(
    client: AsyncClient,
    async_session: AsyncSession,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试创建每周执行的定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    task_data = create_task_data(
        sub_user_ids=sub_user_ids,
        schedule_type="weekly",
        schedule_config={"days": [1, 3, 5], "times": ["09:00", "18:00"]},
    )
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["schedule_type"] == "weekly"
    assert data["schedule_config_json"]["days"] == [1, 3, 5]
    assert data["schedule_config_json"]["times"] == ["09:00", "18:00"]


@pytest.mark.asyncio
async def test_create_scheduled_task_without_auth(
    client: AsyncClient,
    test_sub_users: list[SubUser],
):
    """测试未认证时创建定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    task_data = create_task_data(sub_user_ids)
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
    )
    
    # 打印调试信息
    print(f"DEBUG: status_code = {response.status_code}")
    print(f"DEBUG: response body = {response.text}")
    
    # 应该返回 401 或 403
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_scheduled_task_by_super_admin(
    client: AsyncClient,
    test_sub_users: list[SubUser],
    super_admin_token: str,
):
    """测试超级管理员创建定时任务（应该被拒绝）"""
    sub_user_ids = [su.id for su in test_sub_users]
    task_data = create_task_data(sub_user_ids)
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(super_admin_token),
    )
    
    # 超级管理员不能创建定时任务
    assert response.status_code == 403


# ============================================
# 获取定时任务列表测试
# ============================================

@pytest.mark.asyncio
async def test_list_scheduled_tasks_success(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试获取定时任务列表"""
    # 创建多个定时任务
    sub_user_ids = [su.id for su in test_sub_users]
    for i in range(3):
        task_data = create_task_data(sub_user_ids)
        task_data["name"] = f"测试任务{i}"
        
        task = ScheduledTask(
            name=task_data["name"],
            task_type=task_data["task_type"],
            schedule_type=task_data["schedule_type"],
            schedule_config_json=task_data["schedule_config_json"],
            sub_user_ids_json=task_data["sub_user_ids_json"],
            model_selection_mode=task_data["model_selection_mode"],
            max_concurrency=task_data["max_concurrency"],
            image_count=task_data["image_count"],
            owner_operator_id=test_operator.id,
            is_active=True,
            status="active",
        )
        async_session.add(task)
    
    await async_session.commit()
    
    # 获取列表
    response = await client.get(
        "/api/v1/scheduled-tasks",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_scheduled_tasks_with_pagination(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试分页获取定时任务列表"""
    # 创建多个定时任务
    sub_user_ids = [su.id for su in test_sub_users]
    for i in range(5):
        task = ScheduledTask(
            name=f"测试任务{i}",
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
    
    # 测试第一页
    response = await client.get(
        "/api/v1/scheduled-tasks?page=1&limit=2",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_list_scheduled_tasks_with_filter(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试筛选定时任务列表"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建活跃任务
    task1 = ScheduledTask(
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
    )
    async_session.add(task1)
    
    # 创建暂停任务
    task2 = ScheduledTask(
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
    )
    async_session.add(task2)
    
    await async_session.commit()
    
    # 筛选活跃任务
    response = await client.get(
        "/api/v1/scheduled-tasks?status=active",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["total"] == 1
    assert data["items"][0]["name"] == "活跃任务"


@pytest.mark.asyncio
async def test_list_scheduled_tasks_isolation(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_operator2: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
    operator2_token: str,
):
    """测试创作管理员只能看到自己的任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建创作管理员1的任务
    task1 = ScheduledTask(
        name="创作管理员1的任务",
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
    async_session.add(task1)
    
    # 创建创作管理员2的任务
    task2 = ScheduledTask(
        name="创作管理员2的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator2.id,
        is_active=True,
        status="active",
    )
    async_session.add(task2)
    
    await async_session.commit()
    
    # 创作管理员1查看列表
    response = await client.get(
        "/api/v1/scheduled-tasks",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # 应该只看到自己的任务
    assert data["total"] == 1
    assert data["items"][0]["name"] == "创作管理员1的任务"
    
    # 创作管理员2查看列表
    response = await client.get(
        "/api/v1/scheduled-tasks",
        headers=get_auth_headers(operator2_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # 应该只看到自己的任务
    assert data["total"] == 1
    assert data["items"][0]["name"] == "创作管理员2的任务"


# ============================================
# 获取定时任务详情测试
# ============================================

@pytest.mark.asyncio
async def test_get_scheduled_task_detail(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试获取定时任务详情"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
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
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 获取详情
    response = await client.get(
        f"/api/v1/scheduled-tasks/{task.id}",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["id"] == task.id
    assert data["name"] == "测试任务"
    assert data["schedule_config_json"]["times"] == ["09:00", "18:00"]


@pytest.mark.asyncio
async def test_get_scheduled_task_not_found(
    client: AsyncClient,
    operator_token: str,
):
    """测试获取不存在的定时任务"""
    response = await client.get(
        "/api/v1/scheduled-tasks/99999",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scheduled_task_no_permission(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator2: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试获取其他创作管理员的定时任务（应该失败）"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建属于创作管理员2的任务
    task = ScheduledTask(
        name="创作管理员2的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator2.id,
        is_active=True,
        status="active",
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 创作管理员1尝试获取
    response = await client.get(
        f"/api/v1/scheduled-tasks/{task.id}",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 404


# ============================================
# 更新定时任务测试
# ============================================

@pytest.mark.asyncio
async def test_update_scheduled_task_success(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试更新定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="原始任务名",
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
    
    # 更新任务
    update_data = {
        "name": "更新后的任务名",
        "schedule_config_json": {"times": ["10:00", "20:00"]},
        "max_concurrency": 10,
    }
    
    response = await client.put(
        f"/api/v1/scheduled-tasks/{task.id}",
        json=update_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["name"] == "更新后的任务名"
    assert data["schedule_config_json"]["times"] == ["10:00", "20:00"]
    assert data["max_concurrency"] == 10
    
    # 验证数据库
    await async_session.refresh(task)
    assert task.name == "更新后的任务名"


@pytest.mark.asyncio
async def test_update_scheduled_task_change_schedule_type(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试更新定时任务的调度类型"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建每日任务
    task = ScheduledTask(
        name="每日任务",
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
    
    # 更新为每周任务
    update_data = {
        "schedule_type": "weekly",
        "schedule_config_json": {"days": [1, 3, 5], "times": ["09:00"]},
    }
    
    response = await client.put(
        f"/api/v1/scheduled-tasks/{task.id}",
        json=update_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["schedule_type"] == "weekly"
    assert data["schedule_config_json"]["days"] == [1, 3, 5]


@pytest.mark.asyncio
async def test_update_scheduled_task_by_super_admin(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    super_admin_token: str,
):
    """测试超级管理员更新定时任务（应该成功）"""
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
    
    # 尝试更新
    response = await client.put(
        f"/api/v1/scheduled-tasks/{task.id}",
        json={"name": "新名称"},
        headers=get_auth_headers(super_admin_token),
    )
    
    # 超级管理员可以更新定时任务
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "新名称"


# ============================================
# 删除定时任务测试
# ============================================

@pytest.mark.asyncio
async def test_delete_scheduled_task_success(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试删除定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="待删除任务",
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
    
    task_id = task.id
    
    # 删除任务
    response = await client.delete(
        f"/api/v1/scheduled-tasks/{task_id}",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    
    # 验证数据库中已删除
    deleted_task = await async_session.get(ScheduledTask, task_id)
    assert deleted_task is None


@pytest.mark.asyncio
async def test_delete_scheduled_task_not_found(
    client: AsyncClient,
    operator_token: str,
):
    """测试删除不存在的定时任务"""
    response = await client.delete(
        "/api/v1/scheduled-tasks/99999",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheduled_task_no_permission(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator2: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试删除其他创作管理员的定时任务（应该失败）"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建属于创作管理员2的任务
    task = ScheduledTask(
        name="创作管理员2的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator2.id,
        is_active=True,
        status="active",
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 创作管理员1尝试删除
    response = await client.delete(
        f"/api/v1/scheduled-tasks/{task.id}",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 404


# ============================================
# 启用/禁用定时任务测试
# ============================================

@pytest.mark.asyncio
async def test_toggle_scheduled_task_disable(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试禁用定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="待禁用任务",
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
    
    # 禁用任务
    response = await client.post(
        f"/api/v1/scheduled-tasks/{task.id}/toggle?is_active=false",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["is_active"] is False
    assert data["status"] == "paused"
    assert data["next_execution_at"] is None


@pytest.mark.asyncio
async def test_toggle_scheduled_task_enable(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试启用定时任务"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建禁用的任务
    task = ScheduledTask(
        name="待启用任务",
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
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 启用任务
    response = await client.post(
        f"/api/v1/scheduled-tasks/{task.id}/toggle?is_active=true",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["is_active"] is True
    assert data["status"] == "active"
    assert data["next_execution_at"] is not None


# ============================================
# 立即执行定时任务测试
# ============================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="依赖Celery和Redis外部服务，需要配置测试环境")
async def test_execute_scheduled_task_now_success(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试立即执行定时任务"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建任务
    task = ScheduledTask(
        name="待执行任务",
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
    
    # 立即执行
    response = await client.post(
        f"/api/v1/scheduled-tasks/{task.id}/execute",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # 应该返回生成任务ID
    assert "generation_task_id" in data
    
    # 验证任务统计更新（执行成功后应该更新）
    await async_session.refresh(task)
    assert task.total_executions == 1
    assert task.successful_executions == 1  # 执行成功后应该变成1
    assert task.last_execution_at is not None
    assert task.last_execution_status == "success"


@pytest.mark.asyncio
async def test_execute_scheduled_task_now_no_permission(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator2: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试立即执行其他创作管理员的定时任务（应该失败）"""
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建属于创作管理员2的任务
    task = ScheduledTask(
        name="创作管理员2的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator2.id,
        is_active=True,
        status="active",
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)
    
    # 创作管理员1尝试执行
    response = await client.post(
        f"/api/v1/scheduled-tasks/{task.id}/execute",
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 404


# ============================================
# Benchmark 任务类型测试
# ============================================

@pytest.mark.asyncio
async def test_create_benchmark_scheduled_task(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_sub_users: list[SubUser],
    operator_token: str,
):
    """测试创建对标任务"""
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
    
    # 创建对标任务
    task_data = {
        "name": "对标测试任务",
        "task_type": "benchmark",
        "schedule_type": "daily",
        "schedule_config_json": {"times": ["09:00"]},
        "benchmark_material_ids_json": benchmark_material_ids,
        "sub_user_ids_json": sub_user_ids,
        "model_selection_mode": "auto",
        "max_concurrency": 5,
        "image_count": 4,
    }
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(operator_token),
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["task_type"] == "benchmark"
    assert data["benchmark_material_ids_json"] == benchmark_material_ids


@pytest.mark.asyncio
async def test_create_scheduled_task_without_sub_users(
    client: AsyncClient,
    operator_token: str,
):
    """测试创建定时任务但不选创作者（应该成功，创作者可选）"""
    task_data = {
        "name": "无创作者任务",
        "task_type": "custom",
        "schedule_type": "daily",
        "schedule_config_json": {"times": ["09:00"]},
        "sub_user_ids_json": [],  # 空列表
        "model_selection_mode": "auto",
        "max_concurrency": 5,
        "image_count": 4,
    }
    
    response = await client.post(
        "/api/v1/scheduled-tasks",
        json=task_data,
        headers=get_auth_headers(operator_token),
    )
    
    # API允许创建不带创作者的任务
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "无创作者任务"
    assert data["sub_user_ids_json"] == []


# ============================================
# 超级管理员测试
# ============================================

@pytest.mark.asyncio
async def test_super_admin_list_all_tasks(
    client: AsyncClient,
    async_session: AsyncSession,
    test_operator: Operator,
    test_operator2: Operator,
    test_sub_users: list[SubUser],
    super_admin_token: str,
):
    """测试超级管理员查看所有任务"""
    from app.services.scheduled_task_service import ScheduledTaskService
    
    sub_user_ids = [su.id for su in test_sub_users]
    
    # 创建创作管理员1的任务
    task1 = ScheduledTask(
        name="创作管理员1的任务",
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
    task1.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task1.schedule_type, task1.schedule_config_json
    )
    async_session.add(task1)
    
    # 创建创作管理员2的任务
    task2 = ScheduledTask(
        name="创作管理员2的任务",
        task_type="custom",
        schedule_type="daily",
        schedule_config_json={"times": ["09:00"]},
        sub_user_ids_json=sub_user_ids,
        model_selection_mode="auto",
        max_concurrency=5,
        image_count=4,
        owner_operator_id=test_operator2.id,
        is_active=True,
        status="active",
    )
    task2.next_execution_at = ScheduledTaskService._calculate_next_execution_at(
        task2.schedule_type, task2.schedule_config_json
    )
    async_session.add(task2)
    
    await async_session.commit()
    
    # 超级管理员查看所有任务（不指定 operator_id）
    response = await client.get(
        "/api/v1/scheduled-tasks",
        headers=get_auth_headers(super_admin_token),
    )
    
    # 应该返回所有任务
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) >= 2
