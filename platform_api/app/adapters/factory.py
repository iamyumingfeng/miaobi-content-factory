"""
AI 模型适配器工厂 (factory.py)

提供适配器实例的创建和管理。

Author: Claude Code
Date: 2025
"""

from typing import Dict, Type, Optional
import logging

from .base import BaseModelAdapter, ModelConfig

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    适配器注册中心

    管理所有可用的 AI 平台适配器。
    """

    _adapters: Dict[str, Type[BaseModelAdapter]] = {}

    @classmethod
    def register(cls, platform: str, adapter_class: Type[BaseModelAdapter]):
        """
        注册适配器

        Args:
            platform: 平台名称
            adapter_class: 适配器类
        """
        cls._adapters[platform.lower()] = adapter_class
        logger.info(f"Registered adapter for platform: {platform}")

    @classmethod
    def get_adapter_class(cls, platform: str) -> Optional[Type[BaseModelAdapter]]:
        """
        获取适配器类

        Args:
            platform: 平台名称

        Returns:
            适配器类，如果未注册则返回 None
        """
        return cls._adapters.get(platform.lower())

    @classmethod
    def list_platforms(cls) -> list[str]:
        """
        获取所有已注册的平台列表

        Returns:
            平台名称列表
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_supported(cls, platform: str) -> bool:
        """
        检查平台是否支持

        Args:
            platform: 平台名称

        Returns:
            是否支持
        """
        return platform.lower() in cls._adapters


class ModelAdapterFactory:
    """
    AI 模型适配器工厂

    创建和管理 AI 模型平台适配器实例。
    """

    @staticmethod
    def create_adapter(
        platform: str,
        config: ModelConfig,
        validate: bool = True,
    ) -> BaseModelAdapter:
        """
        创建适配器实例

        Args:
            platform: 平台名称
            config: 模型配置
            validate: 是否验证配置（默认 True）

        Returns:
            适配器实例

        Raises:
            ValueError: 当平台不支持或配置无效时
        """
        platform_lower = platform.lower()

        # 从注册中心获取适配器类
        adapter_class = AdapterRegistry.get_adapter_class(platform_lower)

        if not adapter_class:
            # 尝试延迟导入适配器
            try:
                ModelAdapterFactory._import_adapter(platform_lower)
                adapter_class = AdapterRegistry.get_adapter_class(platform_lower)
            except ImportError as e:
                logger.warning(f"Failed to import adapter for {platform}: {e}")

        if not adapter_class:
            raise ValueError(f"Unsupported platform: {platform}")

        # 验证配置
        if validate:
            ModelAdapterFactory._validate_config(platform, config)

        # 创建适配器实例
        return adapter_class(config)

    @staticmethod
    def _validate_config(platform: str, config: ModelConfig):
        """
        验证模型配置

        Args:
            platform: 平台名称
            config: 模型配置

        Raises:
            ValueError: 当配置无效时
        """
        # 验证必需字段
        if not config.platform:
            raise ValueError(f"platform is required for model config")

        if not config.model_id:
            raise ValueError(f"model_id is required for platform {platform}")

        platform_lower = platform.lower()

        if not config.api_key:
            # 可灵平台使用 AccessKey+SecretKey 动态 JWT，不需要静态 api_key
            if platform_lower == "kling":
                has_access_keys = bool(
                    config.extra_params and
                    config.extra_params.get("access_key_id") and
                    config.extra_params.get("access_key_secret")
                )
                if not has_access_keys:
                    raise ValueError(f"access_key_id and access_key_secret are required for platform {platform}")
            # 即梦AI使用火山引擎 HMAC-SHA256 签名认证，不需要静态 api_key
            elif platform_lower == "jimeng":
                has_access_keys = bool(
                    config.extra_params and
                    config.extra_params.get("access_key") and
                    config.extra_params.get("secret_key")
                )
                if not has_access_keys:
                    raise ValueError(f"access_key and secret_key are required for platform {platform}")
            else:
                raise ValueError(f"api_key is required for platform {platform}")

        # 验证并发限制
        if config.max_concurrency is not None and config.max_concurrency < 1:
            raise ValueError(f"max_concurrency must be at least 1, got {config.max_concurrency}")

        # 平台特定验证

        # 所有 OpenAI 兼容平台的统一验证
        openai_compatible_platforms = {"volcano", "zhipu", "moonshot", "deepseek", "lingyaai"}
        if platform_lower in openai_compatible_platforms:
            if not config.base_url:
                logger.warning(f"base_url not provided for {platform}, using default")

        # 百炼平台验证（专有格式）
        elif platform_lower == "bailian":
            if not config.base_url:
                logger.warning("base_url not provided for bailian, using default")

        # 即梦平台验证
        elif platform_lower == "jimeng":
            if not config.base_url:
                logger.warning("base_url not provided for jimeng, using default")

        # 可灵平台验证
        elif platform_lower == "kling":
            if not config.base_url:
                logger.warning("base_url not provided for kling, using default")
        
        # lingyaai平台验证
        elif platform_lower == "lingyaai":
            if not config.base_url:
                logger.warning("base_url not provided for lingyaai, using default")

        # 4sapi平台验证
        elif platform_lower == "4sapi":
            if not config.base_url:
                logger.warning("base_url not provided for 4sapi, using default")

        logger.debug(f"Config validated for platform: {platform}")

    @staticmethod
    def _import_adapter(platform: str):
        """
        延迟导入适配器

        Args:
            platform: 平台名称
        """
        # 平台到模块名的映射
        platform_modules = {
            "bailian": "app.adapters.bailian",
            "volcano": "app.adapters.volcano",
            "moonshot": "app.adapters.moonshot",
            "jimeng": "app.adapters.jimeng",
            "kling": "app.adapters.kling",
            "deepseek": "app.adapters.deepseek",
            "zhipu": "app.adapters.zhipu",
            "lingyaai": "app.adapters.lingyaai",
            "4sapi": "app.adapters.4sapi",
        }

        module_name = platform_modules.get(platform)
        if module_name:
            try:
                import importlib
                importlib.import_module(module_name)
                logger.info(f"Successfully imported adapter for {platform}")
            except Exception as e:
                logger.error(f"Failed to import adapter for {platform}: {e}", exc_info=True)
