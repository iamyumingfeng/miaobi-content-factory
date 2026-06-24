#!/usr/bin/env python3
"""
超级管理员密码重置脚本

使用方法：
  python scripts/reset_admin_password.py [userid] [new_password]

示例：
  python scripts/reset_admin_password.py admin newpassword123
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal as async_session_factory
from app.models import SuperAdmin
from app.core.security import get_password_hash


async def reset_admin_password(userid: str, new_password: str):
    """
    重置超级管理员密码
    """
    async with async_session_factory() as session:
        # 查找用户
        result = await session.execute(
            select(SuperAdmin).where(SuperAdmin.userid == userid)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print(f"错误：找不到用户 '{userid}'")
            return False

        # 更新密码
        admin.hashed_password = get_password_hash(new_password)
        from datetime import datetime
        admin.last_password_changed_at = datetime.utcnow()

        await session.commit()
        await session.refresh(admin)

        print(f"成功！用户 '{userid}' 的密码已更新")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("使用方法: python scripts/reset_admin_password.py <userid> <new_password>")
        print("示例: python scripts/reset_admin_password.py admin newpassword123")
        sys.exit(1)

    userid = sys.argv[1]
    new_password = sys.argv[2]

    if len(new_password) < 6:
        print("错误：密码长度不能少于6位")
        sys.exit(1)

    print("=" * 60)
    print("超级管理员密码重置")
    print("=" * 60)

    try:
        success = asyncio.run(reset_admin_password(userid, new_password))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
