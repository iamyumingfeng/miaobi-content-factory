"""
火山引擎 AI 模型适配器 (volcano.py)

实现火山引擎平台的文本、图片、视频生成功能。

支持的模型：
- LLM: doubao-seed-2-0-pro, doubao-seed-2-0-lite, doubao-seed-2-0-mini 等
- 图像: doubao-seedream-4-0-250828, doubao-seedream-4-5-251128, doubao-seedream-5-0-260128 等
- 视频: doubao-seedance-1-5-pro, doubao-seedance-1-0-pro 等

API 文档：
- 图像生成: https://www.volcengine.com/docs/82379/1541523

Author: Claude Code
Date: 2025
"""

import json
import logging
import re
import time
from typing import List, Optional

import aiohttp

from .base import GenerationResult
from .factory import AdapterRegistry
from .image_prompts import enhance_image_prompt
from .openai_compatible import OpenAICompatibleAdapter
from .params import ImageGenParams

logger = logging.getLogger(__name__)


class VolcanoAdapter(OpenAICompatibleAdapter):
    """
    火山引擎 AI 模型适配器

    支持文本生成、图片生成（文生图、图生图、多图参考生图）、视频生成。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_TEXT_ENDPOINT = "/chat/completions"
    DEFAULT_IMAGE_ENDPOINT = "/images/generations"

    def __init__(self, config):
        super().__init__(config)
        self.platform = "volcano"

    def model_max_pixels(self, model_id: str = None) -> int:
        """火山引擎 Seedream 模型支持 4K（部分模型 2K）"""
        mid = (model_id or "").lower()
        if "seedream-4" in mid:
            return 2556  # 4.0 系列 2K
        return 4096  # 5.0 系列 4K

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """
        生成图片（文生图、图生图、多图参考生图）

        文档：https://www.volcengine.com/docs/82379/1541523

        Args:
            prompt: 提示词（已完成变量替换）
            params: 图片生成参数

        Returns:
            GenerationResult: 生成结果
        """
        p = params or ImageGenParams()
        p.model_id = p.model_id or self.config.model_id
        session = None
        try:
            formatted_prompt = prompt
            has_pair_instruction = "【参考图说明】" in formatted_prompt
            enhanced_prompt = enhance_image_prompt(
                formatted_prompt, has_reference=not has_pair_instruction
            )

            url = f"{self.base_url}{self.DEFAULT_IMAGE_ENDPOINT}"
            model_id = p.model_id
            size = self.convert_ratio_to_size(p.ratio, p.model_id, separator="x")
            reference_images: List[str] = p.reference_images or []
            watermark = (
                bool(p.watermark) if isinstance(p.watermark, int) else p.watermark
            )

            # 构建请求体
            payload = {
                "model": model_id,
                "prompt": enhanced_prompt,
                "size": size,
                "n": min(p.count, 4),
                "response_format": "url",
                "watermark": watermark,
            }

            # 添加参考图片（图生图/多图参考）
            if reference_images:
                if len(reference_images) == 1:
                    payload["image"] = reference_images[0]
                else:
                    payload["image"] = reference_images

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            # payload 日志：替换 Base64 为长度标记，其余完整输出
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(
                r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                lambda m: f"<Base64 {len(m.group(0))} chars>",
                payload_str,
            )
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()

            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                # 先读取响应体，再判断状态码
                response_text = await response.text()

                if response.status != 200:
                    # 打印详细错误响应
                    logger.error(
                        "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                    )
                    logger.error(
                        "[Image] 火山引擎图片生成失败 | status=%s | model=%s",
                        response.status,
                        model_id,
                    )
                    logger.error("[Image] 错误响应体: %s", response_text[:2000])
                    logger.error(
                        "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                    )

                    # 尝试解析错误响应
                    try:
                        error_data = json.loads(response_text)
                        error_msg = error_data.get("error", {}).get(
                            "message", response_text[:200]
                        )
                    except:
                        error_msg = response_text[:200]

                    return GenerationResult(
                        success=False,
                        error_message=f"API Error {response.status}: {error_msg}",
                        raw_response={
                            "status": response.status,
                            "body": response_text[:500],
                        },
                    )

                result = json.loads(response_text)

                elapsed = time.time() - start_time
                logger.info(
                    "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[Image] 火山引擎图片生成响应 | platform=volcano | elapsed=%.2fs | model=%s",
                    elapsed,
                    model_id,
                )
                logger.info(
                    "[Image] 响应内容: %s",
                    json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                )

                # 提取生成的图片 URL
                data = result.get("data", [])

                if not data:
                    logger.warning("[Image] 火山引擎图片生成失败：返回的 data 为空")
                    return GenerationResult(
                        success=False,
                        error_message="No image generated",
                        raw_response=result,
                    )

                image_urls = [item.get("url") for item in data if item.get("url")]
                logger.info(
                    "[Image] 生成图片数量: %d", len(image_urls) if image_urls else 0
                )
                logger.info("[Image] 图片URL: %s", image_urls[:2] if image_urls else [])
                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Volcano HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"Volcano image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def generate_video(
        self,
        prompt: str,
        variables=None,
        image_url=None,
        **kwargs,
    ):
        """
        生成视频（火山引擎暂不添加该视频生成）
        """
        return GenerationResult(
            success=False,
            error_message="Volcano does not support video generation",
        )


# 注册适配器
AdapterRegistry.register("volcano", VolcanoAdapter)
