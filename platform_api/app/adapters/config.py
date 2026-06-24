"""
模型配置管理器 (config.py)

提供模型配置的加载、缓存和管理功能。

Author: Claude Code
Date: 2025
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import ModelConfig as DBModelConfig

from .base import ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class PlatformConfig:
    """
    平台配置数据类
    """

    platform: str
    display_name: str
    default_qps: int = 5
    min_qps: int = 1
    max_qps: int = 100
    supports_batch: bool = False
    supports_text: bool = True
    supports_image: bool = False
    supports_video: bool = False
    supports_embedding: bool = False
    retry_config: Dict[str, Any] = field(default_factory=dict)


class PlatformConfigRegistry:
    """
    平台配置注册表

    管理各平台的默认配置。
    """

    # 平台显示名称映射
    PLATFORM_NAMES: Dict[str, str] = {
        "bailian": "阿里百炼",
        "volcano": "火山引擎",
        "moonshot": "月之暗面",
        "zhipu": "智谱AI",
        "jimeng": "即梦",
        "kling": "可灵",
        "deepseek": "DeepSeek",
        "4sapi": "4SAPI",
    }

    # 平台默认配置
    PLATFORM_DEFAULTS: Dict[str, Dict[str, Any]] = {
        "bailian": {
            "default_qps": 3,
            "min_qps": 1,
            "max_qps": 10,
            "supports_batch": True,
            "supports_text": True,
            "supports_image": True,
            "supports_video": True,
            "supports_embedding": True,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "volcano": {
            "default_qps": 2,
            "min_qps": 1,
            "max_qps": 5,
            "supports_batch": True,
            "supports_text": True,
            "supports_image": True,
            "supports_video": True,
            "retry_config": {
                "max_retries": 5,
                "base_delay": 2.0,
                "max_delay": 120.0,
                "exponential_base": 2.5,
                "jitter": True,
            },
        },
        "deepseek": {
            "default_qps": 5,
            "min_qps": 1,
            "max_qps": 20,
            "supports_batch": False,
            "supports_text": True,
            "supports_image": False,
            "supports_video": False,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "kling": {
            "default_qps": 10,
            "min_qps": 2,
            "max_qps": 30,
            "supports_batch": False,
            "supports_text": False,
            "supports_image": True,
            "supports_video": True,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 0.5,
                "max_delay": 30.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "moonshot": {
            "default_qps": 5,
            "min_qps": 1,
            "max_qps": 20,
            "supports_batch": False,
            "supports_text": True,
            "supports_image": False,
            "supports_video": False,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "zhipu": {
            "default_qps": 5,
            "min_qps": 1,
            "max_qps": 20,
            "supports_batch": False,
            "supports_text": True,
            "supports_image": True,
            "supports_video": False,
            "supports_embedding": True,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "jimeng": {
            "default_qps": 5,
            "min_qps": 1,
            "max_qps": 20,
            "supports_batch": False,
            "supports_text": False,
            "supports_image": True,
            "supports_video": True,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
        "4sapi": {
            "default_qps": 5,
            "min_qps": 1,
            "max_qps": 20,
            "supports_batch": False,
            "supports_text": True,
            "supports_image": True,
            "supports_video": False,
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        },
    }

    @classmethod
    def get_platform_config(cls, platform: str) -> Optional[PlatformConfig]:
        """
        获取平台配置

        Args:
            platform: 平台名称

        Returns:
            平台配置，如果平台不存在则返回 None
        """
        platform_lower = platform.lower()
        defaults = cls.PLATFORM_DEFAULTS.get(platform_lower)
        if not defaults:
            return None

        return PlatformConfig(
            platform=platform_lower,
            display_name=cls.PLATFORM_NAMES.get(platform_lower, platform),
            **defaults,
        )

    @classmethod
    def get_display_name(cls, platform: str) -> str:
        """
        获取平台显示名称

        Args:
            platform: 平台名称

        Returns:
            平台显示名称
        """
        return cls.PLATFORM_NAMES.get(platform.lower(), platform)

    @classmethod
    def list_all_platforms(cls) -> List[PlatformConfig]:
        """
        获取所有平台配置

        Returns:
            平台配置列表
        """
        return [
            cls.get_platform_config(platform)
            for platform in cls.PLATFORM_DEFAULTS.keys()
        ]


class ModelConfigManager:
    """
    模型配置管理器

    从数据库加载和管理模型配置，提供缓存功能。
    """

    def __init__(self):
        self._cache: Dict[int, ModelConfig] = {}
        self._cache_by_platform: Dict[str, List[ModelConfig]] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)

    def _is_cache_valid(self) -> bool:
        """
        检查缓存是否有效

        Returns:
            缓存是否有效
        """
        if not self._cache_time:
            return False
        return datetime.utcnow() - self._cache_time < self._cache_ttl

    def _invalidate_cache(self):
        """
        使缓存失效
        """
        self._cache.clear()
        self._cache_by_platform.clear()
        self._cache_time = None
        logger.debug("Model config cache invalidated")

    async def load_all_configs(
        self,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> Dict[int, ModelConfig]:
        """
        加载所有模型配置

        Args:
            db: 数据库会话
            force_refresh: 是否强制刷新

        Returns:
            模型配置字典（ID -> 配置）
        """
        if not force_refresh and self._is_cache_valid():
            return self._cache.copy()

        # 从数据库加载所有活跃的模型配置
        query = select(DBModelConfig).where(DBModelConfig.status == "active")
        result = await db.execute(query)
        db_configs = result.scalars().all()

        # 转换为 ModelConfig 对象
        new_cache: Dict[int, ModelConfig] = {}
        new_cache_by_platform: Dict[str, List[ModelConfig]] = {}
        # 保存 DBConfig 用于获取平台信息
        self._db_configs: Dict[int, DBModelConfig] = {}

        for db_config in db_configs:
            # 从 config_json 中提取 api_key
            api_key = ""
            extra_params = {}

            # 调试：打印原始 config_json
            logger.debug(
                f"[ConfigManager] 加载模型配置 | id={db_config.id} | platform={db_config.platform} | model_id={db_config.model_id} | config_json_type={type(db_config.config_json)} | config_json={db_config.config_json}"
            )

            if db_config.config_json:
                api_key = db_config.config_json.get("api_key", "")
                extra_params = {
                    k: v for k, v in db_config.config_json.items() if k != "api_key"
                }

            config = ModelConfig(
                platform=db_config.platform,
                model_id=db_config.model_id,
                api_key=api_key,
                base_url=db_config.base_url,
                max_concurrency=db_config.max_concurrency,
                extra_params=extra_params,
            )

            new_cache[db_config.id] = config
            self._db_configs[db_config.id] = db_config

            # 调试日志：验证 api_key 是否正确加载（仅对需要 api_key 的平台）
            if api_key:
                logger.debug(
                    f"[ConfigManager] 模型配置加载成功 | platform={db_config.platform} | model_id={db_config.model_id} | api_key_len={len(api_key)}"
                )
            elif db_config.platform.lower() not in ["kling", "jimeng"]:
                # kling/jimeng 使用 access_key，不需要 api_key
                logger.warning(
                    f"[ConfigManager] 模型配置缺少 api_key | platform={db_config.platform} | model_id={db_config.model_id} | config_json={bool(db_config.config_json)}"
                )

            # 按平台分组
            platform = db_config.platform.lower()
            if platform not in new_cache_by_platform:
                new_cache_by_platform[platform] = []
            new_cache_by_platform[platform].append(config)

        # 更新缓存
        self._cache = new_cache
        self._cache_by_platform = new_cache_by_platform
        self._cache_time = datetime.utcnow()

        logger.info(f"Loaded {len(new_cache)} model configs from database")
        return new_cache.copy()

    async def get_db_config(
        self,
        db: AsyncSession,
        config_id: int,
    ) -> Optional[DBModelConfig]:
        """
        获取数据库配置对象

        Args:
            db: 数据库会话
            config_id: 配置ID

        Returns:
            数据库配置对象，如果不存在则返回 None
        """
        if not self._is_cache_valid():
            await self.load_all_configs(db, force_refresh=True)

        return getattr(self, "_db_configs", {}).get(config_id)

    async def get_config(
        self,
        db: AsyncSession,
        config_id: int,
    ) -> Optional[ModelConfig]:
        """
        获取指定ID的模型配置

        Args:
            db: 数据库会话
            config_id: 配置ID

        Returns:
            模型配置，如果不存在则返回 None
        """
        if not self._is_cache_valid():
            await self.load_all_configs(db, force_refresh=True)

        return self._cache.get(config_id)

    async def get_configs_by_platform(
        self,
        db: AsyncSession,
        platform: str,
        model_type: Optional[str] = None,
    ) -> List[ModelConfig]:
        """
        获取指定平台的模型配置

        Args:
            db: 数据库会话
            platform: 平台名称
            model_type: 可选的模型类型过滤（llm/image/video）

        Returns:
            模型配置列表
        """
        if not self._is_cache_valid():
            await self.load_all_configs(db, force_refresh=True)

        platform_lower = platform.lower()
        configs = self._cache_by_platform.get(platform_lower, [])

        # 如果需要按模型类型过滤，需要从数据库查询
        if model_type:
            query = select(DBModelConfig).where(
                and_(
                    DBModelConfig.platform == platform_lower,
                    DBModelConfig.model_type == model_type,
                    DBModelConfig.status == "active",
                )
            )
            result = await db.execute(query)
            db_configs = result.scalars().all()

            filtered_configs = []
            for db_config in db_configs:
                config = self._cache.get(db_config.id)
                if config:
                    filtered_configs.append(config)

            return filtered_configs

        return configs.copy()

    async def get_default_config(
        self,
        db: AsyncSession,
        platform: Optional[str] = None,
        model_type: str = "llm",
    ) -> Optional[ModelConfig]:
        """
        获取默认模型配置

        Args:
            db: 数据库会话
            platform: 可选的平台限制
            model_type: 模型类型（llm/image/video）

        Returns:
            默认模型配置，如果没有则返回 None
        """
        result = await self.get_default_config_with_platform(db, platform, model_type)
        return result[0] if result else None

    async def get_default_config_with_platform(
        self,
        db: AsyncSession,
        platform: Optional[str] = None,
        model_type: str = "llm",
    ) -> Optional[tuple[ModelConfig, str]]:
        """
        获取默认模型配置及对应的平台名称

        Args:
            db: 数据库会话
            platform: 可选的平台限制
            model_type: 模型类型（llm/image/video/embedding）

        Returns:
            (配置对象, 平台名称) 元组，如果没有则返回 None
        """
        if not self._is_cache_valid():
            await self.load_all_configs(db, force_refresh=True)

        # 查询默认配置
        query = select(DBModelConfig).where(
            and_(
                DBModelConfig.model_type == model_type,
                DBModelConfig.is_default,
                DBModelConfig.status == "active",
            )
        )

        if platform:
            query = query.where(DBModelConfig.platform == platform.lower())

        result = await db.execute(query)
        default_config = result.scalars().first()

        if default_config:
            config = self._cache.get(default_config.id)
            if config:
                return (config, default_config.platform)

        # 如果没有默认配置，返回第一个可用的
        query = select(DBModelConfig).where(
            and_(
                DBModelConfig.model_type == model_type,
                DBModelConfig.status == "active",
            )
        )
        if platform:
            query = query.where(DBModelConfig.platform == platform.lower())

        result = await db.execute(query)
        first_config = result.scalars().first()

        if first_config:
            config = self._cache.get(first_config.id)
            if config:
                return (config, first_config.platform)

        return None

    def notify_config_changed(self):
        """
        通知配置已更改

        当数据库中的模型配置变更时调用此方法。
        """
        self._invalidate_cache()


# 全局配置管理器实例
_model_config_manager = ModelConfigManager()


def get_model_config_manager() -> ModelConfigManager:
    """
    获取模型配置管理器单例

    Returns:
        模型配置管理器
    """
    return _model_config_manager
