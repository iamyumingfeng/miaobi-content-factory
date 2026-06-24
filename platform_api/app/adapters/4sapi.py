"""
4sapi 适配器 (4sapi.py)

完全独立实现的 4sapi 平台适配器，兼容 OpenAI 接口。

特性：
- 支持文本生成（gpt-4.1-mini, gpt-4.1, gpt-4o, gpt-4o-mini）
- 支持图片生成（gemini-2.5-flash-image-preview、gemini-3.1-flash-image-preview、gemini-3.1-flash-image）
- 支持图片编辑（gpt-image-2）
- Base URL: https://4sapi.com/v1
- 支持多种图片尺寸比例：1:1, 4:3, 16:9, 3:4, 9:16, 3:2, 2:3, 21:9
- 支持流式预览、参考图编辑、透明背景等特殊功能

API 文档：
- 文本生成: https://4sapi.apifox.cn/359534973e0
- 图片生成（gemini模型）: https://4sapi.apifox.cn/447631659e0
- 图片编辑（GPT-Image-2）: https://4sapi.apifox.cn/448573555e0

Author: Claude Code
Date: 2026-05-12
"""

import base64
import io
import json
import logging
import re
import tempfile
import time
from typing import Any, Dict, Optional

import aiohttp

from .base import BaseModelAdapter, GenerationResult, ModelConfig
from .factory import AdapterRegistry
from .params import ImageGenParams, TextGenParams

logger = logging.getLogger(__name__)


