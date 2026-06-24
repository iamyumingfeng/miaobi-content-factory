"""
Schema 模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime
from pydantic import ValidationError

from app.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    PageParams,
    TimestampMixin,
    IdMixin,
    BaseSchema,
)
from app.schemas.auth import (
    LoginRequest,
    UsernamePasswordLoginRequest,
    TokenResponse,
    UserInfo,
    LoginResponse,
    ChangePasswordRequest,
    UpdateDisplayNameRequest,
    RefreshTokenRequest,
)


@pytest.mark.unit
class TestCommonSchemas:
    """通用 Schema 测试"""

    def test_api_response_default(self) -> None:
        """测试默认 API 响应"""
        response = ApiResponse()
        assert response.success is True
        assert response.data is None
        assert response.message is None
        assert response.error is None

    def test_api_response_with_data(self) -> None:
        """测试带数据的 API 响应"""
        data: Dict[str, Any] = {"id": 1, "name": "Test"}
        response = ApiResponse(success=True, data=data, message="成功")
        assert response.success is True
        assert response.data == data
        assert response.message == "成功"

    def test_api_response_error(self) -> None:
        """测试错误 API 响应"""
        response = ApiResponse(
            success=False,
            error="ERROR_CODE",
            message="错误消息"
        )
        assert response.success is False
        assert response.error == "ERROR_CODE"
        assert response.message == "错误消息"

    def test_paginated_response(self) -> None:
        """测试分页响应"""
        items: List[int] = [1, 2, 3]
        response = PaginatedResponse(
            items=items,
            total=10,
            page=1,
            limit=3,
            total_pages=4
        )
        assert response.items == items
        assert response.total == 10
        assert response.page == 1
        assert response.limit == 3
        assert response.total_pages == 4

    def test_page_params_default(self) -> None:
        """测试默认分页参数"""
        params = PageParams()
        assert params.page == 1
        assert params.limit == 20

    def test_page_params_custom(self) -> None:
        """测试自定义分页参数"""
        params = PageParams(page=3, limit=50)
        assert params.page == 3
        assert params.limit == 50

    def test_page_params_validation(self) -> None:
        """测试分页参数验证"""
        # 页码不能小于 1
        with pytest.raises(ValidationError):
            PageParams(page=0)

        # 每页数量不能小于 1
        with pytest.raises(ValidationError):
            PageParams(limit=0)

        # 每页数量不能大于 100
        with pytest.raises(ValidationError):
            PageParams(limit=101)

    def test_timestamp_mixin(self) -> None:
        """测试时间戳混入"""
        now = datetime.now()
        mixin = TimestampMixin(created_at=now, updated_at=now)
        assert mixin.created_at == now
        assert mixin.updated_at == now

    def test_id_mixin(self) -> None:
        """测试 ID 混入"""
        mixin = IdMixin(id=123)
        assert mixin.id == 123

    def test_base_schema(self) -> None:
        """测试基础 Schema"""
        now = datetime.now()
        schema = BaseSchema(id=456, created_at=now, updated_at=now)
        assert schema.id == 456
        assert schema.created_at == now
        assert schema.updated_at == now


@pytest.mark.unit
class TestAuthSchemas:
    """认证 Schema 测试"""

    def test_login_request_valid(self) -> None:
        """测试有效登录请求"""
        request = LoginRequest(userid="test_user", password="test_password")
        assert request.userid == "test_user"
        assert request.password == "test_password"

    def test_login_request_invalid_empty(self) -> None:
        """测试空登录请求"""
        with pytest.raises(ValidationError):
            LoginRequest(userid="", password="")

    def test_login_request_invalid_userid_too_long(self) -> None:
        """测试用户ID过长"""
        with pytest.raises(ValidationError):
            LoginRequest(userid="a" * 65, password="test")

    def test_login_request_invalid_password_too_long(self) -> None:
        """测试密码过长"""
        with pytest.raises(ValidationError):
            LoginRequest(userid="test", password="a" * 129)

    def test_username_password_login_request(self) -> None:
        """测试账号密码登录请求"""
        request = UsernamePasswordLoginRequest(
            userid="test_user",
            password="test_pass"
        )
        assert request.userid == "test_user"
        assert request.password == "test_pass"

    def test_token_response(self) -> None:
        """测试令牌响应"""
        response = TokenResponse(
            access_token="test_token",
            token_type="bearer",
            expires_in=3600
        )
        assert response.access_token == "test_token"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600

    def test_token_response_default_token_type(self) -> None:
        """测试默认令牌类型"""
        response = TokenResponse(access_token="test_token", expires_in=3600)
        assert response.token_type == "bearer"

    def test_user_info(self) -> None:
        """测试用户信息"""
        info = UserInfo(
            id=1,
            userid="test_user",
            nickname="昵称",
            display_name="自定义昵称",
            role="operator"
        )
        assert info.id == 1
        assert info.userid == "test_user"
        assert info.nickname == "昵称"
        assert info.display_name == "自定义昵称"
        assert info.role == "operator"

    def test_user_info_optional_fields(self) -> None:
        """测试用户信息可选字段"""
        info = UserInfo(
            id=1,
            userid="test_user",
            role="super_admin"
        )
        assert info.nickname is None
        assert info.display_name is None

    def test_login_response(self) -> None:
        """测试登录响应"""
        user_info = UserInfo(
            id=1,
            userid="test_user",
            role="operator"
        )
        response = LoginResponse(
            access_token="test_token",
            refresh_token="refresh_token",
            token_type="bearer",
            expires_in=3600,
            refresh_expires_in=86400,
            user=user_info
        )
        assert response.access_token == "test_token"
        assert response.refresh_token == "refresh_token"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.refresh_expires_in == 86400
        assert response.user == user_info

    def test_change_password_request_valid(self) -> None:
        """测试有效修改密码请求"""
        request = ChangePasswordRequest(
            old_password="old_pass",
            new_password="new_pass123",
            confirm_password="new_pass123"
        )
        assert request.old_password == "old_pass"
        assert request.new_password == "new_pass123"
        assert request.confirm_password == "new_pass123"

    def test_change_password_request_passwords_mismatch(self) -> None:
        """测试密码不匹配"""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                old_password="old_pass",
                new_password="new_pass123",
                confirm_password="different_pass"
            )

    def test_change_password_request_min_length(self) -> None:
        """测试密码最小长度验证"""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                old_password="old",
                new_password="12345",
                confirm_password="12345"
            )

    def test_update_display_name_request(self) -> None:
        """测试更新自定义昵称请求"""
        request = UpdateDisplayNameRequest(display_name="新昵称")
        assert request.display_name == "新昵称"

    def test_update_display_name_request_too_long(self) -> None:
        """测试昵称过长"""
        with pytest.raises(ValidationError):
            UpdateDisplayNameRequest(display_name="a" * 101)

    def test_update_display_name_request_empty(self) -> None:
        """测试空昵称"""
        with pytest.raises(ValidationError):
            UpdateDisplayNameRequest(display_name="")

    def test_refresh_token_request(self) -> None:
        """测试刷新令牌请求"""
        request = RefreshTokenRequest(refresh_token="refresh_token_123")
        assert request.refresh_token == "refresh_token_123"

    def test_refresh_token_request_empty(self) -> None:
        """测试空刷新令牌"""
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="")
