"""
灵芽 AI 模型适配器 (lingyaai.py)

实现灵芽平台 (LingyaAI) 的文本生成和图片生成功能。

灵芽 API 是一个专业的大模型 API 聚合中转平台，完全兼容 OpenAI 接口格式。
- Base URL: https://api.lingyaai.cn/v1
- 认证方式: Bearer Token（sk- 开头）

支持的文本模型：
- GPT 系列、Claude 系列、Gemini 系列
- DeepSeek、通义千问(Qwen)、GLM 等

支持的图片生成模型（通过 model_id 区分）：
- gpt-image-1: GPT Image 1.0 图片生成
- gpt-image-2: GPT Image 2.0 图片生成（推荐）
- nano-banana: Nano Banana 图片生成
- nano-banana-pro: Nano Banana Pro 图片生成（超写实）

API文档：
- 文本生成: https://api.lingyaai.cn/doc/#/coding/openai-chat
- gpt-image-2: https://api.lingyaai.cn/doc/#/coding/gpt-image-2
- nano-banana: https://api.lingyaai.cn/doc/#/coding/nano-banana
- gpt-image-1: https://api.lingyaai.cn/doc/#/coding/gpt-image-1

Author: Claude Code
Date: 2026
"""

import json
import logging
import re
import time
from typing import Dict, Any, Optional, List

import aiohttp

from .params import TextGenParams, ImageGenParams
from .base import GenerationResult
from .openai_compatible import OpenAICompatibleAdapter
from .factory import AdapterRegistry

from .image_prompts import enhance_image_prompt, get_negative_prompt

logger = logging.getLogger(__name__)

# LingyaAI 支持的图片生成模型配置
IMAGE_MODEL_CONFIG = {
    # 模型 ID -> 配置（比例/尺寸选项、默认值、特殊参数等）
    "gpt-image-1": {
        "supported_sizes": ["1024x1024", "1792x1024", "1024x1792"],
        "default_size": "1024x1024",
        "uses_aspect_ratio": False,
        "description": "GPT Image 1.0 图片生成",
    },
    "gpt-image-2": {
        "supported_aspect_ratios": [
            "1:1", "4:3", "3:4", "16:9", "9:16",
        ],
        "default_aspect_ratio": "1:1",
        "uses_aspect_ratio": True,
        "supports_resolution": True,
        "supported_resolutions": ["1K", "2K", "4K"],
        "description": "GPT Image 2.0 图片生成（推荐）",
    },
    "nano-banana": {
        "supported_aspect_ratios": [
            "1:1", "4:3", "3:4", "16:9", "9:16",
            "2:3", "3:2", "4:5", "5:4", "21:9",
        ],
        "default_aspect_ratio": "1:1",
        "uses_aspect_ratio": True,
        "description": "Nano Banana 图片生成",
    },
    "nano-banana-pro": {
        "supported_aspect_ratios": [
            "1:1", "4:3", "3:4", "16:9", "9:16",
            "2:3", "3:2", "4:5", "5:4", "21:9",
        ],
        "default_aspect_ratio": "1:1",
        "uses_aspect_ratio": True,
        "supports_image_size": True,
        "supported_image_sizes": ["1K", "2K", "4K"],
        "default_image_size": "4K",
        "description": "Nano Banana Pro 图片生成（超写实）",
    },
    "nano-banana-2": {
        "supported_aspect_ratios": [
            "1:1", "4:3", "3:4", "16:9", "9:16",
            "2:3", "3:2", "4:5", "5:4", "21:9",
        ],
        "default_aspect_ratio": "1:1",
        "uses_aspect_ratio": True,
        "supports_image_size": True,
        "supported_image_sizes": ["1K", "2K", "4K"],
        "default_image_size": "4K",
        "description": "Nano Banana 2 图片生成",
    },
}


