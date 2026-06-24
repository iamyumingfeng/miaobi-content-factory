"""
Token 服务 (token_service.py)

处理 refresh token 的存储、验证、刷新、撤销等逻辑。

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from typing import Any, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_tokens_for_user, refresh_access_token
from app.models.operator import Operator
from app.models.refresh_token import RefreshToken
from app.models.sub_user import SubUser
from app.models.super_admin import SuperAdmin
from app.schemas.auth import LoginResponse, RefreshTokenResponse


class TokenService:
    """Token 服务类"""

    @staticmethod
    async def save_refresh_token(
        db: AsyncSession,
        refresh_token: str,
        jti: str,
        user_id: int,
        user_type: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> RefreshToken:
        """
        保存 refresh token 到数据库

        Args:
            db: 数据库会话
            refresh_token: Refresh Token 字符串
            jti: Token 的唯一标识
            user_id: 用户 ID
            user_type: 用户类型
            expires_at: 过期时间
            ip_address: 客户端 IP（可选）
            device_info: 设备信息（可选）

        Returns:
            RefreshToken: 创建的 refresh token 对象
        """
        token = RefreshToken(
            token=refresh_token,
            jti=jti,
            user_id=user_id,
            user_type=user_type,
            issued_at=datetime.utcnow(),
            expires_at=expires_at,
            ip_address=ip_address,
            device_info=device_info,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def create_login_response(
        db: AsyncSession,
        user: Any,
        user_type: str,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> LoginResponse:
        """
        创建登录响应（包含 access token 和 refresh token）

        Args:
            db: 数据库会话
            user: 用户对象
            user_type: 用户类型
            ip_address: 客户端 IP（可选）
            device_info: 设备信息（可选）

        Returns:
            LoginResponse: 登录响应
        """
        # 生成 tokens
        token_data = create_tokens_for_user(
            user_id=user.id,
            user_type=user_type,
            userid=user.userid,
            nickname=user.nickname,
        )

        # 保存 refresh token 到数据库
        await TokenService.save_refresh_token(
            db=db,
            refresh_token=token_data["refresh_token"],
            jti=token_data["jti"],
            user_id=user.id,
            user_type=user_type,
            expires_at=datetime.fromisoformat(token_data["refresh_expires_at"]),
            ip_address=ip_address,
            device_info=device_info,
        )

        # 更新用户登录状态
        await TokenService._update_user_login_status(db, user, user_type)

        # 返回登录响应
        return LoginResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"],
            refresh_expires_in=token_data["refresh_expires_in"],
            user={
                "id": user.id,
                "userid": user.userid,
                "nickname": user.nickname,
                "display_name": user.display_name,
                "role": user_type,
                "wechat_bound": bool(user.wechat_openid),
            },
        )

    @staticmethod
    async def _update_user_login_status(
        db: AsyncSession, user: Any, user_type: str
    ) -> None:
        """更新用户登录状态"""
        user_model = TokenService._get_user_model(user_type)
        if not user_model:
            return

        await db.execute(
            update(user_model)
            .where(user_model.id == user.id)
            .values(
                status="online",
                last_login_at=datetime.utcnow(),
                login_failure_count=0,
                locked_until=None,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token_str: str,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Tuple[Optional[RefreshTokenResponse], Optional[str]]:
        """
        使用 refresh token 刷新 access token

        Args:
            db: 数据库会话
            refresh_token_str: Refresh Token 字符串
            ip_address: 客户端 IP（可选）
            device_info: 设备信息（可选）

        Returns:
            Tuple[Optional[RefreshTokenResponse], Optional[错误信息]]
        """
        # 首先尝试解码和验证 refresh token
        new_access_token, user_data = refresh_access_token(refresh_token_str)
        if not new_access_token or not user_data:
            return None, "无效的 refresh token"

        jti = user_data["jti"]

        # 在数据库中查找 refresh token
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            return None, "Refresh token 不存在"

        if not stored_token.is_valid():
            return None, "Refresh token 已过期或已撤销"

        # 更新 refresh token 的使用时间
        stored_token.last_used_at = datetime.utcnow()

        # 确保用户仍然存在且状态正常
        user, error = await TokenService._get_user_by_id_and_type(
            db, user_data["user_id"], user_data["user_type"]
        )
        if not user or error:
            # 用户不存在或被禁用，撤销该 token
            await TokenService._revoke_token(db, stored_token, error or "用户状态异常")
            return None, error or "用户状态异常"

        if user.status == "disabled":
            await TokenService._revoke_token(db, stored_token, "账号已禁用")
            return None, "账号已被禁用"

        await db.commit()

        # 返回新的 access token
        return (
            RefreshTokenResponse(
                access_token=new_access_token,
                token_type="bearer",
                expires_in=1440 * 60,  # 24小时
            ),
            None,
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        user_id: int,
        user_type: str,
        refresh_token_str: Optional[str] = None,
    ) -> None:
        """
        用户登出，更新状态并撤销 token

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
            refresh_token_str: 要撤销的 refresh token（可选）
        """
        # 更新用户状态为离线
        await TokenService._mark_user_offline(db, user_id, user_type)

        # 撤销指定的 refresh token（如果提供）
        if refresh_token_str:
            from app.core.security import decode_access_token

            payload = decode_access_token(refresh_token_str)
            if payload and payload.get("jti"):
                jti = payload["jti"]
                await TokenService.revoke_token_by_jti(db, jti, "用户主动登出")

    @staticmethod
    async def _mark_user_offline(
        db: AsyncSession, user_id: int, user_type: str
    ) -> None:
        """将用户标记为离线"""
        user_model = TokenService._get_user_model(user_type)
        if not user_model:
            return

        await db.execute(
            update(user_model)
            .where(user_model.id == user_id)
            .values(status="offline", updated_at=datetime.utcnow())
        )
        await db.commit()

    @staticmethod
    async def mark_user_offline_on_token_expiry(
        db: AsyncSession, user_id: int, user_type: str
    ) -> None:
        """
        当 token 过期时，标记用户为离线状态（如果没有其他有效 token）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
        """
        # 检查该用户是否还有其他有效的 token
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.user_type == user_type,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow(),
            )
        )
        active_tokens = result.scalars().all()

        # 如果没有其他有效的 token，则标记用户为离线
        if not active_tokens:
            await TokenService._mark_user_offline(db, user_id, user_type)

    @staticmethod
    async def revoke_token_by_jti(
        db: AsyncSession, jti: str, reason: str = "已撤销"
    ) -> bool:
        """
        根据 JTI 撤销 token

        Args:
            db: 数据库会话
            jti: Token 的唯一标识
            reason: 撤销原因

        Returns:
            bool: 是否成功撤销
        """
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == jti, RefreshToken.is_revoked == False)
            .values(
                is_revoked=True,
                revoked_at=datetime.utcnow(),
                revoke_reason=reason,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def revoke_all_user_tokens(
        db: AsyncSession, user_id: int, user_type: str, reason: str = "用户退出"
    ) -> int:
        """
        撤销用户的所有 token

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
            reason: 撤销原因

        Returns:
            int: 撤销的 token 数量
        """
        result = await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.user_type == user_type,
                RefreshToken.is_revoked == False,
            )
            .values(
                is_revoked=True,
                revoked_at=datetime.utcnow(),
                revoke_reason=reason,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def _revoke_token(db: AsyncSession, token: RefreshToken, reason: str) -> None:
        """撤销单个 token"""
        token.is_revoked = True
        token.revoked_at = datetime.utcnow()
        token.revoke_reason = reason
        token.updated_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def _get_user_by_id_and_type(
        db: AsyncSession, user_id: int, user_type: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """根据 ID 和类型获取用户"""
        user_model = TokenService._get_user_model(user_type)
        if not user_model:
            return None, "无效的用户类型"

        result = await db.execute(select(user_model).where(user_model.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None, "用户不存在"

        return user, None

    @staticmethod
    def _get_user_model(user_type: str) -> Any:
        """获取用户类型对应的模型类"""
        user_models = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }
        return user_models.get(user_type)
