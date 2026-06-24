"""
直接使用bcrypt创建管理员账号
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import get_settings
from app.models import SuperAdmin

settings = get_settings()


async def main():
    """主函数"""
    print("=" * 60)
    print("初始化超级管理员账号 (直接使用bcrypt)")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # 检查是否已有超级管理员
        result = await db.execute(select(SuperAdmin).limit(1))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"\n超级管理员已存在:")
            print(f"  用户ID: {existing_admin.userid}")
            print(f"  昵称: {existing_admin.nickname}")
            return

        # 创建密码哈希 - 直接使用bcrypt
        password = settings.initial_super_admin_password.encode('utf-8')
        # 确保不超过72字节
        if len(password) > 72:
            password = password[:72]
            print(f"  警告: 密码过长，已截断到72字节")

        print(f"\n准备创建超级管理员:")
        print(f"  用户ID: {settings.initial_super_admin_userid}")
        print(f"  昵称: {settings.initial_super_admin_nickname}")
        print(f"  密码: {'*' * len(password)}")

        # 生成salt并哈希密码
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password, salt)

        admin = SuperAdmin(
            userid=settings.initial_super_admin_userid,
            nickname=settings.initial_super_admin_nickname,
            hashed_password=hashed_password.decode('utf-8'),
            status="active",
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"\n✓ 超级管理员创建成功!")
        print(f"\n登录信息:")
        print(f"  登录地址: http://localhost")
        print(f"  用户ID: {admin.userid}")
        print(f"  密码: {settings.initial_super_admin_password}")
        print(f"\n请妥善保管登录信息!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
