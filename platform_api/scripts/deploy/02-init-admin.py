#!/usr/bin/env python3
"""初始化超级管理员和创作管理员"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal as async_session_factory
from app.models import SuperAdmin
from app.core.security import get_password_hash


async def main():
    print("初始化超级管理员...")

    async with async_session_factory() as session:
        # 初始化超级管理员
        userid = os.getenv("INITIAL_SUPER_ADMIN_USERID", "admin")
        password = os.getenv("INITIAL_SUPER_ADMIN_PASSWORD", "admin123")
        nickname = os.getenv("INITIAL_SUPER_ADMIN_NICKNAME", "超级管理员")

        existing = await session.execute(
            select(SuperAdmin).where(SuperAdmin.userid == userid)
        )
        super_admin = existing.scalar_one_or_none()
        if not super_admin:
            super_admin = SuperAdmin(
                userid=userid,
                hashed_password=get_password_hash(password),
                nickname=nickname,
                display_name=nickname,
                status="active",
            )
            session.add(super_admin)
            await session.flush()
            await session.refresh(super_admin)
            print(f"✅ 超级管理员 {userid} 创建完成")
        else:
            print(f"⚠️  超级管理员 {userid} 已存在，跳过")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
