"""
响应工具模块 (response.py)

提供统一的 API 响应格式。

Author: Claude Code
Date: 2025
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式

    所有 API 端点都应该使用这个格式返回响应。
    """

    success: bool = Field(default=True, description="是否成功")
    data: Optional[T] = Field(default=None, description="数据负载")
    message: Optional[str] = Field(default=None, description="消息")
    error: Optional[str] = Field(default=None, description="错误码（失败时）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "message": "操作成功",
            }
        }
    }


def success_response(
    data: Optional[T] = None,
    message: Optional[str] = "操作成功",
) -> ApiResponse[T]:
    """
    创建成功响应

    Args:
        data: 数据负载
        message: 成功消息

    Returns:
        ApiResponse[T]: 成功响应
    """
    return ApiResponse(
        success=True,
        data=data,
        message=message,
        error=None,
    )


def error_response(
    error: str = "ERROR",
    message: str = "操作失败",
    data: Optional[T] = None,
) -> ApiResponse[T]:
    """
    创建失败响应

    Args:
        error: 错误码
        message: 错误消息
        data: 可选数据

    Returns:
        ApiResponse[T]: 失败响应
    """
    return ApiResponse(
        success=False,
        data=data,
        message=message,
        error=error,
    )


class ListResponse(BaseModel, Generic[T]):
    """
    列表响应（非分页）
    """

    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")


def list_response(items: List[T]) -> ListResponse[T]:
    """
    创建列表响应

    Args:
        items: 数据列表

    Returns:
        ListResponse[T]: 列表响应
    """
    return ListResponse(
        items=items,
        total=len(items),
    )