class FourSAPIAdapter(BaseModelAdapter):
    """
    4sapi 平台适配器

    完全独立实现，不依赖 OpenAICompatibleAdapter。
    """

    # 4sapi 默认配置
    DEFAULT_BASE_URL = "https://4sapi.com/v1"
    DEFAULT_TEXT_ENDPOINT = "/chat/completions"
    DEFAULT_IMAGE_ENDPOINT = "/images/generations"
    DEFAULT_IMAGE_EDIT_ENDPOINT = "/images/edits"

    def __init__(self, config: ModelConfig):
        """
        初始化 4sapi 适配器

        Args:
            config: 模型配置
        """
        super().__init__(config)
        self.base_url = config.base_url or self.DEFAULT_BASE_URL
        logger.info(
            f"[4sapi] 适配器初始化 | base_url={self.base_url} | model_id={config.model_id}"
        )

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

    def model_max_pixels(self, model_id: str = None) -> int:
        """4sapi 各模型的最大像素"""
        mid = (model_id or "").lower()
        if "gpt-image-2" in mid:
            return 1024  # 1K
        if any(k in mid for k in ("gemini", "imagen")):
            return 0  # Gemini 不限制像素
        return 2048  # 默认 2K

    def _convert_ratio_to_size(self, ratio: str, model_id: str = None) -> str:
        from .params import calc_pixel_size

        max_px = self.model_max_pixels(model_id)
        return calc_pixel_size(ratio, max_px) if max_px > 0 else ratio

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """生成文本内容（4sapi / OpenAI 兼容格式）"""
        session = None
        try:
            p = self._resolve_text_params(params)

            # 根据是否有 system_prompt 构建 messages
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            else:
                messages = [{"role": "user", "content": user_prompt}]

            url = f"{self.base_url}{self.DEFAULT_TEXT_ENDPOINT}"

            # 构建 payload，只包含非 None 的参数
            payload = {
                "model": p.model_id,
                "messages": messages,
            }

            # 添加可选参数（过滤 None 值）
            # if p.max_tokens is not None:
            #    payload["max_tokens"] = p.max_tokens
            if p.temperature is not None:
                payload["temperature"] = p.temperature
            if p.top_p is not None:
                payload["top_p"] = p.top_p

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            # 详细输入日志
            logger.info(
                "[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            )
            logger.info(
                "[LLM] 文案生成请求 | platform=4sapi | model=%s | url=%s",
                p.model_id,
                url,
            )
            logger.info(
                "[LLM] 参数设置 | max_tokens=%s | temperature=%s | top_p=%s",
                p.max_tokens,
                p.temperature,
                p.top_p,
            )
            # 打印完整 payload
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            logger.info("[LLM] 请求 payload: %s", payload_str)

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                # 详细错误日志
                if response.status >= 400:
                    error_body = ""
                    try:
                        error_body = await response.text()
                        logger.error(
                            "[LLM] 4sapi 文本生成失败 | status=%s | body=%s",
                            response.status,
                            error_body[:1000],
                        )
                    except Exception:
                        pass
                    response.raise_for_status()

                result = await response.json()
                elapsed = time.time() - start_time

                # 详细输出日志
                logger.info(
                    "[LLM] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[LLM] 文案生成响应 | platform=4sapi | model=%s | elapsed=%.2fs",
                    p.model_id,
                    elapsed,
                )
                # 打印完整响应
                result_str = json.dumps(result, ensure_ascii=False, indent=2)
                logger.info("[LLM] 响应内容: %s", result_str)

                choices = result.get("choices", [])
                if not choices:
                    logger.warning("[LLM] 响应中无 choices | result=%s", result)
                    return GenerationResult(
                        success=False,
                        error_message="No text generated",
                        raw_response=result,
                    )

                generated_text = choices[0].get("message", {}).get("content", "")
                logger.info(
                    "[LLM] 文案长度: %d", len(generated_text) if generated_text else 0
                )
                logger.info(
                    "[LLM] 文案预览: %s", generated_text[:200] if generated_text else ""
                )
                logger.info(
                    "[LLM] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )
                return GenerationResult(
                    success=True, text=generated_text, raw_response=result
                )

        except aiohttp.ClientError as e:
            logger.error(
                f"[4sapi] HTTP request failed [{self.classify_http_error(e)}]: {e}"
            )
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[4sapi] text generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """生成图片（4sapi），根据模型自动路由 GPT-Image / Gemini"""
        p = self._resolve_image_params(params)
        model_id_lower = (p.model_id or "").lower()

        # 根据模型名称判断：
        # - 同时包含 "gemini" 和 "image" → 使用 Gemini 图片生成接口（chat/completions + modalities）
        # - 其他模型 → 使用 GPT-Image 图片生成接口（/images/generations）
        # 注意：gemini-3.1-pro-preview 等纯文本模型不支持图片生成，不能走 Gemini 图片接口
        if "gemini" in model_id_lower:
            logger.info(f"[4sapi] 使用 Gemini 图片生成接口 | model={p.model_id}")
            return await self._generate_image_gemini(prompt, p)

        logger.info(f"[4sapi] 使用 GPT-Image 图片生成接口 | model={p.model_id}")
        return await self._generate_image_gpt(prompt, p)

    async def _generate_image_gpt(
        self,
        prompt: str,
        p: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """使用 GPT-Image 模型生成图片"""
        session = None
        try:
            p = self._resolve_image_params(p)
            if p.count > 1:
                logger.warning(f"[4sapi] count={p.count}>1 将降级为 1")
                p.count = 1

            # 格式化提示词（已完成变量替换）
            formatted_prompt = prompt

            # 处理图片尺寸（ratio -> pixel）
            normalized_size = self._convert_ratio_to_size(p.ratio, p.model_id)

            # 模型参数
            model_id = p.model_id

            # 处理参考图编辑
            reference_images = p.reference_images

            # 根据是否有参考图选择端点
            if reference_images:
                # 使用 /images/edits 端点进行参考图编辑
                api_endpoint = self.DEFAULT_IMAGE_EDIT_ENDPOINT
                url = f"{self.base_url}{api_endpoint}"
                logger.info(
                    f"[4sapi] 使用 GPT 参考图编辑接口 | model={model_id} | reference_count={len(reference_images)}"
                )

                # 创建 session
                session = await self._get_session()

                # 构建 multipart/form-data 请求
                form_data = aiohttp.FormData()
                form_data.add_field("model", model_id)
                form_data.add_field("prompt", formatted_prompt)
                form_data.add_field("n", str(p.count))
                # form_data.add_field('size', normalized_size)
                form_data.add_field("quality", "high")

                # 将 Base64 字符串解码为二进制数据，添加到 form-data
                # 注意：reference_image_urls 实际包含的是带有 data: 前缀的 Base64 字符串
                for idx, base64_str in enumerate(reference_images):
                    try:
                        # 去除 data:image/xxx;base64, 前缀（如果存在）
                        if ";base64," in base64_str:
                            pure_base64 = base64_str.split(";base64,")[1]
                        else:
                            pure_base64 = base64_str

                        # 解码 Base64
                        img_data = base64.b64decode(pure_base64)

                        # 判断图片格式（通过文件头）
                        img_format = self._detect_image_format(img_data)
                        mime_type = f"image/{img_format}"
                        ext = "png" if img_format == "png" else "jpeg"

                        # 添加到 form-data
                        form_data.add_field(
                            "image[]",
                            io.BytesIO(img_data),
                            filename=f"reference_{idx}.{ext}",
                            content_type=mime_type,
                        )
                        logger.info(
                            f"[4sapi] 添加参考图 {idx} | format={img_format} | size={len(img_data)} bytes"
                        )
                    except Exception as e:
                        logger.warning(f"[4sapi] 处理参考图失败: {e}")
                        continue

                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Accept": "application/json",
                }

                # 构建 payload 摘要（FormData 无法直接序列化，手动构建摘要）
                payload_summary = {
                    "model": model_id,
                    "prompt": formatted_prompt[:200]
                    + ("..." if len(formatted_prompt) > 200 else ""),
                    "n": p.count,
                    "quality": "high",
                    "image[]": f"<{len(reference_images)} 张参考图>",
                }

                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                )
                logger.info(
                    "[Image] GPT参考图编辑请求 | platform=4sapi | model=%s | url=%s | count=%s",
                    model_id,
                    url,
                    p.count,
                )
                logger.info(
                    "[Image] 请求 payload: %s",
                    json.dumps(payload_summary, ensure_ascii=False, indent=2),
                )

                start_time = time.time()

                async with session.post(
                    url, data=form_data, headers=headers
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    elapsed = time.time() - start_time
                    logger.info(
                        "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                    )
                    logger.info(
                        "[Image] GPT参考图编辑响应 | platform=4sapi | elapsed=%.2fs | model=%s",
                        elapsed,
                        model_id,
                    )
                    logger.info(
                        "[Image] 响应内容: %s",
                        json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                    )

                    # 提取生成的图片（支持 url 和 b64_json 两种格式）
                    data = result.get("data", [])

                    if not data:
                        logger.warning("[Image] 图片生成失败：返回的 data 为空")
                        return GenerationResult(
                            success=False,
                            error_message="No image generated",
                            raw_response=result,
                        )

                    image_urls = []
                    image_base64_list = []
                    for item in data:
                        url = item.get("url")
                        b64 = item.get("b64_json")
                        if url:
                            image_urls.append(url)
                        elif b64:
                            # 直接返回 base64 数据，不保存到临时文件
                            image_base64_list.append(b64)
                            logger.info("[Image] b64_json 直接返回 | len=%d", len(b64))

                    logger.info(
                        "[Image] 生成图片数量: urls=%d | base64=%d",
                        len(image_urls),
                        len(image_base64_list),
                    )
                    if image_urls:
                        logger.info("[Image] 图片URL: %s", image_urls[:2])
                    logger.info(
                        "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                    )

                    return GenerationResult(
                        success=True,
                        image_urls=image_urls if image_urls else None,
                        image_base64_list=(
                            image_base64_list if image_base64_list else None
                        ),
                        raw_response=result,
                    )

            else:
                # 使用 /images/generations 端点进行普通图片生成
                api_endpoint = self.DEFAULT_IMAGE_ENDPOINT
                url = f"{self.base_url}{api_endpoint}"

                # 构建请求 payload
                payload = {
                    "model": model_id,
                    "prompt": formatted_prompt,
                    "n": p.count,
                    # "size": normalized_size,
                }

                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                )
                logger.info(
                    "[Image] 图片生成请求 | platform=4sapi | model=%s | url=%s | count=%s",
                    model_id,
                    url,
                    p.count,
                )
                # payload 日志：替换 Base64 为长度标记，其余完整输出
                payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
                payload_str = re.sub(
                    r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                    lambda m: f"<Base64 {len(m.group(0))} chars>",
                    payload_str,
                )
                logger.info("[Image] 请求 payload: %s", payload_str)
                logger.info(
                    "[Image] 图片尺寸设置 | original=%s | normalized=%s",
                    p.ratio,
                    normalized_size,
                )

                start_time = time.time()

                if session is None:
                    session = await self._get_session()
                async with session.post(url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    result = await response.json()

                    elapsed = time.time() - start_time
                    logger.info(
                        "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                    )
                    logger.info(
                        "[Image] 图片生成响应 | platform=4sapi | elapsed=%.2fs | model=%s",
                        elapsed,
                        model_id,
                    )
                    logger.info(
                        "[Image] 响应内容: %s",
                        json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                    )

                    # 提取生成的图片（支持 url 和 b64_json 两种格式）
                    data = result.get("data", [])

                    if not data:
                        logger.warning("[Image] 图片生成失败：返回的 data 为空")
                        return GenerationResult(
                            success=False,
                            error_message="No image generated",
                            raw_response=result,
                        )

                    image_urls = []
                    image_base64_list = []
                    for item in data:
                        url = item.get("url")
                        b64 = item.get("b64_json")
                        if url:
                            image_urls.append(url)
                        elif b64:
                            # 直接返回 base64 数据，不保存到临时文件
                            image_base64_list.append(b64)
                            logger.info("[Image] b64_json 直接返回 | len=%d", len(b64))

                    logger.info(
                        "[Image] 生成图片数量: urls=%d | base64=%d",
                        len(image_urls),
                        len(image_base64_list),
                    )
                    if image_urls:
                        logger.info("[Image] 图片URL: %s", image_urls[:2])
                    logger.info(
                        "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                    )

                    return GenerationResult(
                        success=True,
                        image_urls=image_urls if image_urls else None,
                        image_base64_list=(
                            image_base64_list if image_base64_list else None
                        ),
                        raw_response=result,
                    )

        except aiohttp.ClientError as e:
            error_type = self.classify_http_error(e)
            logger.error(f"[4sapi] HTTP request failed [{error_type}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[4sapi] image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def _generate_image_gemini(
        self,
        prompt: str,
        p: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """
        使用 Gemini 模型生成图片

        API 文档: https://4sapi.apifox.cn/359535009e0 (参考图编辑)

        特点：
        - 使用 chat/completions 端点
        - 必须设置 modalities: ["text", "image"]
        - 图片以 Base64 格式返回
        - 支持参考图编辑：使用 content 数组格式，包含 text 和 image_url 对象
        - 支持本地文件路径，会自动转换为 base64 data URL

        Args:
            prompt: 提示词模板
            variables: 变量字典
            **kwargs: 平台特定参数
                - model_id: 模型ID（可选，默认使用 config.model_id）
                - stream: 是否流式输出（默认 False）
                - reference_image_paths: 参考图片本地路径列表（用于参考图编辑）

        Returns:
            GenerationResult: 生成结果，包含 Base64 图片
        """
        session = None
        try:
            # 格式化提示词（已完成变量替换）
            formatted_prompt = prompt

            # 构建请求
            url = f"{self.base_url}{self.DEFAULT_TEXT_ENDPOINT}"

            # 模型参数
            model_id = p.model_id
            stream = False

            # 处理参考图
            reference_images = p.reference_images

            # 构建 content（根据是否有参考图决定格式）
            if reference_images:
                # 使用数组格式：包含文本和参考图
                logger.info(
                    f"[GeminiImage] 使用参考图编辑 | count={len(reference_images)}"
                )
                content = [{"type": "text", "text": formatted_prompt}]

                # 添加参考图（直接使用 data URL 格式）
                # 注意：reference_image_urls 实际包含的是带有 data: 前缀的 Base64 字符串
                for idx, base64_str in enumerate(reference_images):
                    try:
                        # 确保是 data URL 格式（如果已经有 data: 前缀，直接使用；否则添加前缀）
                        if base64_str.startswith("data:image/"):
                            data_url = base64_str
                        else:
                            # 判断图片格式（通过 Base64 解码后的文件头）
                            if ";base64," in base64_str:
                                pure_base64 = base64_str.split(";base64,")[1]
                            else:
                                pure_base64 = base64_str
                            img_data = base64.b64decode(pure_base64)
                            img_format = self._detect_image_format(img_data)
                            mime_type = f"image/{img_format}"
                            data_url = f"data:{mime_type};base64,{pure_base64}"

                        content.append(
                            {"type": "image_url", "image_url": {"url": data_url}}
                        )
                        logger.info(
                            f"[GeminiImage] 添加参考图 {idx} | data_url_len={len(data_url)}"
                        )
                    except Exception as e:
                        logger.warning(f"[GeminiImage] 处理参考图失败: {e}")
                        continue
            else:
                # 纯文本格式
                content = formatted_prompt

            # 构建 payload（必须包含 modalities 参数）
            payload = {
                "model": model_id,
                "stream": stream,
                "messages": [{"role": "user", "content": content}],
                "n": p.count,
                "temperature": 0.7,
                "quality": "high",
                "modalities": ["text", "image"],  # 关键参数
            }

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            logger.info(
                "[GeminiImage] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            )
            logger.info(
                "[GeminiImage] Gemini 图片生成 | model=%s | url=%s", model_id, url
            )
            logger.info("[GeminiImage] 提示词: %s", formatted_prompt[:200])
            logger.info(
                "[GeminiImage] 参考图数量: %d",
                len(reference_images) if reference_images else 0,
            )

            # 打印完整 payload（替换 Base64 为长度标记）
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(
                r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                lambda m: f"<Base64 {len(m.group(0))} chars>",
                payload_str,
            )
            logger.info("[GeminiImage] 请求 payload: %s", payload_str)

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                elapsed = time.time() - start_time
                logger.info(
                    "[GeminiImage] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[GeminiImage] Gemini 图片生成响应 | elapsed=%.2fs", elapsed
                )

                # 输出完整响应（用于调试）
                result_str = json.dumps(result, ensure_ascii=False, indent=2)
                if len(result_str) > 2000:
                    result_str = result_str[:2000] + "...(截断)"
                logger.info("[GeminiImage] 响应内容: %s", result_str)

                # 提取 Base64 图片
                choices = result.get("choices", [])
                if not choices:
                    logger.warning("[GeminiImage] 图片生成失败：返回的 choices 为空")
                    return GenerationResult(
                        success=False,
                        error_message="No image generated",
                        raw_response=result,
                    )

                message = choices[0].get("message", {})
                content = message.get("content", "")

                # 提取 Base64 图片数据（支持多种格式）
                image_urls = []
                image_base64_list = []

                # 格式1：content 是字符串，包含 markdown 格式 ![image](data:image/...)
                if isinstance(content, str):
                    # 尝试从 markdown 格式中提取
                    match = re.search(
                        r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", content
                    )
                    if match:
                        base64_str = match.group(0)
                        logger.info(
                            "[GeminiImage] 提取到 Base64 图片（markdown格式）| length=%d",
                            len(base64_str),
                        )
                        image_base64_list.append(base64_str)
                    else:
                        # 尝试直接匹配 data URL（无 markdown 包装）
                        if content.startswith("data:image/"):
                            logger.info(
                                "[GeminiImage] 提取到 Base64 图片（直接data URL）| length=%d",
                                len(content),
                            )
                            image_base64_list.append(content)
                        else:
                            logger.warning(
                                "[GeminiImage] content 字符串中未找到图片数据 | content_len=%d | content_preview=%s",
                                len(content),
                                content[:200],
                            )

                # 格式2：content 是数组，包含多个内容块（文本 + 图片）
                elif isinstance(content, list):
                    logger.info(
                        "[GeminiImage] content 是数组格式 | len=%d", len(content)
                    )
                    for item in content:
                        if isinstance(item, dict):
                            # 检查是否是图片类型
                            item_type = item.get("type", "")
                            if item_type == "image_url":
                                # 格式：{"type": "image_url", "image_url": {"url": "data:image/..."}}
                                image_url_obj = item.get("image_url", {})
                                url = image_url_obj.get("url", "")
                                if url.startswith("data:image/"):
                                    logger.info(
                                        "[GeminiImage] 提取到 Base64 图片（数组格式）| length=%d",
                                        len(url),
                                    )
                                    image_base64_list.append(url)
                            elif item_type == "text":
                                # 文本内容，跳过
                                logger.debug(
                                    "[GeminiImage] 跳过文本块 | text=%s",
                                    item.get("text", "")[:100],
                                )

                # 格式3：content 为空，检查 message 的其他字段
                else:
                    logger.warning(
                        "[GeminiImage] content 类型未知 | type=%s | content=%s",
                        type(content).__name__,
                        str(content)[:200],
                    )

                logger.info(
                    "[GeminiImage] 图片提取结果 | base64_count=%d",
                    len(image_base64_list),
                )
                logger.info(
                    "[GeminiImage] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls if image_urls else None,
                    image_base64_list=image_base64_list if image_base64_list else None,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            error_type = self.classify_http_error(e)
            logger.error(f"[4sapi] HTTP request failed [{error_type}]: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[4sapi] Gemini image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_video(
        self,
        prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
    ) -> GenerationResult:
        """
        生成视频（4sapi 不支持）

        Args:
            prompt: 提示词模板
            variables: 变量字典，用于填充提示词模板
            image_url: 参考图片URL（可选）

        Returns:
            GenerationResult: 生成结果
        """
        return GenerationResult(
            success=False,
            error_message="4sapi does not support video generation",
        )

    async def check_availability(self) -> bool:
        """
        检查 4sapi 平台是否可用

        Returns:
            bool: 是否可用
        """
        session = None
        try:
            url = f"{self.base_url}/models"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
            }

            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                return response.status == 200

        except Exception as e:
            # 安全记录错误，过滤敏感信息
            error_msg = str(e)
            if hasattr(self, "config") and hasattr(self.config, "api_key"):
                api_key = getattr(self.config, "api_key", "")
                if api_key:
                    error_msg = error_msg.replace(api_key, "[REDACTED]")
            logger.warning(f"[4sapi] availability check failed: {error_msg}")
            return False
        finally:
            if session:
                await self._close_session(session)

    @staticmethod
    def _detect_image_format(img_data: bytes) -> str:
        """
        通过文件头检测图片格式

        Args:
            img_data: 图片二进制数据

        Returns:
            str: 图片格式（'png', 'jpeg', 'webp', 'gif'），默认 'jpeg'
        """
        # PNG: 89 50 4E 47
        if img_data[:4] == b"\x89PNG":
            return "png"
        # JPEG: FF D8 FF
        elif img_data[:2] == b"\xff\xd8":
            return "jpeg"
        # WebP: 52 49 46 46 ... 57 45 42 50
        elif img_data[:4] == b"RIFF" and img_data[8:12] == b"WEBP":
            return "webp"
        # GIF: 47 49 46 38
        elif img_data[:4] == b"GIF8":
            return "gif"
        else:
            # 默认返回 jpeg
            return "jpeg"

    @staticmethod
    def _save_base64_to_temp(base64_data: str) -> str:
        """将 Base64 图片数据保存为临时文件，返回文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(base64.b64decode(base64_data))
            return f.name


# 注册适配器到工厂
AdapterRegistry.register("4sapi", FourSAPIAdapter)

logger.info("[4sapi] 适配器已注册到工厂")
