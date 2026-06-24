"""
OpenAI 兼容接口适配器基类 (openai_compatible.py)

提供统一的 OpenAI 兼容接口实现，用于文本生成模型。

Author: Claude Code
Date: 2025
"""

import base64
import json
import logging
import re
import time
import asyncio
from typing import Dict, Any, Optional
import aiohttp

from .base import (
    BaseModelAdapter,
    GenerationResult,
    BatchChatResult,
    ModelConfig,
)
from .params import TextGenParams, ImageGenParams, SUPPORTED_RATIOS

logger = logging.getLogger(__name__)


class OpenAICompatibleAdapter(BaseModelAdapter):
    """
    OpenAI 兼容接口适配器基类

    适用于所有兼容 OpenAI API 格式的文本生成模型。
    """

    # 默认 API 端点（子类可覆盖）
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_TEXT_ENDPOINT = "/chat/completions"
    DEFAULT_IMAGE_ENDPOINT = "/images/generations"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or self.DEFAULT_BASE_URL

    async def _get_session(self):
        """
        创建临时会话（每次请求一个新会话，避免未关闭会话的警告）
        """
        timeout = aiohttp.ClientTimeout(total=300.0)
        return aiohttp.ClientSession(timeout=timeout)

    async def _close_session(self, session: aiohttp.ClientSession):
        """
        关闭临时会话
        """
        if session and not session.closed:
            await session.close()

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """使用系统提示词+用户提示词双消息模式生成文本（提示词已完成变量替换）"""
        session = None
        try:
            if system_prompt:
                formatted_system = system_prompt

            formatted_user = user_prompt

            p = self._resolve_text_params(params)
            url = f"{self.base_url}{self.DEFAULT_TEXT_ENDPOINT}"

            if not system_prompt:
                messages = [{"role": "user", "content": formatted_user}]
            else:
                messages = [
                    {"role": "system", "content": formatted_system},
                    {"role": "user", "content": formatted_user},
                ]
            payload = {
                "model": p.model_id,
                "messages": messages,
                "max_tokens": p.max_tokens,
                "temperature": p.temperature,
                "top_p": p.top_p,
            }

            headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
            logger.info("[LLM] 文案生成请求| platform=%s | model=%s", self.platform, p.model_id)
            logger.info("[LLM] 请求 payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                # 检查响应状态
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"{self.platform} API returned status {response.status}: {error_text[:500]}")
                    return GenerationResult(
                        success=False,
                        error_message=f"{self.platform} API error {response.status}: {error_text[:200]}",
                        error_type="server_error" if response.status >= 500 else "client_error",
                    )
                
                result = await response.json()
                elapsed = time.time() - start_time
                logger.info("[LLM] 文案生成响应 | platform=%s | elapsed=%.2fs", self.platform, elapsed)
                logger.info("[LLM] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2))

                choices = result.get("choices", [])
                if not choices:
                    return GenerationResult(success=False, error_message="No text generated", raw_response=result)

                generated_text = choices[0].get("message", {}).get("content", "")

                logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
                logger.info("[LLM] 文案长度: %d", len(generated_text) if generated_text else 0)
                logger.info("[LLM] 生成的文案内容: %s", generated_text)
                logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
                return GenerationResult(success=True, text=generated_text, raw_response=result)

        except asyncio.TimeoutError as e:
            logger.error(f"{self.platform} request timeout after 300s: {e}")
            return GenerationResult(
                success=False,
                error_message=f"{self.platform} request timeout",
                error_type="network_error",
            )
        except aiohttp.ClientError as e:
            logger.error(f"{self.platform} HTTP request failed [{self.classify_http_error(e)}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"{self.platform} text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """生成图片（OpenAI 兼容格式）:不支持参考图"""
        session = None
        try:
            p = self._resolve_image_params(params)
            size = self.convert_ratio_to_size(p.ratio, p.model_id)
            url = f"{self.base_url}{self.DEFAULT_IMAGE_ENDPOINT}"

            payload = {
                "model": p.model_id,
                "prompt": prompt,
                "n": min(p.count, 4),
                "size": size,
            }

            headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}

            logger.info("[Image] 图片生成请求 | platform=%s | model=%s | ratio=%s -> %s | count=%s",
                       self.platform, p.model_id, p.ratio, size, p.count)
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                elapsed = time.time() - start_time
                logger.info("[Image] 图片生成响应 | platform=%s | elapsed=%.2fs", self.platform, elapsed)
                logger.info("[Image] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2))

                data = result.get("data", [])
                if not data:
                    return GenerationResult(success=False, error_message="No image generated", raw_response=result)

                image_urls = []
                image_base64_list = []
                for item in data:
                    url_val = item.get("url")
                    b64_val = item.get("b64_json")
                    if url_val:
                        image_urls.append(url_val)
                    elif b64_val:
                        image_base64_list.append(b64_val)

                logger.info("[Image] 生成图片: urls=%d base64=%d", len(image_urls), len(image_base64_list))
                return GenerationResult(
                    success=True, image_urls=image_urls, image_base64_list=image_base64_list or None,
                    raw_response=result,
                )

        except asyncio.TimeoutError as e:
            logger.error(f"{self.platform} image request timeout after 300s: {e}")
            return GenerationResult(
                success=False,
                error_message=f"{self.platform} image request timeout",
                error_type="network_error",
            )
        except aiohttp.ClientError as e:
            logger.error(f"{self.platform} HTTP request failed [{self.classify_http_error(e)}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"{self.platform} image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_video(
        self,
        prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """
        生成视频（默认不支持，子类可覆盖）

        Args:
            prompt: 提示词模板
            variables: 变量字典，用于填充提示词模板
            image_url: 参考图片URL（可选）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        return GenerationResult(
            success=False,
            error_message=f"{self.platform} does not support video generation",
        )

    def model_max_pixels(self, model_id: str = None) -> int:
        """
        返回模型支持的较大边最大像素（OpenAI 兼容平台默认 2K）

        Args:
            model_id: 模型 ID

        Returns:
            int: 最大像素，默认 2048（2K）
        """
        # OpenAI 兼容平台默认支持 2K
        return 2048