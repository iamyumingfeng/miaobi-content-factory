#!/usr/bin/env python3
"""
测试数据初始化脚本
为 E2E 测试创建测试数据：
- 创作管理员
- 创作者
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal as async_session_factory
from app.models import Operator, SubUser
from app.core.security import get_password_hash


async def init_test_operators(session: AsyncSession):
    """
    初始化测试创作管理员
    """
    test_operators = [
        {
            "userid": "operator1",
            "password": "operator123",
            "nickname": "测试创作管理员1",
            "display_name": "创作管理员一",
            "created_by": 1,
        },
        {
            "userid": "operator2",
            "password": "operator123",
            "nickname": "测试创作管理员2",
            "display_name": "创作管理员二",
            "created_by": 1,
        },
    ]

    for op_data in test_operators:
        result = await session.execute(
            select(Operator).where(Operator.userid == op_data["userid"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"创作管理员已存在，跳过: {op_data['userid']}")
            continue

        operator = Operator(
            userid=op_data["userid"],
            nickname=op_data["nickname"],
            display_name=op_data["display_name"],
            hashed_password=get_password_hash(op_data["password"]),
            created_by=op_data["created_by"],
            status="online",
        )
        session.add(operator)
        print(f"创建创作管理员: {op_data['userid']}")

    await session.commit()


async def init_test_sub_users(session: AsyncSession):
    """
    初始化测试创作者
    """
    # 先获取创作管理员
    result = await session.execute(
        select(Operator).where(Operator.userid == "operator1")
    )
    operator = result.scalar_one_or_none()

    if not operator:
        print("未找到创作管理员 operator1，跳过创作者创建")
        return

    test_sub_users = [
        {
            "userid": "subuser1",
            "password": "subuser123",
            "nickname": "测试创作者1",
            "display_name": "创作者一",
            "owner_operator_id": operator.id,
            "created_by": operator.id,
        },
        {
            "userid": "subuser2",
            "password": "subuser123",
            "nickname": "测试创作者2",
            "display_name": "创作者二",
            "owner_operator_id": operator.id,
            "created_by": operator.id,
        },
    ]

    for sub_data in test_sub_users:
        result = await session.execute(
            select(SubUser).where(SubUser.userid == sub_data["userid"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"创作者已存在，跳过: {sub_data['userid']}")
            continue

        sub_user = SubUser(
            userid=sub_data["userid"],
            nickname=sub_data["nickname"],
            display_name=sub_data["display_name"],
            hashed_password=get_password_hash(sub_data["password"]),
            owner_operator_id=sub_data["owner_operator_id"],
            created_by=sub_data["created_by"],
            status="online",
        )
        session.add(sub_user)
        print(f"创建创作者: {sub_data['userid']}")

    await session.commit()


async def init_test_data():
    """
    初始化所有测试数据
    """
    print("\n" + "=" * 60)
    print("初始化测试数据")
    print("=" * 60)

    async with async_session_factory() as session:
        print("\n1. 初始化测试创作管理员")
        print("-" * 60)
        await init_test_operators(session)

        print("\n2. 初始化测试创作者")
        print("-" * 60)
        await init_test_sub_users(session)

    print("\n" + "=" * 60)
    print("测试数据初始化完成！")
    print("=" * 60)
    print("\n测试账号：")
    print("  超级管理员: admin / admin123")
    print("  创作管理员: operator1 / operator123")
    print("  创作管理员: operator2 / operator123")
    print("  创作者: subuser1 / subuser123")
    print("  创作者: subuser2 / subuser123")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(init_test_data())
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
