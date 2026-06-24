"""
异常模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import Dict, Any, Type
from fastapi import status

from app.core.exceptions import (
    AppException,
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    AuthorizationError,
    PermissionDeniedError,
    NotFoundError,
    UserNotFoundError,
    ValidationError,
    PasswordValidationError,
    BusinessError,
    ConcurrencyLimitError,
    ThirdPartyError,
    ModelAPIError,
    ServerError,
    FileUploadError,
    ERROR_CODE_MAP,
)


@pytest.mark.unit
class TestAppException:
    """AppException 基类测试"""

    def test_default_exception(self) -> None:
        """测试默认异常"""
        exc = AppException()
        assert exc.code == "ERROR"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "An error occurred"
        assert exc.details is None

    def test_exception_with_message(self) -> None:
        """测试带消息的异常"""
        exc = AppException(message="自定义错误消息")
        assert exc.message == "自定义错误消息"

    def test_exception_with_details(self) -> None:
        """测试带详情的异常"""
        details: Dict[str, str] = {"field": "username", "error": "required"}
        exc = AppException(details=details)
        assert exc.details == details

    def test_exception_with_code(self) -> None:
        """测试带错误码的异常"""
        exc = AppException(code="CUSTOM_ERROR")
        assert exc.code == "CUSTOM_ERROR"

    def test_exception_with_all_params(self) -> None:
        """测试带所有参数的异常"""
        exc = AppException(
            message="测试错误",
            details={"key": "value"},
            code="TEST_ERROR"
        )
        assert exc.message == "测试错误"
        assert exc.details == {"key": "value"}
        assert exc.code == "TEST_ERROR"

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        exc = AppException(
            message="转换测试",
            details={"test": "data"},
            code="CONVERT_ERROR"
        )
        result: Dict[str, Any] = exc.to_dict()
        assert result["code"] == "CONVERT_ERROR"
        assert result["message"] == "转换测试"
        assert result["details"] == {"test": "data"}

    def test_to_dict_without_details(self) -> None:
        """测试没有详情时的字典转换"""
        exc = AppException()
        result: Dict[str, Any] = exc.to_dict()
        assert "code" in result
        assert "message" in result
        assert "details" not in result

    def test_to_http_exception(self) -> None:
        """测试转换为 HTTPException"""
        exc = AppException(
            message="HTTP 错误",
            code="HTTP_ERROR"
        )
        http_exc = exc.to_http_exception()
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in http_exc.detail
        assert "message" in http_exc.detail

    def test_exception_inheritance(self) -> None:
        """测试异常继承"""
        exc = AppException()
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestAuthenticationExceptions:
    """认证相关异常测试"""

    def test_authentication_error(self) -> None:
        """测试认证失败异常"""
        exc = AuthenticationError()
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.message == "认证失败"

    def test_invalid_credentials_error(self) -> None:
        """测试无效凭证异常"""
        exc = InvalidCredentialsError()
        assert exc.code == "INVALID_CREDENTIALS"
        assert exc.message == "用户名或密码错误"
        assert isinstance(exc, AuthenticationError)

    def test_token_expired_error(self) -> None:
        """测试令牌过期异常"""
        exc = TokenExpiredError()
        assert exc.code == "TOKEN_EXPIRED"
        assert exc.message == "令牌已过期"
        assert isinstance(exc, AuthenticationError)

    def test_invalid_token_error(self) -> None:
        """测试无效令牌异常"""
        exc = InvalidTokenError()
        assert exc.code == "INVALID_TOKEN"
        assert exc.message == "无效的令牌"
        assert isinstance(exc, AuthenticationError)


@pytest.mark.unit
class TestAuthorizationExceptions:
    """授权相关异常测试"""

    def test_authorization_error(self) -> None:
        """测试授权失败异常"""
        exc = AuthorizationError()
        assert exc.code == "AUTHORIZATION_ERROR"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.message == "没有权限执行此操作"

    def test_permission_denied_error(self) -> None:
        """测试权限拒绝异常"""
        exc = PermissionDeniedError()
        assert exc.code == "PERMISSION_DENIED"
        assert exc.message == "权限不足"
        assert isinstance(exc, AuthorizationError)


@pytest.mark.unit
class TestNotFoundExceptions:
    """资源不存在异常测试"""

    def test_not_found_error(self) -> None:
        """测试资源不存在异常"""
        exc = NotFoundError()
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.message == "资源不存在"

    def test_user_not_found_error(self) -> None:
        """测试用户不存在异常"""
        exc = UserNotFoundError()
        assert exc.code == "USER_NOT_FOUND"
        assert exc.message == "用户不存在"
        assert isinstance(exc, NotFoundError)


@pytest.mark.unit
class TestValidationExceptions:
    """验证相关异常测试"""

    def test_validation_error(self) -> None:
        """测试数据验证失败异常"""
        exc = ValidationError()
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.message == "数据验证失败"

    def test_password_validation_error(self) -> None:
        """测试密码验证失败异常"""
        exc = PasswordValidationError()
        assert exc.code == "PASSWORD_VALIDATION_ERROR"
        assert exc.message == "密码验证失败"
        assert isinstance(exc, ValidationError)


@pytest.mark.unit
class TestBusinessExceptions:
    """业务逻辑异常测试"""

    def test_business_error(self) -> None:
        """测试业务逻辑异常"""
        exc = BusinessError()
        assert exc.code == "BUSINESS_ERROR"
        assert exc.message == "业务操作失败"

    def test_concurrency_limit_error(self) -> None:
        """测试并发限制异常"""
        exc = ConcurrencyLimitError()
        assert exc.code == "CONCURRENCY_LIMIT"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.message == "已达到并发限制"
        assert isinstance(exc, BusinessError)


@pytest.mark.unit
class TestThirdPartyExceptions:
    """第三方服务异常测试"""

    def test_third_party_error(self) -> None:
        """测试第三方服务异常"""
        exc = ThirdPartyError()
        assert exc.code == "THIRD_PARTY_ERROR"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.message == "第三方服务调用失败"

    def test_model_api_error(self) -> None:
        """测试模型 API 异常"""
        exc = ModelAPIError()
        assert exc.code == "MODEL_API_ERROR"
        assert exc.message == "AI 模型 API 调用失败"
        assert isinstance(exc, ThirdPartyError)


@pytest.mark.unit
class TestServerExceptions:
    """服务器内部异常测试"""

    def test_server_error(self) -> None:
        """测试服务器内部错误"""
        exc = ServerError()
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.message == "服务器内部错误"

    def test_file_upload_error(self) -> None:
        """测试文件上传错误"""
        exc = FileUploadError()
        assert exc.code == "FILE_UPLOAD_ERROR"
        assert exc.message == "文件上传失败"
        assert isinstance(exc, ServerError)


@pytest.mark.unit
class TestErrorCodeMap:
    """错误码映射测试"""

    def test_error_code_map_exists(self) -> None:
        """测试错误码映射存在"""
        assert isinstance(ERROR_CODE_MAP, dict)
        assert len(ERROR_CODE_MAP) > 0

    def test_error_code_map_values_are_exceptions(self) -> None:
        """测试错误码映射的值都是异常类"""
        for code, exc_class in ERROR_CODE_MAP.items():
            assert isinstance(code, int)
            assert issubclass(exc_class, AppException)

    def test_common_error_codes_exist(self) -> None:
        """测试常见错误码存在"""
        # 认证相关
        assert 40101 in ERROR_CODE_MAP
        assert 40102 in ERROR_CODE_MAP

        # 权限相关
        assert 40301 in ERROR_CODE_MAP

        # 不存在相关
        assert 40401 in ERROR_CODE_MAP

        # 服务器错误
        assert 50001 in ERROR_CODE_MAP

    def test_error_code_instances(self) -> None:
        """测试错误码对应的异常可以实例化"""
        for code, exc_class in ERROR_CODE_MAP.items():
            exc = exc_class()
            assert isinstance(exc, AppException)
            assert exc.code is not None
