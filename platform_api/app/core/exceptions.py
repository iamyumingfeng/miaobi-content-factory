"""
自定义异常模块 (exceptions.py)

定义应用使用的所有自定义异常类。

Author: Claude Code
Date: 2025
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


# ============================================
# 应用基础异常类
# ============================================
class AppException(Exception):
    """
    应用基础异常类

    所有自定义异常的基类。
    """

    code: str = "ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "An error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Any = None,
        code: Optional[str] = None,
    ):
        if message:
            self.message = message
        if code:
            self.code = code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于响应"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details is not None:
            result["details"] = self.details
        return result

    def to_http_exception(self) -> HTTPException:
        """转换为 FastAPI HTTPException"""
        return HTTPException(status_code=self.status_code, detail=self.to_dict())


# ============================================
# 认证相关异常
# ============================================
class AuthenticationError(AppException):
    """认证失败异常"""

    code = "AUTHENTICATION_ERROR"
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "认证失败"


class InvalidCredentialsError(AuthenticationError):
    """无效的凭证异常"""

    code = "INVALID_CREDENTIALS"
    message = "用户名或密码错误"


class UseridNotFoundError(AuthenticationError):
    """账号不存在异常"""

    code = "USERID_NOT_FOUND"
    message = "账号不存在"


class PasswordIncorrectError(AuthenticationError):
    """密码错误异常"""

    code = "PASSWORD_INCORRECT"
    message = "密码错误"


class AccountLockedError(AuthenticationError):
    """账号已锁定异常"""

    code = "ACCOUNT_LOCKED"
    message = "账号已被锁定，请稍后再试"


class TokenExpiredError(AuthenticationError):
    """令牌已过期异常"""

    code = "TOKEN_EXPIRED"
    message = "令牌已过期"


class InvalidTokenError(AuthenticationError):
    """无效的令牌异常"""

    code = "INVALID_TOKEN"
    message = "无效的令牌"


class WechatAuthError(AuthenticationError):
    """微信认证失败异常"""

    code = "WECHAT_AUTH_ERROR"
    message = "微信认证失败"


class WechatQRExpiredError(AuthenticationError):
    """微信二维码已过期异常"""

    code = "WECHAT_QR_EXPIRED"
    message = "二维码已过期，请刷新"


class BindTokenExpiredError(AuthenticationError):
    """绑定令牌已过期异常"""

    code = "BIND_TOKEN_EXPIRED"
    message = "绑定凭证已过期，请重新扫码"


class WechatAlreadyBoundError(AuthenticationError):
    """微信已绑定其他账号异常"""

    code = "WECHAT_ALREADY_BOUND"
    message = "该微信已绑定其他账号"


class InvitationRequiredError(AuthenticationError):
    """需要邀请码异常"""

    code = "INVITATION_REQUIRED"
    status_code = status.HTTP_403_FORBIDDEN
    message = "需要邀请码才能注册"


class InvalidInvitationCodeError(AuthenticationError):
    """无效的邀请码异常"""

    code = "INVALID_INVITATION_CODE"
    message = "无效的邀请码"


# ============================================
# 授权相关异常
# ============================================
class AuthorizationError(AppException):
    """授权失败异常"""

    code = "AUTHORIZATION_ERROR"
    status_code = status.HTTP_403_FORBIDDEN
    message = "没有权限执行此操作"


class PermissionDeniedError(AuthorizationError):
    """权限拒绝异常"""

    code = "PERMISSION_DENIED"
    message = "权限不足"


class SuperAdminRequiredError(AuthorizationError):
    """需要超级管理员权限异常"""

    code = "SUPER_ADMIN_REQUIRED"
    message = "需要超级管理员权限"


class OperatorRequiredError(AuthorizationError):
    """需要创作管理员权限异常"""

    code = "OPERATOR_REQUIRED"
    message = "需要创作管理员权限"


# ============================================
# 资源相关异常
# ============================================
class DuplicateResourceError(AppException):
    """资源重复异常"""

    code = "DUPLICATE_RESOURCE"
    status_code = status.HTTP_409_CONFLICT
    message = "资源已存在"


class NotFoundError(AppException):
    """资源不存在异常"""

    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND
    message = "资源不存在"


class UserNotFoundError(NotFoundError):
    """用户不存在异常"""

    code = "USER_NOT_FOUND"
    message = "用户不存在"


class TemplateNotFoundError(NotFoundError):
    """模板不存在异常"""

    code = "TEMPLATE_NOT_FOUND"
    message = "模板不存在"


class MaterialNotFoundError(NotFoundError):
    """素材不存在异常"""

    code = "MATERIAL_NOT_FOUND"
    message = "素材不存在"


class GenerationTaskNotFoundError(NotFoundError):
    """生成任务不存在异常"""

    code = "GENERATION_TASK_NOT_FOUND"
    message = "生成任务不存在"


class GenerationItemNotFoundError(NotFoundError):
    """生成子任务不存在异常"""

    code = "GENERATION_ITEM_NOT_FOUND"
    message = "生成子任务不存在"


# ============================================
# 验证相关异常
# ============================================
class ValidationError(AppException):
    """数据验证失败异常"""

    code = "VALIDATION_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "数据验证失败"


class PasswordValidationError(ValidationError):
    """密码验证失败异常"""

    code = "PASSWORD_VALIDATION_ERROR"
    message = "密码验证失败"


class OldPasswordError(PasswordValidationError):
    """原密码错误异常"""

    code = "OLD_PASSWORD_ERROR"
    message = "原密码错误"


class PasswordMismatchError(PasswordValidationError):
    """两次输入的密码不一致异常"""

    code = "PASSWORD_MISMATCH"
    message = "两次输入的密码不一致"


class PasswordTooShortError(PasswordValidationError):
    """密码太短异常"""

    code = "PASSWORD_TOO_SHORT"
    message = "密码长度不足"


class PasswordSameError(PasswordValidationError):
    """新密码与原密码相同异常"""

    code = "PASSWORD_SAME"
    message = "新密码不能与原密码相同"


# ============================================
# 业务逻辑异常
# ============================================
class BusinessError(AppException):
    """业务逻辑异常"""

    code = "BUSINESS_ERROR"
    message = "业务操作失败"


class BusinessException(BusinessError):
    """业务异常（兼容旧代码命名）"""

    pass


class ConcurrencyLimitError(BusinessError):
    """并发限制异常"""

    code = "CONCURRENCY_LIMIT"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = "已达到并发限制"


class TaskAlreadyCancelledError(BusinessError):
    """任务已取消异常"""

    code = "TASK_ALREADY_CANCELLED"
    message = "任务已取消"


class TaskCannotCancelError(BusinessError):
    """任务无法取消异常"""

    code = "TASK_CANNOT_CANCEL"
    message = "任务无法取消"


class PlatformHasTemplatesError(BusinessError):
    """平台下有模板异常"""

    code = "PLATFORM_HAS_TEMPLATES"
    message = "该平台下还有模板，无法删除"


class SystemResourceError(BusinessError):
    """系统资源不可操作异常"""

    code = "SYSTEM_RESOURCE_ERROR"
    message = "系统默认资源不可删除或修改"


class CannotDeleteSystemModelError(BusinessError):
    """无法删除系统预置模型异常"""

    code = "CANNOT_DELETE_SYSTEM_MODEL"
    message = "无法删除系统预置模型"


class WechatNotBoundError(BusinessError):
    """微信未绑定异常"""

    code = "WECHAT_NOT_BOUND"
    message = "未绑定微信账号"


# ============================================
# 第三方服务异常
# ============================================
class ThirdPartyError(AppException):
    """第三方服务异常"""

    code = "THIRD_PARTY_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY
    message = "第三方服务调用失败"


class ModelAPIError(ThirdPartyError):
    """模型 API 异常"""

    code = "MODEL_API_ERROR"
    message = "AI 模型 API 调用失败"


class WechatAPIError(ThirdPartyError):
    """微信 API 异常"""

    code = "WECHAT_API_ERROR"
    message = "微信 API 调用失败"


class XiaohongshuError(ThirdPartyError):
    """小红书 API 异常"""

    code = "XIAOHONGSHU_ERROR"
    message = "小红书 API 调用失败"


class XiaohongshuNotEnabledError(XiaohongshuError):
    """小红书分享未启用异常"""

    code = "XIAOHONGSHU_NOT_ENABLED"
    status_code = status.HTTP_400_BAD_REQUEST
    message = "小红书分享功能未启用"


# ============================================
# 服务器内部异常
# ============================================
class ServerError(AppException):
    """服务器内部错误"""

    code = "INTERNAL_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "服务器内部错误"


class FileUploadError(ServerError):
    """文件上传错误"""

    code = "FILE_UPLOAD_ERROR"
    message = "文件上传失败"


class FileValidationError(FileUploadError):
    """文件验证错误"""

    code = "FILE_VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST
    message = "文件验证失败"


# ============================================
# 错误码映射
# ============================================
ERROR_CODE_MAP = {
    # 认证相关
    40101: AuthenticationError,
    40102: TokenExpiredError,
    40103: InvitationRequiredError,
    40011: OldPasswordError,
    40012: PasswordMismatchError,
    40013: PasswordTooShortError,
    40014: PasswordSameError,
    40021: WechatQRExpiredError,
    40022: InvalidTokenError,
    40023: WechatAuthError,
    40024: InvalidInvitationCodeError,
    40025: WechatAlreadyBoundError,
    40026: BindTokenExpiredError,
    40301: PermissionDeniedError,
    40401: NotFoundError,
    50001: ServerError,
    50021: WechatAPIError,
    50031: XiaohongshuNotEnabledError,
    50032: XiaohongshuError,
    50033: BusinessError,
    50034: ModelAPIError,
}
