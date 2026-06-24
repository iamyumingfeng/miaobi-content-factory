"""
DeepSeek AI 模型适配器 (deepseek.py)

实现 DeepSeek 平台的文本生成功能。

Author: Claude Code
Date: 2025
"""

import logging
from typing import Optional

from .openai_compatible import OpenAICompatibleAdapter
from .factory import AdapterRegistry
from .params import TextGenParams, ImageGenParams
from .base import GenerationResult

logger = logging.getLogger(__name__)


class DeepSeekAdapter(OpenAICompatibleAdapter):
    """
    DeepSeek AI 模型适配器

    支持文本生成。
    DeepSeek API 兼容 OpenAI 格式。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, config):
        super().__init__(config)
        self.platform = "deepseek"

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """DeepSeek 暂不支持图片生成"""
        return GenerationResult(success=False, error_message="deepseek does not support image generation")

    async def generate_video(
        self,
        prompt: str,
        image_url=None,
        **kwargs,
    ):
        """
        生成视频（DeepSeek 暂不支持视频生成）
        """
        return GenerationResult(
            success=False,
            error_message="DeepSeek does not support video generation",
        )

# 注册适配器
AdapterRegistry.register("deepseek", DeepSeekAdapter)
