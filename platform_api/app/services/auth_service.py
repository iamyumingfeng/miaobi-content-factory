"""
认证服务 (auth_service.py)

提供用户认证相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (AccountLockedError, PasswordIncorrectError,
                                 UseridNotFoundError, UserNotFoundError)
from app.core.security import get_password_hash, verify_password
from app.models import Operator, SubUser, SuperAdmin

# 登录失败配置
MAX_LOGIN_FAILURES = 3  # 最大连续失败次数
LOCKOUT_DURATION_MINUTES = 15  # 锁定时长（分钟）


class AuthService:
    """
    认证服务类
    """

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        userid: str,
        password: str,
    ) -> Tuple[SuperAdmin | Operator | SubUser, str, dict]:
        """
        认证用户（支持三种角色）

        Args:
            db: 数据库会话
            userid: 用户ID
            password: 密码

        Returns:
            Tuple[用户对象, 用户类型, 额外信息字典]

        Raises:
            UseridNotFoundError: 账号不存在
            PasswordIncorrectError: 密码错误
            AccountLockedError: 账号已锁定
        """
        # 按优先级尝试三种用户类型
        user_types = [
            (SuperAdmin, "super_admin"),
            (Operator, "operator"),
            (SubUser, "sub_user"),
        ]

        found_user = None
        found_user_type = None

        for model, user_type in user_types:
            result = await db.execute(select(model).where(model.userid == userid))
            user = result.scalar_one_or_none()

            if user:
                found_user = user
                found_user_type = user_type
                break

        # 账号不存在
        if not found_user:
            raise UseridNotFoundError()

        # 检查账号是否被锁定
        now = datetime.now(timezone.utc)
        if hasattr(found_user, "locked_until") and found_user.locked_until:
            if found_user.locked_until > now:
                # 账号仍在锁定中
                remaining_minutes = int(
                    (found_user.locked_until - now).total_seconds() / 60
                )
                raise AccountLockedError(
                    f"账号已被锁定，请在 {remaining_minutes} 分钟后再试"
                )
            else:
                # 锁定已过期，重置失败计数
                found_user.locked_until = None
                found_user.login_failure_count = 0

        # 检查账号状态
        if hasattr(found_user, "status"):
            if found_user.status == "disabled":
                raise AccountLockedError("账号已被禁用")

        # 验证密码
        if not verify_password(password, found_user.hashed_password):
            # 密码错误，增加失败计数
            if hasattr(found_user, "login_failure_count"):
                found_user.login_failure_count = (
                    found_user.login_failure_count or 0
                ) + 1

                remaining_attempts = MAX_LOGIN_FAILURES - found_user.login_failure_count

                if remaining_attempts <= 0:
                    # 达到最大失败次数，锁定账号
                    found_user.locked_until = now + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    await db.commit()
                    raise AccountLockedError(
                        f"连续登录失败次数过多，账号已被锁定 {LOCKOUT_DURATION_MINUTES} 分钟"
                    )

                await db.commit()

                # 抛出通用异常，不泄露剩余次数（防止账号枚举）
                raise PasswordIncorrectError("密码错误")

        # 登录成功，重置失败计数
        if hasattr(found_user, "login_failure_count"):
            found_user.login_failure_count = 0
        if hasattr(found_user, "locked_until"):
            found_user.locked_until = None

        # 更新登录状态和最后登录时间（仅创作管理员和创作者）
        if hasattr(found_user, "last_login_at"):
            found_user.last_login_at = datetime.utcnow()
            # 仅对创作管理员和创作者更新在线状态
            if found_user_type in ("operator", "sub_user"):
                if hasattr(found_user, "status"):
                    found_user.status = "online"

        await db.commit()
        return found_user, found_user_type, {}

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: int,
        user_type: str,
    ) -> Optional[SuperAdmin | Operator | SubUser]:
        """
        根据 ID 和用户类型获取用户

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型

        Returns:
            用户对象或 None
        """
        model_map = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }

        model = model_map.get(user_type)
        if not model:
            return None

        result = await db.execute(select(model).where(model.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_wechat_openid(
        db: AsyncSession,
        openid: str,
    ) -> Optional[Tuple[SuperAdmin | Operator | SubUser, str]]:
        """
        根据微信 OpenID 获取用户

        Args:
            db: 数据库会话
            openid: 微信 OpenID

        Returns:
            Tuple[用户对象, 用户类型] 或 None
        """
        user_types = [
            (SuperAdmin, "super_admin"),
            (Operator, "operator"),
            (SubUser, "sub_user"),
        ]

        for model, user_type in user_types:
            result = await db.execute(
                select(model).where(model.wechat_openid == openid)
            )
            user = result.scalar_one_or_none()
            if user:
                return user, user_type

        return None

    @staticmethod
    async def bind_wechat_to_user(
        db: AsyncSession,
        user_id: int,
        user_type: str,
        openid: str,
        unionid: Optional[str] = None,
    ) -> bool:
        """
        绑定微信到用户

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
            openid: 微信 OpenID
            unionid: 微信 UnionID (可选)

        Returns:
            bool: 是否成功
        """
        model_map = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }

        model = model_map.get(user_type)
        if not model:
            return False

        result = await db.execute(select(model).where(model.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.wechat_openid = openid
        if unionid:
            user.wechat_unionid = unionid

        await db.commit()
        await db.refresh(user)
        return True

    @staticmethod
    async def unbind_wechat_from_user(
        db: AsyncSession,
        user_id: int,
        user_type: str,
    ) -> bool:
        """
        解绑用户微信

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型

        Returns:
            bool: 是否成功
        """
        model_map = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }

        model = model_map.get(user_type)
        if not model:
            return False

        result = await db.execute(select(model).where(model.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.wechat_openid = None
        user.wechat_unionid = None

        await db.commit()
        await db.refresh(user)
        return True

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        user_type: str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        修改用户密码

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
            old_password: 原密码
            new_password: 新密码

        Returns:
            bool: 是否成功

        Raises:
            OldPasswordError: 原密码错误
        """
        from datetime import datetime

        from app.core.exceptions import OldPasswordError

        model_map = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }

        model = model_map.get(user_type)
        if not model:
            return False

        result = await db.execute(select(model).where(model.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError()

        # 验证原密码
        if not verify_password(old_password, user.hashed_password):
            raise OldPasswordError()

        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        user.last_password_changed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)
        return True

    @staticmethod
    async def update_display_name(
        db: AsyncSession,
        user_id: int,
        user_type: str,
        display_name: Optional[str],
    ) -> Optional[SuperAdmin | Operator | SubUser]:
        """
        更新用户自定义昵称

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_type: 用户类型
            display_name: 自定义昵称

        Returns:
            更新后的用户对象
        """
        from datetime import datetime

        model_map = {
            "super_admin": SuperAdmin,
            "operator": Operator,
            "sub_user": SubUser,
        }

        model = model_map.get(user_type)
        if not model:
            return None

        result = await db.execute(select(model).where(model.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError()

        user.display_name = display_name
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)
        return user
