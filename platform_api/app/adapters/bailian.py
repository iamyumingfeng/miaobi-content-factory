"""
阿里百炼 AI 模型适配器 (bailian.py)

实现阿里百炼平台的文本、图片、视频生成功能。

支持的模型：
- LLM: qwen3.6-plus, qwen3-max 等
- 图像: wan2.7-image-pro, wan2.7-image, wan2.6-image 等
- 视频: wan2.7-t2v, wan2.7-i2v 等

API 文档：
- 多模态生成: https://help.aliyun.com/zh/model-studio/wan-image-generation-api-reference

Author: Claude Code
Date: 2025
"""

import json
import logging
import re
import time
from typing import Dict, Any, Optional, List
import aiohttp

from .params import TextGenParams, ImageGenParams
from .base import (
    BaseModelAdapter,
    GenerationResult,
    BatchChatResult,
    ModelConfig,
)
from .factory import AdapterRegistry

from .image_prompts import enhance_image_prompt, get_negative_prompt

logger = logging.getLogger(__name__)


class BailianAdapter(BaseModelAdapter):
    """
    阿里百炼 AI 模型适配器

    支持文本生成、图片生成（文生图、多图参考生图）、视频生成。
    """

    # 默认 API 端点 — OpenAI 兼容模式（Qwen 系列模型推荐）
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # DashScope 原始端点（多模态接口：图片、视频）
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com"
    # 文本生成端点（OpenAI 兼容 chat completions）
    TEXT_ENDPOINT = "/chat/completions"
    # 多模态生成端点（文生图、图生图、多图参考、视频生成）
    MULTIMODAL_ENDPOINT = "/api/v1/services/aigc/multimodal-generation/generation"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if config.base_url:
            # Normalize: DashScope's raw API path /api/v1 is not OpenAI-compatible.
            # Replace it with the correct /compatible-mode/v1 endpoint.
            self.base_url = config.base_url.replace("/api/v1", "/compatible-mode/v1")
        else:
            self.base_url = self.DEFAULT_BASE_URL
        # 多模态接口使用固定的 DashScope 原始端点
        self._multimodal_url = f"{self.DASHSCOPE_BASE_URL}{self.MULTIMODAL_ENDPOINT}"

    def _enhance_image_prompt(self, prompt: str, has_reference: bool = False) -> str:
        """
        V4.0 真实感增强：自动为短提示词补全高质量要素

        使用统一的提示词管理模块。

        Args:
            prompt: 原始提示词
            has_reference: 是否有参考图片

        Returns:
            增强后的提示词
        """
        return enhance_image_prompt(prompt, has_reference=has_reference)
    
    def model_max_pixels(self, model_id: str = None) -> int:
        """
        模型对应的最大像素（1K=1024, 2K=2048, 4K=4096）

        Args:
            model_id: 模型 ID
            has_reference: 是否有参考图片（图生图场景）

        Returns:
            int: 最大像素，0 表示不限制

        Note:
            百炼各模型像素限制：
            - wan2.7-image-pro: 支持 4K
            - qwen-image-2.0-pro、qwen-image-2.0、wan2.7-image: 支持 2K
            图生图场景（i2i）统一限制为 2K
        """
        mid = (model_id or "").lower()

        # 按模型细分像素限制
        if "wan2.7-image-pro" in mid:
            return 4096  # 4K
        if any(x in mid for x in ["qwen-image-2.0-pro", "qwen-image-2.0", "wan2.7-image"]):
            return 2048  # 2K
        
        # 默认 2K（保守策略）
        return 2048

    def _convert_ratio_to_size(self, ratio: str, model_id: str = None, has_reference: bool = False) -> str:
        """
        根据模型能力将比例转为像素尺寸

        Args:
            ratio: 图片比例，如 "3:4"
            model_id: 模型 ID
            has_reference: 是否有参考图片（图生图场景）

        Returns:
            str: 像素尺寸，如 "1536*2048"
        """
        from .params import calc_pixel_size
        if has_reference == True:
            max_px = 2048
        else:
            max_px = self.model_max_pixels(model_id)
        return calc_pixel_size(ratio, max_px, separator="*") if max_px > 0 else ratio

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

    async def cleanup(self):
        """
        清理适配器资源（兼容旧接口）
        """
        pass

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """
        生成文本内容

        使用阿里百炼 OpenAI 兼容接口（chat completions）。

        Args:
            user_prompt: 用户提示词（已完成变量替换）
            system_prompt: 系统提示词（已完成变量替换）
            params: 文本生成参数

        Returns:
            GenerationResult: 生成结果
        """
        session = None
        try:
            # 构建请求 URL（去除 base_url 尾部斜杠，避免双斜杠）
            base = self.base_url.rstrip("/")
            url = f"{base}{self.TEXT_ENDPOINT}"

            # 模型参数
            model_id = params.model_id if params else self.config.model_id
            max_tokens = params.max_tokens if params else 32000
            temperature = params.temperature if params else 0.7
            top_p = params.top_p if params else 0.8
            enable_thinking = params.enable_thinking if params else True

            # 构建 messages（支持 system_prompt）
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            payload = {
                "model": model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "enable_thinking": True,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logger.info("[LLM] 文案生成请求 | model=%s | url=%s", model_id, url)
            logger.info("[LLM] 请求 payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
            logger.info("[LLM] 请求头: Authorization=Bearer [REDACTED], Content-Type=application/json")

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                # Handle non-JSON error responses (e.g., 404 HTML pages)
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or "application/json" not in content_type:
                    raw_body = await response.text()
                    try:
                        result = json.loads(raw_body)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw_text": raw_body[:500]}
                    error_detail = result.get("message", "") or result.get("error", {}).get("message", "") or raw_body[:300]
                    logger.error(f"Bailian API error: status={response.status} url={url} detail={error_detail}")
                    return GenerationResult(
                        success=False,
                        error_message=f"Bailian API error {response.status}: {error_detail}",
                        raw_response=result,
                    )

                result = await response.json()

                elapsed = time.time() - start_time
                logger.info("[LLM] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                logger.info("[LLM] 文案生成响应 | elapsed=%.2fs | model=%s", elapsed, model_id)
                logger.info("[LLM] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2)[:2000])

                # OpenAI 兼容格式响应
                choices = result.get("choices", [])

                if not choices:
                    logger.warning("[LLM] 文案生成失败：返回的 choices 为空")
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
            logger.error(f"Bailian HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Bailian text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_text_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """
        使用系统提示词+用户提示词双消息模式生成文本

        发送两条独立消息（role: system 和 role: user），确保 LLM 正确识别角色指令。

        Args:
            system_prompt: 系统提示词（平台专家角色设定）
            user_prompt: 用户提示词（具体生成要求）
            variables: 变量字典，用于填充提示词模板
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        session = None
        try:
            formatted_system = self.format_prompt(system_prompt, variables)
            formatted_user = self.format_prompt(user_prompt, variables)

            base = self.base_url.rstrip("/")
            url = f"{base}{self.TEXT_ENDPOINT}"

            model_id = getattr(params, "model_id", self.config.model_id) if params else self.config.model_id
            max_tokens = getattr(params, "max_tokens", 32000) if params else 32000
            temperature = getattr(params, "temperature", 0.7) if params else 0.7
            top_p = getattr(params, "top_p", 0.8) if params else 0.8

            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": formatted_system},
                    {"role": "user", "content": formatted_user},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "enable_thinking": True,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info("[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logger.info("[LLM] 文案生成请求(system+user) | model=%s | url=%s", model_id, url)
            logger.info("[LLM] 请求 payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
            logger.info("[LLM] 请求头: Authorization=Bearer [REDACTED], Content-Type=application/json")

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or "application/json" not in content_type:
                    raw_body = await response.text()
                    try:
                        result = json.loads(raw_body)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw_text": raw_body[:500]}
                    error_detail = result.get("message", "") or result.get("error", {}).get("message", "") or raw_body[:300]
                    logger.error(f"Bailian API error: status={response.status} url={url} detail={error_detail}")
                    return GenerationResult(
                        success=False,
                        error_message=f"Bailian API error {response.status}: {error_detail}",
                        raw_response=result,
                    )

                result = await response.json()

                elapsed = time.time() - start_time
                logger.info("[LLM] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                logger.info("[LLM] 文案生成响应 | elapsed=%.2fs | model=%s", elapsed, model_id)
                logger.info("[LLM] 响应内容: %s", json.dumps(result, ensure_ascii=False, indent=2)[:2000])

                choices = result.get("choices", [])
                if not choices:
                    logger.warning("[LLM] 文案生成失败：返回的 choices 为空")
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
            logger.error(f"Bailian HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Bailian text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_image_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        count: int = 1,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs,
    ) -> GenerationResult:
        """
        使用系统提示词+用户提示词双消息模式生成图片（带参考图片）

        Args:
            system_prompt: 图片系统提示词（构图、风格、质量要求）
            user_prompt: 图片用户提示词（具体画面内容）
            variables: 变量字典，用于填充提示词模板
            count: 生成图片数量
            reference_image_urls: 参考图片URL列表（可选）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        combined = f"{system_prompt}\n\n{user_prompt}"
        return await self.generate_image(
            combined,
            variables,
            count,
            images=reference_image_urls,
            **kwargs,
        )

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """
        生成图片（文生图或多图参考生图）

        使用阿里百炼同步多模态生成接口（multimodal-generation/generation）。
        官方推荐大多数场景使用此同步接口，一次请求即可返回结果。

        文档：https://help.aliyun.com/zh/model-studio/wan-image-generation-api-reference

        Args:
            prompt: 提示词（已完成变量替换）
            params: 图片生成参数

        Returns:
            GenerationResult: 生成结果
        """
        session = None
        try:
            # 模型参数
            p = params or ImageGenParams()
            model_id = p.model_id or "wan2.7-image-pro"
            watermark = p.watermark or False
            reference_images: List[str] = p.reference_images or []
            n = p.count or 1

            # === V4.0 真实感增强：自动补全高质量要素 ===
            # 双图模式下融合指令已包含一致性要求，无需追加英文说明
            has_reference = len(reference_images) > 0
            has_pair_instruction = "【参考图说明】" in prompt
            enhanced_prompt = self._enhance_image_prompt(
                prompt,
                has_reference=has_reference and not has_pair_instruction,
            )

            # 将 ratio 转换为百炼标准格式（图生图场景限制为 2K）
            size = self._convert_ratio_to_size(p.ratio, model_id, has_reference=has_reference)

            # 构建 content 数组（使用增强后的提示词）
            # 注意：当有参考图片时，先放图片再放文本，让模型先理解参考内容
            content: List[Dict[str, str]] = []
            for img_url in reference_images:
                content.append({"image": img_url})
            content.append({"text": enhanced_prompt})

            # === 负向提示词 - V4.0 增强版 ===
            # 自动添加高质量负向提示词，防止 AI 假人感
            final_negative_prompt = get_negative_prompt()

            # 构建请求体（同步接口）
            payload = {
                "model": model_id,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": content,
                        }
                    ]
                },
                "parameters": {
                    "size": size,
                    "n": n,
                    "watermark": watermark,
                    "negative_prompt": final_negative_prompt,
                },
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            # 日志优化：Base64 只显示长度
            log_preview = []
            for img in reference_images:
                if img.startswith('data:'):
                    log_preview.append(f"<Base64 {len(img)} chars>")
                else:
                    log_preview.append(img[:60] + ('...' if len(img) > 60 else ''))
            logger.info(
                f"[Image] Bailian 图片生成请求 | model={model_id} | size={size} | n={n} | "
                f"ref_images={len(reference_images)} | imgs={log_preview}"
            )
            logger.info(f"[Image] Bailian request URL: {self._multimodal_url}")
            # payload 日志：替换 Base64 为长度标记，其余完整输出
            payload_log = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_log = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+',
                                lambda m: f'<Base64 {len(m.group(0))} chars>',
                                payload_log)
            logger.info(f"[Image] Bailian request payload: {payload_log}")

            start_time = time.time()

            session = await self._get_session()
            async with session.post(
                self._multimodal_url, json=payload, headers=headers
            ) as response:
                raw_text = await response.text()
                try:
                    result = json.loads(raw_text)
                except json.JSONDecodeError:
                    result = {"raw_text": raw_text[:500]}

                if response.status != 200:
                    error_msg = result.get("message", "") or result.get("error", {}).get("message", "") or raw_text[:300]
                    logger.error(
                        f"Bailian image API error: status={response.status}, "
                        f"detail={error_msg}, "
                        f"full_response={raw_text[:500]}"
                    )
                    return GenerationResult(
                        success=False,
                        error_message=f"Bailian API error {response.status}: {error_msg}",
                        raw_response=result,
                    )

                elapsed = time.time() - start_time
                logger.debug(f"Bailian image generation completed in {elapsed:.2f}s")

                # 解析响应：{"output": {"choices": [{"message": {"content": [{"image": "url"}, ...]}}]}}
                output = result.get("output", {})
                choices = output.get("choices", [])

                if not choices:
                    return GenerationResult(
                        success=False,
                        error_message="No image generated",
                        raw_response=result,
                    )

                # 提取所有图片 URL
                image_urls: List[str] = []
                for choice in choices:
                    message = choice.get("message", {})
                    message_content = message.get("content", [])
                    for item in message_content:
                        if isinstance(item, dict) and item.get("image"):
                            image_urls.append(item["image"])

                if not image_urls:
                    return GenerationResult(
                        success=False,
                        error_message="No image URLs in response",
                        raw_response=result,
                    )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Bailian HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Bailian image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> GenerationResult:
        """
        生成视频（文生视频或图生视频）
        
        使用阿里百炼 multimodal-generation 接口。
        
        支持模型：
        - wan2.7-t2v: 文生视频
        - wan2.7-i2v: 图生视频
        
        Args:
            prompt: 提示词（已完成变量替换）
            image_url: 参考图片URL（图生视频时使用）
            model_id: 模型ID (wan2.7-t2v 或 wan2.7-i2v)
        
        Returns:
            GenerationResult: 生成结果（视频需要异步获取）
        """
        try:
            await self._ensure_session()

            url = self._multimodal_url

            # 模型参数
            if model_id is None:
                model_id = "wan2.7-t2v"

            # 构建 content 数组
            content = [{"text": prompt}]

            # 图生视频
            if image_url:
                model_id = "wan2.7-i2v"
                content.append({"image": image_url})

            # 构建请求体
            payload = {
                "model": model_id,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": content,
                        }
                    ]
                },
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.debug(f"Calling Bailian video generation: model={model_id}")

            start_time = time.time()

            async with self._session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                elapsed = time.time() - start_time
                logger.debug(f"Bailian video generation completed in {elapsed:.2f}s")

                # 检查错误
                if result.get("code") and result["code"] != "200":
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"Bailian API error: {error_msg}")
                    return GenerationResult(
                        success=False,
                        error_message=f"Bailian API error: {error_msg}",
                        raw_response=result,
                    )

                # 解析 multimodal 响应格式
                output = result.get("output", {})
                choices = output.get("choices", [])

                if not choices:
                    return GenerationResult(
                        success=False,
                        error_message="No video generated",
                        raw_response=result,
                    )

                # 提取视频 URL
                message = choices[0].get("message", {})
                message_content = message.get("content", [])

                video_url = None
                for item in message_content:
                    if isinstance(item, dict) and item.get("video"):
                        video_url = item["video"]
                        break

                return GenerationResult(
                    success=True,
                    video_url=video_url,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Bailian HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Bailian video generation failed: {e}")
            return self.handle_error(e)

    async def check_availability(self) -> bool:
        """
        检查模型平台是否可用

        Returns:
            bool: 是否可用
        """
        try:
            await self._ensure_session()

            url = f"{self.DASHSCOPE_BASE_URL}/models"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
            }

            async with self._session.get(url, headers=headers) as response:
                return response.status == 200

        except Exception as e:
            # 安全记录错误，过滤敏感信息
            error_msg = str(e)
            if self.config.api_key:
                error_msg = error_msg.replace(self.config.api_key, "[REDACTED]")
            logger.warning(f"Bailian availability check failed: {error_msg}")
            return False

    async def get_embedding(self, text: str, **kwargs) -> Optional[List[float]]:
        """
        获取文本的嵌入向量

        使用百炼 OpenAI 兼容的 embedding 接口。
        注意：多模态模型（qwen3-vl-embedding 等）不支持此接口，
        应使用 get_multimodal_embedding 方法。

        Args:
            text: 待嵌入的文本
            **kwargs: 平台特定参数
                - model_id: embedding 模型 ID (默认 text-embedding-v4)

        Returns:
            嵌入向量列表，失败时返回 None
        """
        session = None
        try:
            session = await self._get_session()

            # 构建请求 URL（使用 OpenAI 兼容的 embedding 端点）
            base = self.base_url.rstrip("/")
            url = f"{base}/embeddings"

            # 模型参数 - 仅支持文本 embedding 模型
            model_id = kwargs.get("model_id", "text-embedding-v4")

            payload = {
                "model": model_id,
                "input": text,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.debug(f"Calling Bailian embedding: model={model_id}, text_len={len(text)}")

            start_time = time.time()

            async with session.post(url, json=payload, headers=headers) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or "application/json" not in content_type:
                    raw_body = await response.text()
                    try:
                        result = json.loads(raw_body)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw_text": raw_body[:500]}
                    error_detail = result.get("message", "") or result.get("error", {}).get("message", "") or raw_body[:300]
                    logger.error(f"Bailian embedding API error: status={response.status} detail={error_detail}")
                    return None

                result = await response.json()

                elapsed = time.time() - start_time
                logger.debug(f"Bailian embedding completed in {elapsed:.2f}s")

                # 解析 OpenAI 兼容格式响应
                data = result.get("data", [])
                if not data:
                    logger.warning("Bailian embedding response has no data")
                    return None

                embedding = data[0].get("embedding")
                if not embedding:
                    logger.warning("Bailian embedding response has no embedding")
                    return None

                return embedding

        except aiohttp.ClientError as e:
            logger.error(f"Bailian embedding HTTP request failed: {e}")
            return None
        except Exception as e:
            error_msg = str(e)
            if self.config.api_key:
                error_msg = error_msg.replace(self.config.api_key, "[REDACTED]")
            logger.error(f"Bailian embedding failed: {error_msg}")
            return None
        finally:
            if session:
                await self._close_session(session)

    async def get_multimodal_embedding(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> Optional[List[float]]:
        """
        获取多模态嵌入向量（支持文本+图片）

        使用百炼多模态 embedding 接口，支持纯文本、纯图片、或文本+图片组合。

        API 文档：https://help.aliyun.com/zh/model-studio/developer-reference/multimodal-embedding-api

        Args:
            text: 待嵌入的文本（可选）
            image_url: 图片 URL（可选，支持公网 URL 或 Base64 data URI）
            **kwargs: 平台特定参数

        Returns:
            嵌入向量列表，失败时返回 None
        """
        session = None
        try:
            session = await self._get_session()

            # 多模态 embedding 端点
            url = f"{self.DASHSCOPE_BASE_URL}/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"

            # 模型参数 - 使用支持多模态的 embedding 模型
            model_id = kwargs.get("model_id", "qwen3-vl-embedding")

            # 构建输入内容 - contents 数组格式
            contents = []
            if text:
                contents.append({"text": text})

            final_image = image_url
            if image_url:
                # 检查是否需要处理图片 URL（本地路径、localhost 等）
                if not image_url.startswith("data:"):
                    try:
                        # 尝试导入 storage service 处理图片
                        from app.services.storage_service import get_storage_service
                        storage_service = get_storage_service()

                        # 处理图片，优先使用 Base64
                        # no_compression=True: embedding 需要原图，不压缩
                        processed_url, processed_base64 = await storage_service.process_reference_image(
                            image_url,
                            prefer_url=False,
                            no_compression=True  # embedding 需要原图
                        )

                        final_image = processed_base64 if processed_base64 else processed_url
                        if not final_image:
                            final_image = image_url

                        logger.info(f"[Bailian] 图片处理完成 | original={image_url[:60]}... | final_type={'Base64' if final_image.startswith('data:') else 'URL'}")
                    except Exception as e:
                        logger.warning(f"[Bailian] 图片处理失败，使用原始 URL: {e}")
                        final_image = image_url

                contents.append({"image": final_image})

            if not contents:
                logger.warning("get_multimodal_embedding: 需要提供 text 或 image_url")
                return None

            # qwen3-vl-embedding[文本长度限制：32,000 Token]: 2560（默认）, 2048, 1536, 1024, 768, 512, 256
            # qwen2.5-vl-embedding[文本长度限制：32,000 Token]: 2048, 1024（默认）, 768, 512
            # tongyi-embedding-vision-plus-2026-03-06[文本长度限制：1,024 Token]: 1152（默认）, 1024, 512, 256, 128, 64
            # tongyi-embedding-vision-flash-2026-03-06[文本长度限制：1,024 Token]: 768（默认）, 512, 256, 128, 64
            payload = {
                "model": model_id,
                "input": {
                    "contents": contents
                },
                "parameters": {
                    #"dimension": 512,  # 百炼512 相对通用
                    "enable_fusion": True  # 启用特征融合
                }
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            # 日志：Base64 只显示长度
            log_preview = {"model": model_id, "contents": []}
            for item in contents:
                if "text" in item:
                    log_preview["contents"].append({"text": f"({len(item['text'])} chars)"})
                elif "image" in item:
                    img = item["image"]
                    if img.startswith("data:"):
                        log_preview["contents"].append({"image": f"<Base64 {len(img)} chars>"})
                    else:
                        log_preview["contents"].append({"image": img[:60] + ("..." if len(img) > 60 else "")})

            logger.info(f"Calling Bailian multimodal embedding: {log_preview}")

            start_time = time.time()

            async with session.post(url, json=payload, headers=headers) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or "application/json" not in content_type:
                    raw_body = await response.text()
                    try:
                        result = json.loads(raw_body)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw_text": raw_body[:500]}
                    error_detail = result.get("message", "") or result.get("error", {}).get("message", "") or raw_body[:300]
                    logger.error(f"Bailian multimodal embedding API error: status={response.status} detail={error_detail}")
                    return None

                result = await response.json()

                elapsed = time.time() - start_time
                logger.debug(f"Bailian multimodal embedding completed in {elapsed:.2f}s")

                # 解析响应格式
                # {"output": {"embeddings": [{"embedding": [...], "text_index": 0}]}}
                # 或 {"output": {"embedding": [...]}}  (单输入时)
                output = result.get("output", {})

                # 尝试获取 embeddings 数组
                embeddings = output.get("embeddings", [])
                if embeddings:
                    embedding = embeddings[0].get("embedding")
                    if embedding:
                        logger.info(f"Bailian multimodal embedding success: vector_dim={len(embedding)}")
                        return embedding

                # 尝试单 embedding 格式
                embedding = output.get("embedding")
                if embedding:
                    logger.info(f"Bailian multimodal embedding success: vector_dim={len(embedding)}")
                    return embedding

                # 尝试 OpenAI 兼容格式
                data = result.get("data", [])
                if data:
                    embedding = data[0].get("embedding")
                    if embedding:
                        logger.info(f"Bailian multimodal embedding success: vector_dim={len(embedding)}")
                        return embedding

                logger.warning("Bailian multimodal embedding response has no valid embedding")
                return None

        except aiohttp.ClientError as e:
            logger.error(f"Bailian multimodal embedding HTTP request failed: {e}")
            return None
        except Exception as e:
            error_msg = str(e)
            if self.config.api_key:
                error_msg = error_msg.replace(self.config.api_key, "[REDACTED]")
            logger.error(f"Bailian multimodal embedding failed: {error_msg}", exc_info=True)
            return None
        finally:
            if session:
                await self._close_session(session)

    async def get_image_embedding(self, image_url: str, **kwargs) -> Optional[List[float]]:
        """
        获取图片的嵌入向量

        使用多模态 embedding 接口获取图片的向量表示。

        Args:
            image_url: 图片 URL（支持公网 URL 或 Base64 data URI）
            **kwargs: 平台特定参数

        Returns:
            嵌入向量列表，失败时返回 None
        """
        return await self.get_multimodal_embedding(image_url=image_url, **kwargs)

    async def batch_chat(
        self,
        prompts: list[str],
        variables: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BatchChatResult:
        """
        批量聊天（阿里百炼 Batch Chat）

        Args:
            prompts: 提示词模板列表
            variables: 变量字典，用于填充提示词模板
            **kwargs: 平台特定参数

        Returns:
            BatchChatResult: 批量聊天结果
        """
        try:
            await self._ensure_session()

            # 批量聊天专属 BaseURL
            batch_base_url = kwargs.get("batch_base_url", "https://batch.dashscope.aliyuncs.com/compatible-mode/v1")
            api_endpoint = kwargs.get("api_endpoint", "/chat/completions")
            url = f"{batch_base_url}{api_endpoint}"

            # 模型参数
            model_id = getattr(params, "model_id", self.config.model_id) if params else self.config.model_id
            max_tokens = getattr(params, "max_tokens", 32000) if params else 32000
            temperature = getattr(params, "temperature", 0.7) if params else 0.7
            top_p = getattr(params, "top_p", 0.8) if params else 0.8

            # 格式化所有提示词
            formatted_prompts = [
                self.format_prompt(prompt, variables)
                for prompt in prompts
            ]

            # 构建批量请求
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                    for prompt in formatted_prompts
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.debug(f"Calling Bailian batch chat: model={model_id}, count={len(prompts)}")

            start_time = time.time()

            async with self._session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                elapsed = time.time() - start_time
                logger.debug(f"Bailian batch chat completed in {elapsed:.2f}s")

                # 提取批量任务 ID
                batch_id = result.get("id")

                return BatchChatResult(
                    success=True,
                    batch_id=batch_id,
                    status="submitted",
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Bailian HTTP request failed: {e}")
            error_msg = str(e)
            if self.config.api_key:
                error_msg = error_msg.replace(self.config.api_key, "[REDACTED]")
            return BatchChatResult(
                success=False,
                error_message=error_msg,
            )
        except Exception as e:
            logger.error(f"Bailian batch chat failed: {e}")
            error_msg = str(e)
            if self.config.api_key:
                error_msg = error_msg.replace(self.config.api_key, "[REDACTED]")
            return BatchChatResult(
                success=False,
                error_message=error_msg,
            )


# 注册适配器
AdapterRegistry.register("bailian", BailianAdapter)
