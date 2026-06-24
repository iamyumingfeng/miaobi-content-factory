#!/usr/bin/env python3
"""初始化数据库表"""
import asyncio
from alembic.config import Config
from alembic import command
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    print("初始化数据库表...")
    alembic_cfg = Config(Path(__file__).parent.parent.parent / "alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ 数据库表初始化完成")


if __name__ == "__main__":
    asyncio.run(main())
