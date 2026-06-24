"""
通用 Schema (common.py)

包含通用的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    """

    success: bool = Field(default=True, description="是否成功")
    data: Optional[T] = Field(default=None, description="数据负载")
    message: Optional[str] = Field(default=None, description="消息")
    error: Optional[str] = Field(default=None, description="错误码（失败时）")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应
    """

    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class PageParams(BaseModel):
    """
    分页参数
    """

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")


class TimestampMixin(BaseModel):
    """
    时间戳混入
    """

    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class IdMixin(BaseModel):
    """
    ID 混入
    """

    id: int = Field(description="主键ID")


class BaseSchema(IdMixin, TimestampMixin):
    """
    基础 Schema
    """

    model_config = {"from_attributes": True}
