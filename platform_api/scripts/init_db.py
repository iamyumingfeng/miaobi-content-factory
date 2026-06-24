"""
数据库初始化脚本 (init_db.py)

创建数据库表和初始数据。

Author: Claude Code
Date: 2025
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.database import async_engine, Base, SyncSessionLocal, sync_engine
from app.core.security import get_password_hash, generate_userid, generate_invitation_code
from app.models import (
    SuperAdmin,
    ModelConfig,
    CleanupRule,
)

settings = get_settings()


def init_db_sync():
    """
    同步方式初始化数据库（用于 Alembic 初始化前）
    """
    print("Creating database tables...")

    # 创建所有表
    Base.metadata.create_all(bind=sync_engine)

    print("Tables created successfully!")

    # 创建初始数据
    with SyncSessionLocal() as db:
        try:
            # 检查是否已有超级管理员
            from sqlalchemy import select
            result = db.execute(select(SuperAdmin).limit(1))
            if result.scalar_one_or_none():
                print("Super admin already exists, skipping initial data creation.")
                return

            # 创建默认超级管理员
            print("Creating default super admin...")
            default_password = "admin123"
            super_admin = SuperAdmin(
                userid="admin",
                nickname="系统管理员",
                hashed_password=get_password_hash(default_password),
                status="active",
            )
            db.add(super_admin)

            # 创建默认清理规则
            print("Creating default cleanup rules...")
            cleanup_rules = [
                CleanupRule(
                    rule_name="清理3个月前的生成内容",
                    content_type="generation",
                    retention_period="quarter",
                    enabled=True,
                ),
            ]
            for rule in cleanup_rules:
                db.add(rule)

            db.commit()
            print()
            print("=" * 60)
            print("Initial data created successfully!")
            print()
            print(f"Super Admin UserID: admin")
            print(f"Super Admin Password: {default_password}")
            print()
            print("Please change the default password immediately after first login!")
            print("=" * 60)
            print()

        except Exception as e:
            db.rollback()
            print(f"Error creating initial data: {e}")
            raise


async def init_db_async():
    """
    异步方式初始化数据库
    """
    print("Creating database tables (async)...")

    # 创建所有表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created successfully!")


def main():
    """
    主函数
    """
    print("=" * 60)
    print("Miaobi Content Factory - Database Initialization")
    print("=" * 60)
    print()

    import argparse
    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument("--sync", action="store_true", help="Use sync engine")
    args = parser.parse_args()

    if args.sync:
        init_db_sync()
    else:
        asyncio.run(init_db_async())


if __name__ == "__main__":
    main()
