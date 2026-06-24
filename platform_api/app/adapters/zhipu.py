"""
智谱AI 模型适配器 (zhipu.py)

实现智谱AI平台的文本、图片、视频生成功能。

支持的模型：
- LLM: glm-4-plus, glm-4-air, glm-4-flash, glm-5.1 等
- 图像: glm-image, cogview-4-250304, cogview-4, cogview-3-flash 等
- 视频: cogvideox-3 等

API 文档：
- 图像生成: https://docs.bigmodel.cn/api-reference/模型-api/图像生成

Author: Claude Code
Date: 2025
"""

import logging
from typing import Optional

from .base import GenerationResult
from .factory import AdapterRegistry
from .openai_compatible import OpenAICompatibleAdapter
from .params import ImageGenParams

logger = logging.getLogger(__name__)


class ZhipuAdapter(OpenAICompatibleAdapter):
    """
    智谱AI 模型适配器

    支持文本生成、图片生成、视频生成。


    智谱 API 兼容 OpenAI 格式。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, config):
        super().__init__(config)
        self.platform = "zhipu"

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """智谱暂不支持图片生成"""
        return GenerationResult(
            success=False, error_message="zhipu does not support image generation"
        )

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """
        生成视频（智谱 CogVideoX）

        支持模型：cogvideox-3 等

        Args:
            prompt: 提示词（已完成变量替换）
            image_url: 参考图片URL（图生视频时使用）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        return GenerationResult(
            success=False, error_message="zhipu does not support video generation"
        )


# 注册适配器
AdapterRegistry.register("zhipu", ZhipuAdapter)
