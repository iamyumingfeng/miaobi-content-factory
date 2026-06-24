"""
分页工具模块 (pagination.py)

提供分页相关的工具函数和响应模型。

Author: Claude Code
Date: 2025
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PageParams(BaseModel):
    """
    分页参数
    """
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应

    通用的分页响应格式。
    """
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "limit": 20,
                "total_pages": 5,
            }
        }
    }


async def paginate_query(
    db: AsyncSession,
    query,
    page: int = 1,
    limit: int = 20,
) -> tuple[list, int, int]:
    """
    对查询进行分页

    Args:
        db: 数据库会话
        query: SQLAlchemy 查询对象
        page: 页码
        limit: 每页数量

    Returns:
        tuple[list, int, int]: (数据列表, 总数量, 总页数)
    """
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 计算偏移
    offset = (page - 1) * limit

    # 执行分页查询
    paginated_query = query.offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # 计算总页数
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return items, total, total_pages


def create_paginated_response(
    items: List[T],
    total: int,
    page: int,
    limit: int,
) -> PaginatedResponse[T]:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        limit: 每页数量

    Returns:
        PaginatedResponse[T]: 分页响应对象
    """
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
