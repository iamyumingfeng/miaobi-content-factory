"""
创意种子库服务 (creative_seed_service.py)

提供创意种子的CRUD操作和业务逻辑。

Author: Claude Code
Date: 2026
"""

import json
import logging
import random
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreativeSeed
from app.schemas.creative_seed import (CreativeSeedCreate,
                                       CreativeSeedGroupResponse,
                                       CreativeSeedListResponse,
                                       CreativeSeedResponse,
                                       CreativeSeedSelectResponse,
                                       CreativeSeedUpdate)

logger = logging.getLogger(__name__)


class CreativeSeedService:
    """创意种子库服务"""

    @classmethod
    async def create_seed(
        cls,
        db: AsyncSession,
        seed_data: CreativeSeedCreate,
        owner_operator_id: int,
    ) -> CreativeSeed:
        """
        创建创意种子

        Args:
            db: 数据库会话
            seed_data: 种子数据
            owner_operator_id: 创作管理员ID

        Returns:
            CreativeSeed: 创建的种子
        """
        seed = CreativeSeed(
            name=seed_data.name,
            seed_type=seed_data.seed_type.value,
            template=seed_data.template,
            description=seed_data.description,
            forbidden_patterns=(
                json.dumps(seed_data.forbidden_patterns)
                if seed_data.forbidden_patterns
                else None
            ),
            example_phrases=(
                json.dumps(seed_data.example_phrases)
                if seed_data.example_phrases
                else None
            ),
            avoid_phrases=(
                json.dumps(seed_data.avoid_phrases) if seed_data.avoid_phrases else None
            ),
            category=seed_data.category,
            status=seed_data.status.value,
            is_system=False,
            owner_operator_id=owner_operator_id,
        )

        db.add(seed)
        await db.commit()
        await db.refresh(seed)

        logger.info(
            "[CreativeSeed] 创建种子成功 | id=%s | name=%s | type=%s | owner=%s",
            seed.id,
            seed.name,
            seed.seed_type,
            owner_operator_id,
        )

        return seed

    @classmethod
    async def get_seed(
        cls, db: AsyncSession, seed_id: int, owner_operator_id: int
    ) -> Optional[CreativeSeed]:
        """
        获取单个创意种子

        Args:
            db: 数据库会话
            seed_id: 种子ID
            owner_operator_id: 创作管理员ID

        Returns:
            CreativeSeed: 种子对象，或None
        """
        query = select(CreativeSeed).where(
            and_(
                CreativeSeed.id == seed_id,
                or_(
                    CreativeSeed.owner_operator_id == owner_operator_id,
                    CreativeSeed.is_system,  # 系统种子所有人可见
                ),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list_seeds(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        seed_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CreativeSeedListResponse:
        """
        列表查询创意种子

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            seed_type: 种子类型过滤
            category: 品类过滤
            status: 状态过滤
            keyword: 关键词搜索
            page: 页码
            page_size: 每页数量

        Returns:
            CreativeSeedListResponse: 列表响应
        """
        # 构建查询条件
        conditions = [
            or_(
                CreativeSeed.owner_operator_id == owner_operator_id,
                CreativeSeed.is_system,
            )
        ]

        if seed_type:
            conditions.append(CreativeSeed.seed_type == seed_type)
        if category:
            conditions.append(CreativeSeed.category == category)
        if status:
            conditions.append(CreativeSeed.status == status)
        if keyword:
            conditions.append(
                or_(
                    CreativeSeed.name.ilike(f"%{keyword}%"),
                    CreativeSeed.template.ilike(f"%{keyword}%"),
                    CreativeSeed.description.ilike(f"%{keyword}%"),
                )
            )

        # 查询总数
        count_query = (
            select(func.count()).select_from(CreativeSeed).where(and_(*conditions))
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 查询列表
        query = (
            select(CreativeSeed)
            .where(and_(*conditions))
            .order_by(CreativeSeed.is_system.desc(), CreativeSeed.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        seeds = list(result.scalars().all())

        # 转换为响应格式
        items = [CreativeSeedResponse.model_validate(seed.to_dict()) for seed in seeds]
        total_pages = (total + page_size - 1) // page_size

        return CreativeSeedListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    async def update_seed(
        cls,
        db: AsyncSession,
        seed_id: int,
        seed_data: CreativeSeedUpdate,
        owner_operator_id: int,
    ) -> Optional[CreativeSeed]:
        """
        更新创意种子

        Args:
            db: 数据库会话
            seed_id: 种子ID
            seed_data: 更新数据
            owner_operator_id: 创作管理员ID

        Returns:
            CreativeSeed: 更新后的种子，或None
        """
        seed = await cls.get_seed(db, seed_id, owner_operator_id)

        if not seed:
            return None

        # 系统种子只能修改部分属性
        if seed.is_system:
            # 系统种子只允许修改状态
            if seed_data.status:
                seed.status = seed_data.status.value
        else:
            # 非系统种子可以修改所有属性
            if seed_data.name is not None:
                seed.name = seed_data.name
            if seed_data.seed_type is not None:
                seed.seed_type = seed_data.seed_type.value
            if seed_data.template is not None:
                seed.template = seed_data.template
            if seed_data.description is not None:
                seed.description = seed_data.description
            if seed_data.forbidden_patterns is not None:
                seed.forbidden_patterns = json.dumps(seed_data.forbidden_patterns)
            if seed_data.example_phrases is not None:
                seed.example_phrases = json.dumps(seed_data.example_phrases)
            if seed_data.avoid_phrases is not None:
                seed.avoid_phrases = json.dumps(seed_data.avoid_phrases)
            if seed_data.category is not None:
                seed.category = seed_data.category
            if seed_data.status is not None:
                seed.status = seed_data.status.value

        seed.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(seed)

        logger.info("[CreativeSeed] 更新种子成功 | id=%s | name=%s", seed.id, seed.name)

        return seed

    @classmethod
    async def delete_seed(
        cls,
        db: AsyncSession,
        seed_id: int,
        owner_operator_id: int,
    ) -> bool:
        """
        删除创意种子

        Args:
            db: 数据库会话
            seed_id: 种子ID
            owner_operator_id: 创作管理员ID

        Returns:
            bool: 是否删除成功
        """
        seed = await cls.get_seed(db, seed_id, owner_operator_id)

        if not seed:
            return False

        # 系统种子不可删除
        if seed.is_system:
            logger.warning("[CreativeSeed] 系统种子不可删除 | id=%s", seed_id)
            return False

        await db.delete(seed)
        await db.commit()

        logger.info("[CreativeSeed] 删除种子成功 | id=%s | name=%s", seed.id, seed.name)

        return True

    @classmethod
    async def get_seeds_by_type(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        seed_type: str,
        category: Optional[str] = None,
    ) -> List[CreativeSeedSelectResponse]:
        """
        按类型获取种子列表（用于下拉选择）

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            seed_type: 种子类型
            category: 品类过滤

        Returns:
            List[CreativeSeedSelectResponse]: 种子选择列表
        """
        conditions = [
            CreativeSeed.seed_type == seed_type,
            CreativeSeed.status == "enabled",
            or_(
                CreativeSeed.owner_operator_id == owner_operator_id,
                CreativeSeed.is_system,
            ),
        ]

        if category and category != "通用":
            conditions.append(
                or_(
                    CreativeSeed.category == category,
                    CreativeSeed.category == "通用",
                )
            )

        query = (
            select(CreativeSeed)
            .where(and_(*conditions))
            .order_by(CreativeSeed.is_system.desc(), CreativeSeed.use_count.desc())
        )
        result = await db.execute(query)
        seeds = list(result.scalars().all())

        return [
            CreativeSeedSelectResponse(
                id=s.id,
                name=s.name,
                seed_type=s.seed_type,
                template=s.template,
                category=s.category,
            )
            for s in seeds
        ]

    @classmethod
    async def get_seeds_grouped(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        category: Optional[str] = None,
    ) -> CreativeSeedGroupResponse:
        """
        获取按类型分组的种子列表

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            category: 品类过滤

        Returns:
            CreativeSeedGroupResponse: 分组种子列表
        """
        opening = await cls.get_seeds_by_type(
            db, owner_operator_id, "opening", category
        )
        emotion = await cls.get_seeds_by_type(
            db, owner_operator_id, "emotion", category
        )
        ending = await cls.get_seeds_by_type(db, owner_operator_id, "ending", category)

        return CreativeSeedGroupResponse(
            opening=opening,
            emotion=emotion,
            ending=ending,
        )

    @classmethod
    async def get_random_seed(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        seed_type: str,
        category: Optional[str] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> Optional[CreativeSeed]:
        """
        获取随机种子（用于文案生成）

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            seed_type: 种子类型
            category: 品类过滤
            exclude_ids: 排除的种子ID列表

        Returns:
            CreativeSeed: 随机种子
        """
        conditions = [
            CreativeSeed.seed_type == seed_type,
            CreativeSeed.status == "enabled",
            or_(
                CreativeSeed.owner_operator_id == owner_operator_id,
                CreativeSeed.is_system,
            ),
        ]

        if category and category != "通用":
            conditions.append(
                or_(
                    CreativeSeed.category == category,
                    CreativeSeed.category == "通用",
                )
            )

        if exclude_ids:
            conditions.append(CreativeSeed.id.notin_(exclude_ids))

        query = select(CreativeSeed).where(and_(*conditions))
        result = await db.execute(query)
        seeds = list(result.scalars().all())

        if not seeds:
            return None

        return random.choice(seeds)

    @classmethod
    async def increment_use_count(cls, db: AsyncSession, seed_id: int) -> None:
        """
        增加使用次数

        Args:
            db: 数据库会话
            seed_id: 种子ID
        """
        seed = await db.get(CreativeSeed, seed_id)
        if seed:
            seed.use_count += 1
            await db.commit()
