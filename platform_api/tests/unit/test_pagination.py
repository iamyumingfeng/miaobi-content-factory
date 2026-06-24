"""
分页工具模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import List, Tuple, Any
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.pagination import (
    PageParams,
    PaginatedResponse,
    paginate_query,
    create_paginated_response,
)


@pytest.mark.unit
class TestPageParams:
    """PageParams 模型测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = PageParams()
        assert params.page == 1
        assert params.limit == 20

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = PageParams(page=3, limit=50)
        assert params.page == 3
        assert params.limit == 50

    def test_page_minimum_validation(self) -> None:
        """测试页码最小值验证"""
        with pytest.raises(Exception):
            PageParams(page=0)

    def test_limit_minimum_validation(self) -> None:
        """测试每页数量最小值验证"""
        with pytest.raises(Exception):
            PageParams(limit=0)

    def test_limit_maximum_validation(self) -> None:
        """测试每页数量最大值验证"""
        with pytest.raises(Exception):
            PageParams(limit=101)


@pytest.mark.unit
class TestPaginatedResponse:
    """PaginatedResponse 模型测试"""

    def test_paginated_response_creation(self) -> None:
        """测试分页响应创建"""
        items: List[Dict[str, int]] = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse(
            items=items,
            total=10,
            page=1,
            limit=2,
            total_pages=5
        )
        assert response.items == items
        assert response.total == 10
        assert response.page == 1
        assert response.limit == 2
        assert response.total_pages == 5

    def test_model_example(self) -> None:
        """测试模型示例"""
        example = PaginatedResponse.model_config["json_schema_extra"]["example"]
        assert "items" in example
        assert "total" in example
        assert "page" in example
        assert "limit" in example
        assert "total_pages" in example

    def test_empty_response(self) -> None:
        """测试空响应"""
        response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            limit=20,
            total_pages=0
        )
        assert response.items == []
        assert response.total == 0
        assert response.total_pages == 0


@pytest.mark.unit
class TestCreatePaginatedResponse:
    """create_paginated_response 函数测试"""

    def test_create_basic_response(self) -> None:
        """测试创建基本响应"""
        items: List[int] = [1, 2, 3, 4, 5]
        response = create_paginated_response(items, total=50, page=2, limit=10)
        assert isinstance(response, PaginatedResponse)
        assert response.items == items
        assert response.total == 50
        assert response.page == 2
        assert response.limit == 10
        assert response.total_pages == 5

    def test_create_response_exact_page(self) -> None:
        """测试创建正好一页的响应"""
        items: List[int] = [1, 2, 3]
        response = create_paginated_response(items, total=3, page=1, limit=3)
        assert response.total_pages == 1

    def test_create_response_partial_page(self) -> None:
        """测试创建部分页的响应"""
        items: List[int] = [1, 2]
        response = create_paginated_response(items, total=5, page=2, limit=3)
        assert response.total_pages == 2

    def test_create_response_empty(self) -> None:
        """测试创建空响应"""
        response = create_paginated_response([], total=0, page=1, limit=20)
        assert response.total_pages == 0

    def test_create_response_edge_case_exact_div(self) -> None:
        """测试刚好整除的情况"""
        response = create_paginated_response([], total=20, page=1, limit=10)
        assert response.total_pages == 2

    def test_create_response_edge_case_one_extra(self) -> None:
        """测试多一个的情况"""
        response = create_paginated_response([], total=21, page=1, limit=10)
        assert response.total_pages == 3

    def test_page_greater_than_total_pages(self) -> None:
        """测试页码大于总页数的边界情况"""
        items: List[int] = []
        response = create_paginated_response(items, total=10, page=5, limit=3)
        assert response.total == 10
        assert response.page == 5
        assert response.total_pages == 4
        assert len(response.items) == 0

    def test_very_large_page_number(self) -> None:
        """测试非常大的页码值"""
        items: List[int] = []
        response = create_paginated_response(items, total=100, page=1000000, limit=20)
        assert response.page == 1000000
        assert response.total_pages == 5


@pytest.mark.asyncio
@pytest.mark.unit
class TestPaginateQuery:
    """paginate_query 函数测试 - 需要数据库连接，使用真实模型"""

    async def test_paginate_query_basic(self) -> None:
        """测试基本分页查询 - 使用内存 SQLite"""
        from sqlalchemy import Column, Integer, String, select
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        
        # 创建测试模型
        Base = declarative_base()
        
        class TestModel(Base):
            __tablename__ = "test_items"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        # 创建内存数据库
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 插入测试数据
        async with AsyncSession(engine) as session:
            for i in range(100):
                session.add(TestModel(name=f"item_{i}"))
            await session.commit()
        
        # 执行分页查询
        async with AsyncSession(engine) as session:
            query = select(TestModel)
            items, total, total_pages = await paginate_query(
                session, query, page=1, limit=20
            )
            
            assert total == 100
            assert total_pages == 5
            assert len(items) == 20
        
        await engine.dispose()

    async def test_paginate_query_empty(self) -> None:
        """测试空结果分页查询"""
        from sqlalchemy import Column, Integer, String, select
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        
        Base = declarative_base()
        
        class EmptyModel(Base):
            __tablename__ = "empty_items"
            id = Column(Integer, primary_key=True)
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSession(engine) as session:
            query = select(EmptyModel)
            items, total, total_pages = await paginate_query(
                session, query, page=1, limit=20
            )
            
            assert total == 0
            assert total_pages == 0
            assert items == []
        
        await engine.dispose()

    async def test_paginate_query_page_2(self) -> None:
        """测试第2页分页查询"""
        from sqlalchemy import Column, Integer, String, select
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        
        Base = declarative_base()
        
        class PageModel(Base):
            __tablename__ = "page_items"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSession(engine) as session:
            for i in range(50):
                session.add(PageModel(name=f"item_{i}"))
            await session.commit()
        
        async with AsyncSession(engine) as session:
            query = select(PageModel)
            items, total, total_pages = await paginate_query(
                session, query, page=2, limit=20
            )
            
            assert total == 50
            assert total_pages == 3
            assert len(items) == 20
            # 验证是第二页的数据
            assert items[0].id == 21
        
        await engine.dispose()

    async def test_paginate_query_large_page_number(self) -> None:
        """测试非常大的页码值"""
        from sqlalchemy import Column, Integer, String, select
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        
        Base = declarative_base()
        
        class LargePageModel(Base):
            __tablename__ = "large_page_items"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSession(engine) as session:
            for i in range(100):
                session.add(LargePageModel(name=f"item_{i}"))
            await session.commit()
        
        async with AsyncSession(engine) as session:
            query = select(LargePageModel)
            items, total, total_pages = await paginate_query(
                session, query, page=1000000, limit=20
            )
            
            assert total == 100
            assert total_pages == 5
            assert items == []  # 超出范围，返回空列表
        
        await engine.dispose()
