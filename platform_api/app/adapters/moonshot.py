"""
月之暗面 AI 模型适配器 (moonshot.py)

实现月之暗面平台的文本生成功能。

支持模型：
- kimi-k2.6: 最新模型（默认）
- kimi-k2.5, kimi-k2: 前代模型
- kimi-k2-thinking: 思考模式
- moonshot-v1: 经典模型

API文档：https://platform.kimi.com/docs/api/chat

Author: Claude Code
Date: 2025
"""

import json
import logging
import time
from typing import Dict, Any, Optional

import aiohttp

from .params import TextGenParams, ImageGenParams
from .base import GenerationResult
from .openai_compatible import OpenAICompatibleAdapter
from .factory import AdapterRegistry

logger = logging.getLogger(__name__)


class MoonshotAdapter(OpenAICompatibleAdapter):
    """
    月之暗面 AI 模型适配器

    支持文本生成（Kimi 模型）。
    兼容 OpenAI API 格式，但使用 max_completion_tokens（非 max_tokens）。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"

    # ========== 各模型的参数限制配置 ==========
    # 来源：https://platform.kimi.com/docs/api/chat
    # 参数对比表：temperature / top_p / n / presence_penalty / frequency_penalty / thinking
    MODEL_PARAMS = {
        # kimi-k2.6: 大部分参数不可修改（API 强制固定值）
        "kimi-k2.6": {
            "temperature": 1,        # 不可改，只能为1
            "top_p": 0.95,           # 不可改
            "max_tokens": 32000,
            "thinking_support": True,
        },
        # kimi-k2 系列（kimi-k2.5 等前代模型）
        "kimi-k2.5": {
            "temperature": 0.6,      # 可修改
            "top_p": 1.0,             # 可修改
            "max_tokens": 16384,
            "thinking_support": False,
        },
        # kimi-k2（通用前代）
        "kimi-k2": {
            "temperature": 0.6,
            "top_p": 1.0,
            "max_tokens": 8192,
            "thinking_support": False,
        },
        # kimi-k2-thinking 系列（思考模式）
        "kimi-k2-thinking": {
            "temperature": 1.0,      # 固定值
            "top_p": 1.0,
            "max_tokens": 8192,
            "thinking_support": True,
        },
        # moonshot-v1 经典系列
        "moonshot-v1": {
            "temperature": 0.0,      # 固定值
            "top_p": 1.0,
            "max_tokens": 4096,
            "thinking_support": False,
        },
    }

    def __init__(self, config):
        super().__init__(config)
        self.platform = "moonshot"

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """
        生成文本内容（Moonshot 兼容格式）

        注意：Moonshot 使用 max_completion_tokens 而非 max_tokens

        Args:
            prompt: 提示词（已完成的变量替换）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        session = None
        try:
            # 构建请求
            api_endpoint = self.DEFAULT_TEXT_ENDPOINT
            url = f"{self.base_url}{api_endpoint}"

            # 模型参数
            model_id = params.model_id if params else self.config.model_id

            # 匹配模型配置（支持精确匹配和前缀匹配）
            model_params = None
            if model_id in self.MODEL_PARAMS:
                model_params = self.MODEL_PARAMS[model_id]
            else:
                # 前缀匹配（如 kimi-k2.5-coding 匹配 kimi-k2.5）
                for key in sorted(self.MODEL_PARAMS.keys(), key=len, reverse=True):
                    if model_id.startswith(key) and key != "kimi-k2":
                        model_params = self.MODEL_PARAMS[key]
                        break
            if not model_params:
                model_params = self.MODEL_PARAMS["kimi-k2.6"]

            # token 限制
            max_tokens = params.max_tokens if params else 32000
            if max_tokens > model_params["max_tokens"]:
                logger.warning("[LLM] max_tokens=%d 超过模型 %s 的建议值 %d，自动调整", max_tokens, model_id, model_params["max_tokens"])
                max_tokens = model_params["max_tokens"]

            # 使用模型固定值（API 强制限制，忽略外部传入的 temperature/top_p）
            temperature = model_params["temperature"]
            top_p = model_params["top_p"]
            logger.debug("[LLM] Moonshot 参数适配 | model=%s | temperature=%s | top_p=%s | max_tokens=%s", model_id, temperature, top_p, max_tokens)

            # Moonshot 使用 max_completion_tokens（max_tokens 已弃用）
            # 根据是否有 system_prompt 构建 messages
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            else:
                messages = [{"role": "user", "content": user_prompt}]
            
            payload = {
                "model": model_id,
                "messages": messages,
                "max_completion_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logger.info("[LLM] Moonshot文案生成请求 | model=%s | url=%s", model_id, url)
            logger.info("[LLM] 请求 payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
            logger.info("[LLM] 请求头: Authorization=Bearer [REDACTED], Content-Type=application/json")

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status >= 400:
                    # 记录详细错误信息
                    error_body = ""
                    try:
                        error_body = await response.text()
                        logger.error("[LLM] Moonshot API 错误响应 | status=%s | body=%s", response.status, error_body[:2000])
                    except Exception:
                        pass
                    response.raise_for_status()

                result = await response.json()

                elapsed = time.time() - start_time
                logger.info("[LLM] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                logger.info("[LLM] Moonshot文案生成响应 | elapsed=%.2fs | model=%s", elapsed, model_id)
                logger.info("[LLM] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2)[:2000])

                # 提取生成的文本
                choices = result.get("choices", [])

                if not choices:
                    logger.warning("[LLM] Moonshot文案生成失败：返回的 choices 为空")
                    return GenerationResult(
                        success=False,
                        error_message="No text generated",
                        raw_response=result,
                    )

                generated_text = choices[0].get("message", {}).get("content", "")
                logger.info("[LLM] 生成的文案长度: %d 字符", len(generated_text) if generated_text else 0)
                logger.info("[LLM] 生成的文案内容: %s", (generated_text[:1024] + "...") if generated_text and len(generated_text) > 1024 else (generated_text or ""))
                logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")

                return GenerationResult(
                    success=True,
                    text=generated_text,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Moonshot HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Moonshot text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """月之暗面暂不支持图片生成"""
        return GenerationResult(success=False, error_message="moonshot does not support image generation")

    async def generate_video(
        self,
        prompt: str,
        variables=None,
        image_url=None,
        **kwargs,
    ):
        """
        生成视频（月之暗面暂不支持视频生成）
        """
        return GenerationResult(
            success=False,
            error_message="moonshot does not support video generation",
        )


# 注册适配器
AdapterRegistry.register("moonshot", MoonshotAdapter)
