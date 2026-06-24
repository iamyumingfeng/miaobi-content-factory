"""
数据库初始化模块

提供应用启动时的数据库初始化功能，包括：
- 创建初始超级管理员账号
- 检查并创建必要的系统数据
- 加载创意种子库初始数据

Author: Claude Code
Date: 2025
"""

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.config import get_settings
from app.models import SuperAdmin, CreativeSeed

logger = logging.getLogger(__name__)
settings = get_settings()


async def init_super_admin(db: AsyncSession) -> Optional[SuperAdmin]:
    """
    初始化超级管理员账号

    如果数据库中没有超级管理员，则创建一个初始的超级管理员账号。
    账号信息从环境变量配置中读取。

    Args:
        db: 数据库会话

    Returns:
        SuperAdmin: 创建或已存在的超级管理员对象
    """
    try:
        # 检查是否已有超级管理员
        result = await db.execute(select(SuperAdmin).limit(1))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info(f"超级管理员已存在: {existing_admin.userid}")
            return existing_admin

        # 创建初始超级管理员
        password = settings.initial_super_admin_password
        # bcrypt有72字节限制，确保密码不超过限制
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            logger.warning("初始密码过长，已截断到72字节")

        hashed_password = get_password_hash(password)

        admin = SuperAdmin(
            userid=settings.initial_super_admin_userid,
            nickname=settings.initial_super_admin_nickname,
            hashed_password=hashed_password,
            status="offline",
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        logger.info(f"超级管理员创建成功: {admin.userid}")
        return admin

    except Exception as e:
        await db.rollback()
        logger.error(f"创建超级管理员失败: {e}")
        raise


async def initialize_database():
    """
    初始化数据库

    应用启动时调用此函数来初始化必要的数据。
    """
    try:
        async with AsyncSessionLocal() as db:
            # 初始化超级管理员
            admin = await init_super_admin(db)

            if admin:
                logger.info(f"[DB Init] 超级管理员账号已就绪: {admin.userid}")
            else:
                logger.info("[DB Init] 数据库初始化完成")

            # 初始化创意种子库
            await init_creative_seeds(db)
    except Exception as e:
        logger.error(f"[DB Init] 数据库初始化失败: {e}")


async def init_creative_seeds(db: AsyncSession) -> None:
    """
    初始化创意种子库

    从 init_data.yaml 加载系统预置的创意种子数据
    """
    try:
        # 检查是否已有系统种子
        result = await db.execute(
            select(CreativeSeed).where(CreativeSeed.is_system == True).limit(1)
        )
        existing_seed = result.scalar_one_or_none()

        if existing_seed:
            logger.info("[DB Init] 创意种子库已有系统种子，跳过初始化")
            return

        # 读取 init_data.yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "init_data.yaml"
        if not config_path.exists():
            logger.warning(f"[DB Init] 配置文件不存在: {config_path}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # 获取创意种子数据
        operator_config = config_data.get("operator_admin", [])
        if not operator_config:
            logger.info("[DB Init] 未找到创作管理员配置，跳过创意种子初始化")
            return

        creative_seeds_data = operator_config[0].get("creative_seeds", [])
        if not creative_seeds_data:
            logger.info("[DB Init] 未找到创意种子配置，跳过初始化")
            return

        # 创建种子记录
        created_count = 0
        for seed_data in creative_seeds_data:
            seed = CreativeSeed(
                name=seed_data.get("name"),
                seed_type=seed_data.get("seed_type"),
                template=seed_data.get("template"),
                description=seed_data.get("description"),
                forbidden_patterns=json.dumps(seed_data.get("forbidden_patterns", [])) if seed_data.get("forbidden_patterns") else None,
                example_phrases=json.dumps(seed_data.get("example_phrases", [])) if seed_data.get("example_phrases") else None,
                avoid_phrases=json.dumps(seed_data.get("avoid_phrases", [])) if seed_data.get("avoid_phrases") else None,
                category=seed_data.get("category", "通用"),
                status=seed_data.get("status", "enabled"),
                is_system=seed_data.get("is_system", False),
                owner_operator_id=None,  # 系统种子无归属
            )
            db.add(seed)
            created_count += 1

        await db.commit()
        logger.info(f"[DB Init] 创意种子库初始化完成，共创建 {created_count} 条系统种子")

    except Exception as e:
        await db.rollback()
        logger.error(f"[DB Init] 创意种子库初始化失败: {e}")