class LingyaAIAdapter(OpenAICompatibleAdapter):
    """
    灵芽 AI 模型适配器

    支持文本生成和多种模型的图片生成。
    完全兼容 OpenAI API 格式。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://api.lingyaai.cn/v1"

    def __init__(self, config):
        super().__init__(config)
        self.platform = "lingyaai"

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """
        生成文本内容（LingyaAI / OpenAI 兼容格式）

        Args:
            user_prompt: 用户提示词（已完成变量替换）
            system_prompt: 系统提示词（已完成变量替换）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        session = None
        p_val = params or TextGenParams()
        p_val.model_id = p_val.model_id or self.config.model_id
        try:
            if system_prompt:
                formatted_system = system_prompt

            formatted_prompt = user_prompt
            url = f"{self.base_url}{self.DEFAULT_TEXT_ENDPOINT}"

            # 构建 messages
            if not system_prompt:
                messages = [{"role": "user", "content": formatted_prompt}]
            else:
                messages = [
                    {"role": "system", "content": formatted_system},
                    {"role": "user", "content": formatted_prompt},
                ]

            payload = {
                "model": p_val.model_id,
                "messages": messages,
                "max_tokens": p_val.max_tokens,
                "temperature": p_val.temperature,
                "top_p": p_val.top_p,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info("[LLM] LingyaAI文案生成请求 | platform=lingyaai | model=%s | url=%s", p_val.model_id, url)
            logger.info("[LLM] 请求 payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                elapsed = time.time() - start_time
                logger.info("[LLM] LingyaAI文案生成响应 | platform=lingyaai | elapsed=%.2fs | model=%s", elapsed, p_val.model_id)
                logger.info("[LLM] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2)[:2000])

                # 提取生成的文本
                choices = result.get("choices", [])

                if not choices:
                    logger.warning("[LLM] LingyaAI文案生成失败：返回的 choices 为空")
                    return GenerationResult(
                        success=False,
                        error_message="No text generated",
                        raw_response=result,
                    )

                generated_text = choices[0].get("message", {}).get("content", "")

                logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
                logger.info("[LLM] 生成的文案长度: %d 字符", len(generated_text) if generated_text else 0)
                logger.info("[LLM] 生成的文案内容: %s", generated_text)
                logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")

                return GenerationResult(
                    success=True,
                    text=generated_text,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            error_type = self.classify_http_error(e)
            logger.error(f"LingyaAI HTTP request failed [{error_type}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"LingyaAI text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """生成图片（LingyaAI），根据模型自动适配尺寸参数"""
        p = params or ImageGenParams()
        p.model_id = p.model_id or self.config.model_id
        p.count = min(p.count, 4)

        session = None
        try:
            formatted_prompt = prompt
            refs = p.reference_images or []
            has_reference = len(refs) > 0
            enhanced_prompt = enhance_image_prompt(
                formatted_prompt,
                has_reference=has_reference and "【参考图说明】" not in formatted_prompt,
            )
            negative_prompt = get_negative_prompt("")

            url = f"{self.base_url}/images/generations"
            model_id = p.model_id
            model_config = IMAGE_MODEL_CONFIG.get(model_id, IMAGE_MODEL_CONFIG["gpt-image-1"])

            payload = {
                "model": model_id,
                "prompt": enhanced_prompt,
                "n": p.count,
                "negative_prompt": negative_prompt,
            }

            # 尺寸 — 根据模型类型设置
            payload["aspect_ratio"] = p.ratio
            # nano-banana-pro 清晰度
            if model_config.get("supports_image_size"):
                payload["image_size"] = model_config.get("default_image_size", "4K")
            # gpt-image-2 resolution
            if model_config.get("supports_resolution"):
                payload["resolution"] = "1K" if p.ratio in ("1:1", "auto") else "4K"

            # 参考图
            if refs:
                payload["image"] = refs
                logger.info("[Image] 已附加参考图 | count=%d", len(refs))

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info("[Image] LingyaAI图片生成请求 | platform=lingyaai | model=%s | url=%s | count=%s", model_id, url, p.count)
            # Base64 日志优化：仅替换 Base64 数据为长度标记，其余 payload 完整输出
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+',
                                lambda m: f'<Base64 {len(m.group(0))} chars>',
                                payload_str)
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                elapsed = time.time() - start_time
                logger.info("[Image] LingyaAI图片生成响应 | platform=lingyaai | elapsed=%.2fs", elapsed)
                logger.info("[Image] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2))

                # 提取生成的图片 URL
                data = result.get("data", [])

                if not data:
                    logger.warning("[Image] LingyaAI图片生成失败：返回的 data 为空")
                    return GenerationResult(
                        success=False,
                        error_message="No image generated",
                        raw_response=result,
                    )

                image_urls = [item.get("url") for item in data if item.get("url")]

                logger.info("[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
                logger.info("[Image] LingyaAI生成图片数量: %d", len(image_urls) if image_urls else 0)
                logger.info("[Image] 图片URL: %s", image_urls[:2] if image_urls else [])
                logger.info("[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")

                return GenerationResult(
                    success=True,
                    image_urls=image_urls,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            error_type = self.classify_http_error(e)
            logger.error(f"LingyaAI HTTP request failed [{error_type}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"LingyaAI image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_video(
        self,
        prompt: str,
        image_url=None,
        **kwargs,
    ):
        """
        生成视频（灵芽暂不支持视频生成）
        """
        return GenerationResult(
            success=False,
            error_message="LingyaAI does not support video generation",
        )


# 注册适配器
AdapterRegistry.register("lingyaai", LingyaAIAdapter)
