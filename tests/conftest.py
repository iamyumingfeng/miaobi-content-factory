"""
测试配置文件 (conftest.py)

提供 pytest fixtures 和通用测试配置。

关键处理：SQLite 中 BigInteger 不支持 AUTOINCREMENT，
需要将 BigInteger PRIMARY KEY 映射为 INTEGER PRIMARY KEY AUTOINCREMENT。

Author: Claude Code
Date: 2025
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event, text, MetaData, Table, Column, Integer, String, DateTime, Enum as SAEnum, Text, ForeignKey, JSON, Boolean, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "platform_api"))

from app.core.database import Base
from app.core.security import get_password_hash, create_access_token

# 显式导入所有模型
from app.models.user_base import UserBase
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.models.super_admin import SuperAdmin
from app.models.material import Material
from app.models.template import Template
from app.models.scheduled_task import ScheduledTask


# ============================================
# 创建测试应用
# ============================================

def create_test_app():
    """创建测试应用（不触发存储路径创建）"""
    app = FastAPI(title="Test App", version="1.0.0")
    from app.api.v1 import router as api_router
    app.include_router(api_router, prefix="/api/v1")
    
    # 添加异常处理器
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
    from app.core.exceptions import AppException
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理自定义应用异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    
    return app


# ============================================
# 数据库配置 - SQLite兼容性处理
# ============================================

def _patch_bigint_for_sqlite(metadata: MetaData):
    """
    修补 SQLAlchemy Metadata，将所有 BigInteger PRIMARY KEY 替换为 Integer，
    以便在 SQLite 中正确支持 AUTOINCREMENT。
    """
    from sqlalchemy import BigInteger
    for table in metadata.sorted_tables:
        for col in table.primary_key.columns:
            if isinstance(col.type, BigInteger):
                col.type = Integer()
        # 同时替换所有 BigInteger 外键列，避免类型不匹配
        for col in table.columns:
            if isinstance(col.type, BigInteger):
                col.type = Integer()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """创建异步数据库引擎（SQLite 内存数据库）"""
    # 在创建表之前，修补 BigInteger → Integer
    _patch_bigint_for_sqlite(Base.metadata)
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建异步数据库会话"""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    test_app = create_test_app()
    
    from app.core.database import get_async_db
    
    async def override_get_async_db():
        yield async_session
    
    test_app.dependency_overrides[get_async_db] = override_get_async_db
    
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    test_app.dependency_overrides.clear()


# ============================================
# 用户 Fixtures
# ============================================

@pytest_asyncio.fixture(scope="function")
async def test_operator(async_session: AsyncSession) -> Operator:
    """创建测试创作管理员"""
    operator = Operator(
        userid="test_operator",
        nickname="测试创作管理员",
        hashed_password=get_password_hash("test123456"),
        status="online",
    )
    async_session.add(operator)
    await async_session.commit()
    await async_session.refresh(operator)
    return operator


@pytest_asyncio.fixture(scope="function")
async def test_operator2(async_session: AsyncSession) -> Operator:
    """创建第二个测试创作管理员（用于权限测试）"""
    operator = Operator(
        userid="test_operator2",
        nickname="测试创作管理员2",
        hashed_password=get_password_hash("test123456"),
        status="online",
    )
    async_session.add(operator)
    await async_session.commit()
    await async_session.refresh(operator)
    return operator


@pytest_asyncio.fixture(scope="function")
async def test_sub_users(async_session: AsyncSession, test_operator: Operator) -> list[SubUser]:
    """创建测试创作者"""
    sub_users = []
    for i in range(3):
        sub_user = SubUser(
            userid=f"test_sub_user_{i}",
            nickname=f"测试创作者{i}",
            hashed_password=get_password_hash("test123456"),
            owner_operator_id=test_operator.id,
            status="online",
        )
        async_session.add(sub_user)
        sub_users.append(sub_user)
    
    await async_session.commit()
    
    for sub_user in sub_users:
        await async_session.refresh(sub_user)
    
    return sub_users


@pytest_asyncio.fixture(scope="function")
async def test_material(async_session: AsyncSession, test_operator: Operator) -> Material:
    """创建测试素材"""
    material = Material(
        title="测试素材",
        content="这是一个测试素材的内容",
        topic="测试主题",
        source_type="upload",
        content_type="text",
        library_type="creation",
        owner_operator_id=test_operator.id,
        status="available",
    )
    async_session.add(material)
    await async_session.commit()
    await async_session.refresh(material)
    return material


@pytest_asyncio.fixture(scope="function")
async def test_templates(async_session: AsyncSession, test_operator: Operator) -> list[Template]:
    """创建测试模板"""
    templates = []
    for i in range(3):
        template = Template(
            name=f"测试模板{i}",
            product_name=f"测试产品{i}",
            content_type="text",
            owner_operator_id=test_operator.id,
            status="enabled",
        )
        async_session.add(template)
        templates.append(template)
    
    await async_session.commit()
    
    for template in templates:
        await async_session.refresh(template)
    
    return templates


# ============================================
# Token Fixtures
# ============================================

@pytest.fixture(scope="function")
def operator_token(test_operator: Operator) -> str:
    """生成创作管理员 token"""
    token_data = {
        "sub": str(test_operator.id),
        "user_type": "operator",
    }
    return create_access_token(data=token_data)


@pytest.fixture(scope="function")
def operator2_token(test_operator2: Operator) -> str:
    """生成第二个创作管理员 token"""
    token_data = {
        "sub": str(test_operator2.id),
        "user_type": "operator",
    }
    return create_access_token(data=token_data)


@pytest.fixture(scope="function")
def super_admin_token() -> str:
    """生成超级管理员 token"""
    token_data = {
        "sub": "1",
        "user_type": "super_admin",
    }
    return create_access_token(data=token_data)


# ============================================
# 工具函数
# ============================================

def get_auth_headers(token: str) -> dict:
    """获取认证 headers"""
    return {"Authorization": f"Bearer {token}"}


def create_task_data(
    sub_user_ids: list[int],
    schedule_type: str = "daily",
    schedule_config: dict = None,
) -> dict:
    """创建定时任务数据"""
    if schedule_config is None:
        if schedule_type == "daily":
            schedule_config = {"times": ["09:00", "18:00"]}
        else:
            schedule_config = {"days": [1, 3, 5], "times": ["09:00"]}
    
    return {
        "name": f"测试定时任务-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "task_type": "custom",
        "schedule_type": schedule_type,
        "schedule_config_json": schedule_config,
        "sub_user_ids_json": sub_user_ids,
        "model_selection_mode": "auto",
        "max_concurrency": 5,
        "image_count": 4,
    }
