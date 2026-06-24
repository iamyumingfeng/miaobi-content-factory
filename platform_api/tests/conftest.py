"""
测试配置和共享 fixtures

Author: Claude Code
Date: 2025
"""

import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, MagicMock

from app.core.config import Settings, get_settings
from app.core.security import create_access_token


@pytest.fixture
def test_settings() -> Settings:
    """测试用配置"""
    return Settings(
        secret_key="test-secret-key-for-testing-only-do-not-use-in-production",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        debug=True,
        access_token_expire_minutes=60,
    )


@pytest.fixture
def mock_settings(test_settings: Settings, monkeypatch) -> Settings:
    """Mock 配置单例"""
    def mock_get_settings():
        return test_settings

    # Mock get_settings 函数
    monkeypatch.setattr("app.core.config.get_settings", mock_get_settings)
    monkeypatch.setattr("app.core.security.get_settings", mock_get_settings)
    
    # Mock security.py 中的模块级 settings 变量
    from app.core import security
    monkeypatch.setattr(security, "settings", test_settings)
    
    return test_settings


@pytest.fixture
def super_admin_token(mock_settings: Settings) -> str:
    """超级管理员测试令牌"""
    return create_access_token(
        data={
            "sub": "1",
            "user_type": "super_admin",
            "userid": "admin_test",
        }
    )


@pytest.fixture
def operator_token(mock_settings: Settings) -> str:
    """创作管理员测试令牌"""
    return create_access_token(
        data={
            "sub": "2",
            "user_type": "operator",
            "userid": "operator_test",
        }
    )


@pytest.fixture
def sub_user_token(mock_settings: Settings) -> str:
    """创作者测试令牌"""
    return create_access_token(
        data={
            "sub": "3",
            "user_type": "sub_user",
            "userid": "subuser_test",
        }
    )


@pytest.fixture
def expired_token(mock_settings: Settings) -> str:
    """已过期的测试令牌"""
    return create_access_token(
        data={
            "sub": "1",
            "user_type": "super_admin",
            "userid": "admin_test",
        },
        expires_delta=timedelta(minutes=-30)
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock 数据库会话"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    session.add_all = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """示例用户数据"""
    return {
        "userid": "test_user_001",
        "nickname": "测试用户",
        "display_name": "自定义昵称",
        "email": "test@example.com",
        "phone": "13800138000",
    }


@pytest.fixture
def sample_template_data() -> Dict[str, Any]:
    """示例模板数据"""
    return {
        "name": "测试模板",
        "description": "这是一个测试模板",
        "platform_id": 1,
        "content_text": "测试内容 {{title}}",
        "variables": '[{"name": "title", "type": "string", "label": "标题"}]',
        "is_public": False,
    }


@pytest.fixture
def sample_material_data() -> Dict[str, Any]:
    """示例素材数据"""
    return {
        "name": "测试素材",
        "description": "这是一个测试素材",
        "type": "image",
        "file_url": "https://example.com/test.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg",
    }


@pytest.fixture
def sample_generation_task_data() -> Dict[str, Any]:
    """示例生成任务数据"""
    return {
        "name": "测试生成任务",
        "template_id": 1,
        "model_platform": "bailian",
        "model_id": "qwen-max",
        "status": "queued",
        "total_count": 10,
        "queued_count": 10,
        "generating_count": 0,
        "completed_count": 0,
        "failed_count": 0,
    }
