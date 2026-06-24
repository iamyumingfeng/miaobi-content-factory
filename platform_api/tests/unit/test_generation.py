"""
内容生成服务测试 (test_generation.py)

Author: Claude Code
Date: 2025
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.generation_service import GenerationService
from app.models import GenerationTask, GenerationItem
from app.core.exceptions import GenerationTaskNotFoundError, GenerationItemNotFoundError


@pytest.mark.asyncio
@pytest.mark.unit
class TestGenerationService:
    """GenerationService 单元测试"""

    # ============================================
    # 测试任务创建
    # ============================================

    async def test_create_generation_task_basic(self) -> None:
        """测试创建基本生成任务"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # 创建模拟的任务对象
        task = GenerationTask(
            id=1,
            material_id=1,
            model_selection_mode="auto",
            max_concurrency=5,
            status="processing",
            total_count=0,
            owner_operator_id=1,
            created_by=1,
        )
        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', 1))

        with patch('app.services.generation_service.GenerationTask', return_value=task):
            result = await GenerationService.create_generation_task(
                db=mock_db,
                owner_operator_id=1,
                created_by=1,
                material_id=1,
                model_selection_mode="auto",
                max_concurrency=5,
            )

        assert result is not None
        assert result.material_id == 1
        assert result.status == "processing"

    # ============================================
    # 测试获取任务列表
    # ============================================

    async def test_list_generation_tasks_empty(self) -> None:
        """测试获取空的任务列表"""
        mock_db = AsyncMock()
        
        # Mock 计数查询结果
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        # Mock items 查询结果
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = []
        
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_items_result])
        
        items, total = await GenerationService.list_generation_tasks(
            db=mock_db,
            owner_operator_id=1,
            page=1,
            limit=20,
        )

        assert total == 0
        assert items == []

    async def test_list_generation_tasks_with_status_filter(self) -> None:
        """测试带状态筛选的任务列表"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute = AsyncMock(return_value=mock_result)

        items, total = await GenerationService.list_generation_tasks(
            db=mock_db,
            owner_operator_id=1,
            status="processing",
            page=1,
            limit=20,
        )

        assert total == 5

    # ============================================
    # 测试获取任务详情
    # ============================================

    async def test_get_generation_task_found(self) -> None:
        """测试获取存在的任务详情"""
        mock_db = AsyncMock()
        task = GenerationTask(
            id=1,
            material_id=1,
            status="processing",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GenerationService.get_generation_task(
            db=mock_db,
            task_id=1,
            owner_operator_id=1,
        )

        assert result is not None
        assert result.id == 1

    async def test_get_generation_task_not_found(self) -> None:
        """测试获取不存在的任务详情"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GenerationService.get_generation_task(
            db=mock_db,
            task_id=999,
            owner_operator_id=1,
        )

        assert result is None

    # ============================================
    # 测试取消任务
    # ============================================

    async def test_cancel_pending_task(self) -> None:
        """测试取消待处理任务"""
        mock_db = AsyncMock()
        task = GenerationTask(
            id=1,
            material_id=1,
            status="pending",
            queued_count=10,
            generating_count=0,
            owner_operator_id=1,
        )
        
        mock_task_result = MagicMock()
        mock_task_result.scalar_one_or_none.return_value = task
        
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = []
        
        mock_db.execute = AsyncMock(side_effect=[mock_task_result, mock_items_result])
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await GenerationService.cancel_generation_task(
            db=mock_db,
            task_id=1,
            owner_operator_id=1,
        )

        assert result.status == "cancelled"

    async def test_cancel_completed_task_raises_error(self) -> None:
        """测试取消已完成任务应抛出错误"""
        mock_db = AsyncMock()
        task = GenerationTask(
            id=1,
            material_id=1,
            status="completed",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="只能取消待处理或处理中的任务"):
            await GenerationService.cancel_generation_task(
                db=mock_db,
                task_id=1,
                owner_operator_id=1,
            )

    # ============================================
    # 测试子任务重试
    # ============================================

    async def test_retry_failed_item(self) -> None:
        """测试重试失败的子任务"""
        mock_db = AsyncMock()
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="failed",
            retry_count=0,
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(GenerationService, 'update_generation_item_status', new_callable=AsyncMock):
            await GenerationService.retry_failed_item(
                db=mock_db,
                item_id=1,
                owner_operator_id=1,
            )

    async def test_retry_non_failed_item_raises_error(self) -> None:
        """测试重试非失败状态的子任务应抛出错误"""
        mock_db = AsyncMock()
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="completed",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="只能重试失败的子任务"):
            await GenerationService.retry_failed_item(
                db=mock_db,
                item_id=1,
                owner_operator_id=1,
            )

    # ============================================
    # 测试子任务暂停/继续
    # ============================================

    async def test_pause_queued_item(self) -> None:
        """测试暂停队列中的子任务"""
        mock_db = AsyncMock()
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="queued",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(GenerationService, 'update_generation_item_status', new_callable=AsyncMock):
            await GenerationService.toggle_pause_item(
                db=mock_db,
                item_id=1,
                owner_operator_id=1,
                pause=True,
            )

    async def test_resume_paused_item(self) -> None:
        """测试继续已暂停的子任务"""
        mock_db = AsyncMock()
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="paused",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(GenerationService, 'update_generation_item_status', new_callable=AsyncMock):
            await GenerationService.toggle_pause_item(
                db=mock_db,
                item_id=1,
                owner_operator_id=1,
                pause=False,
            )

    async def test_pause_completed_item_raises_error(self) -> None:
        """测试暂停已完成的子任务应抛出错误"""
        mock_db = AsyncMock()
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="completed",
            owner_operator_id=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="只能暂停队列中或生成中的子任务"):
            await GenerationService.toggle_pause_item(
                db=mock_db,
                item_id=1,
                owner_operator_id=1,
                pause=True,
            )

    # ============================================
    # 测试批量操作
    # ============================================

    async def test_batch_retry_items_with_ids(self) -> None:
        """测试批量重试指定的子任务"""
        mock_db = AsyncMock()
        
        item1 = GenerationItem(id=1, task_id=1, status="failed", owner_operator_id=1)
        item2 = GenerationItem(id=2, task_id=1, status="failed", owner_operator_id=1)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item1, item2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(GenerationService, 'update_generation_item_status', new_callable=AsyncMock, return_value=item1):
            result = await GenerationService.batch_retry_items(
                db=mock_db,
                item_ids=[1, 2],
                owner_operator_id=1,
            )

        assert len(result) == 2

    async def test_batch_retry_items_without_ids_raises_error(self) -> None:
        """测试批量重试不提供 ID 应抛出错误"""
        mock_db = AsyncMock()

        with pytest.raises(ValueError, match="必须提供 item_ids 或 task_id"):
            await GenerationService.batch_retry_items(
                db=mock_db,
                owner_operator_id=1,
            )

    async def test_batch_pause_items(self) -> None:
        """测试批量暂停子任务"""
        mock_db = AsyncMock()
        
        item1 = GenerationItem(id=1, task_id=1, status="queued", owner_operator_id=1)
        item2 = GenerationItem(id=2, task_id=1, status="generating", owner_operator_id=1)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item1, item2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(GenerationService, 'update_generation_item_status', new_callable=AsyncMock, return_value=item1):
            result = await GenerationService.batch_pause_items(
                db=mock_db,
                item_ids=[1, 2],
                pause=True,
                owner_operator_id=1,
            )

        assert len(result) == 2

    async def test_batch_pause_without_ids_raises_error(self) -> None:
        """测试批量暂停不提供 ID 应抛出错误"""
        mock_db = AsyncMock()

        # 空列表应该触发验证错误
        with pytest.raises(ValueError, match="必须提供 item_ids"):
            await GenerationService.batch_pause_items(
                db=mock_db,
                item_ids=[],  # 空列表
                pause=True,
                owner_operator_id=1,
            )

    # ============================================
    # 测试获取进度日志
    # ============================================

    async def test_get_task_progress_logs(self) -> None:
        """测试获取任务进度日志"""
        mock_db = AsyncMock()
        
        from app.models.generation import GenerationTaskProgressLog
        log1 = GenerationTaskProgressLog(
            id=1,
            task_id=1,
            queued_count=10,
            generating_count=0,
            completed_count=0,
            failed_count=0,
            status="pending",
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [log1]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GenerationService.get_task_progress_logs(
            db=mock_db,
            task_id=1,
            owner_operator_id=1,
            limit=50,
        )

        assert len(result) == 1
        assert result[0].task_id == 1


@pytest.mark.asyncio
@pytest.mark.unit
class TestGenerationTaskModel:
    """GenerationTask 模型测试"""

    def test_task_status_enum_values(self) -> None:
        """测试任务状态枚举值"""
        valid_statuses = ["pending", "processing", "completed", "failed", "cancelled"]
        for status in valid_statuses:
            task = GenerationTask(
                id=1,
                material_id=1,
                status=status,
                model_selection_mode="auto",
                max_concurrency=5,
                total_count=0,
                owner_operator_id=1,
                created_by=1,
            )
            assert task.status == status

    def test_task_repr(self) -> None:
        """测试任务字符串表示"""
        task = GenerationTask(
            id=1,
            material_id=1,
            status="pending",
            model_selection_mode="auto",
            max_concurrency=5,
            total_count=10,
            owner_operator_id=1,
            created_by=1,
        )
        assert "GenerationTask" in repr(task)
        assert "id=1" in repr(task)


@pytest.mark.asyncio
@pytest.mark.unit
class TestGenerationItemModel:
    """GenerationItem 模型测试"""

    def test_item_status_enum_values(self) -> None:
        """测试子任务状态枚举值"""
        valid_statuses = ["queued", "generating", "completed", "failed", "paused"]
        for status in valid_statuses:
            item = GenerationItem(
                id=1,
                task_id=1,
                sub_user_id=1,
                status=status,
                distribution_status="draft",
                owner_operator_id=1,
            )
            assert item.status == status

    def test_item_repr(self) -> None:
        """测试子任务字符串表示"""
        item = GenerationItem(
            id=1,
            task_id=1,
            sub_user_id=1,
            status="queued",
            distribution_status="draft",
            owner_operator_id=1,
        )
        assert "GenerationItem" in repr(item)
        assert "id=1" in repr(item)
