"""
响应工具模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import Dict, List, Optional, Any
from app.utils.response import (
    ApiResponse,
    success_response,
    error_response,
    ListResponse,
    list_response,
)


@pytest.mark.unit
class TestApiResponse:
    """ApiResponse 模型测试"""

    def test_default_success_response(self) -> None:
        """测试默认成功响应"""
        response = ApiResponse()
        assert response.success is True
        assert response.data is None
        assert response.message is None
        assert response.error is None

    def test_success_response_with_data(self) -> None:
        """测试带数据的成功响应"""
        data: Dict[str, Any] = {"id": 1, "name": "Test"}
        response = ApiResponse(success=True, data=data, message="操作成功")
        assert response.success is True
        assert response.data == data
        assert response.message == "操作成功"
        assert response.error is None

    def test_error_response(self) -> None:
        """测试错误响应"""
        response = ApiResponse(
            success=False,
            error="VALIDATION_ERROR",
            message="数据验证失败"
        )
        assert response.success is False
        assert response.error == "VALIDATION_ERROR"
        assert response.message == "数据验证失败"

    def test_model_example(self) -> None:
        """测试模型示例"""
        example = ApiResponse.model_config["json_schema_extra"]["example"]
        assert "success" in example
        assert "data" in example
        assert "message" in example


@pytest.mark.unit
class TestSuccessResponse:
    """success_response 函数测试"""

    def test_basic_success_response(self) -> None:
        """测试基本成功响应"""
        response = success_response()
        assert response.success is True
        assert response.data is None
        assert response.message == "操作成功"
        assert response.error is None

    def test_success_with_data(self) -> None:
        """测试带数据的成功响应"""
        data: Dict[str, Any] = {"id": 123, "name": "测试数据"}
        response = success_response(data=data)
        assert response.success is True
        assert response.data == data
        assert response.message == "操作成功"

    def test_success_with_custom_message(self) -> None:
        """测试自定义消息"""
        response = success_response(message="创建成功")
        assert response.success is True
        assert response.message == "创建成功"

    def test_success_with_data_and_message(self) -> None:
        """测试带数据和自定义消息"""
        data: List[int] = [1, 2, 3]
        response = success_response(data=data, message="获取列表成功")
        assert response.success is True
        assert response.data == data
        assert response.message == "获取列表成功"


@pytest.mark.unit
class TestErrorResponse:
    """error_response 函数测试"""

    def test_basic_error_response(self) -> None:
        """测试基本错误响应"""
        response = error_response()
        assert response.success is False
        assert response.error == "ERROR"
        assert response.message == "操作失败"
        assert response.data is None

    def test_error_with_custom_code(self) -> None:
        """测试自定义错误码"""
        response = error_response(error="NOT_FOUND")
        assert response.success is False
        assert response.error == "NOT_FOUND"
        assert response.message == "操作失败"

    def test_error_with_custom_message(self) -> None:
        """测试自定义错误消息"""
        response = error_response(message="用户不存在")
        assert response.success is False
        assert response.error == "ERROR"
        assert response.message == "用户不存在"

    def test_error_with_all_params(self) -> None:
        """测试所有参数"""
        response = error_response(
            error="VALIDATION_ERROR",
            message="密码长度不足",
            data={"field": "password"}
        )
        assert response.success is False
        assert response.error == "VALIDATION_ERROR"
        assert response.message == "密码长度不足"
        assert response.data == {"field": "password"}


@pytest.mark.unit
class TestListResponse:
    """ListResponse 模型测试"""

    def test_list_response_creation(self) -> None:
        """测试列表响应创建"""
        items: List[Dict[str, int]] = [{"id": 1}, {"id": 2}]
        response = ListResponse(items=items, total=2)
        assert response.items == items
        assert response.total == 2

    def test_empty_list(self) -> None:
        """测试空列表"""
        response = ListResponse(items=[], total=0)
        assert response.items == []
        assert response.total == 0


@pytest.mark.unit
class TestListResponseFunction:
    """list_response 函数测试"""

    def test_list_response_with_items(self) -> None:
        """测试带项目的列表响应"""
        items: List[str] = ["a", "b", "c"]
        response = list_response(items)
        assert isinstance(response, ListResponse)
        assert response.items == items
        assert response.total == 3

    def test_list_response_empty(self) -> None:
        """测试空列表响应"""
        response = list_response([])
        assert response.items == []
        assert response.total == 0

    def test_list_response_with_objects(self) -> None:
        """测试带对象的列表响应"""
        items: List[Dict[str, Any]] = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        response = list_response(items)
        assert len(response.items) == 2
        assert response.total == 2
        assert response.items[0]["name"] == "A"
        assert response.items[1]["name"] == "B"
