"""
AI 模型适配器模块

包含各 AI 平台的适配器实现。
"""

from .base import BaseModelAdapter, GenerationResult, ModelConfig
from .config import (ModelConfigManager, PlatformConfig,
                     PlatformConfigRegistry, get_model_config_manager)
from .factory import AdapterRegistry, ModelAdapterFactory

__all__ = [
    "BaseModelAdapter",
    "GenerationResult",
    "ModelConfig",
    "AdapterRegistry",
    "ModelAdapterFactory",
    "PlatformConfig",
    "PlatformConfigRegistry",
    "ModelConfigManager",
    "get_model_config_manager",
]
