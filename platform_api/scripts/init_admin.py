"""
初始化超级管理员账号脚本

直接运行此脚本来创建初始超级管理员账号。

用法:
    python scripts/init_admin.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.config import get_settings
from app.models import SuperAdmin

settings = get_settings()


async def main():
    """主函数"""
    print("=" * 60)
    print("初始化超级管理员账号")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # 检查是否已有超级管理员
        result = await db.execute(select(SuperAdmin).limit(1))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"\n超级管理员已存在:")
            print(f"  用户ID: {existing_admin.userid}")
            print(f"  昵称: {existing_admin.nickname}")
            print(f"\n如需重置密码，请修改数据库或删除现有账号后重新运行。")
            return

        # 创建初始超级管理员
        print(f"\n准备创建超级管理员:")
        print(f"  用户ID: {settings.initial_super_admin_userid}")
        print(f"  昵称: {settings.initial_super_admin_nickname}")

        # 处理密码（bcrypt限制72字节）
        password = settings.initial_super_admin_password
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            print(f"  警告: 密码过长，已截断到72字节")

        print(f"  密码: {'*' * len(password)}")

        # 创建密码哈希
        hashed_password = get_password_hash(password)

        admin = SuperAdmin(
            userid=settings.initial_super_admin_userid,
            nickname=settings.initial_super_admin_nickname,
            hashed_password=hashed_password,
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
