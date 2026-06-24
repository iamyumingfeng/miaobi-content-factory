"""
即梦 AI 模型适配器 (jimeng.py)

实现即梦平台的图片、视频生成功能。

支持的模型：
- jimeng_t2i_v40: 图片生成4.0
- jimeng_seedream46_cvtob: 图片生成4.6
- jimeng_ti2v_v30_pro: 视频生成3.0 Pro

注意：即梦AI使用火山引擎 Header 签名认证

Author: Claude Code
Date: 2025
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional, Tuple


from .base import BaseModelAdapter, GenerationResult, ModelConfig
from .factory import AdapterRegistry
from .image_prompts import enhance_image_prompt
from .params import ImageGenParams, TextGenParams

# 即梦 v46 异步任务轮询配置
JIMENG_V46_POLL_INTERVAL = 5
JIMENG_V46_POLL_TIMEOUT = 300

logger = logging.getLogger(__name__)


class JimengAdapter(BaseModelAdapter):
    """
    即梦 AI 模型适配器

    使用火山引擎 Header 签名认证（HMAC-SHA256）。
    """

    DEFAULT_BASE_URL = "https://visual.volcengineapi.com"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or self.DEFAULT_BASE_URL
        self.platform = "jimeng"

        config_json = config.extra_params or {}
        self.access_key = config_json.get("access_key", "")
        self.secret_key = config_json.get("secret_key", "")

        logger.info(
            "[Jimeng] 适配器初始化 | model_id=%s | access_key_len=%d | secret_key_len=%d",
            config.model_id,
            len(self.access_key),
            len(self.secret_key),
        )

    def _build_url(self, query_params: dict) -> str:
        """构建 URL（仅包含 Action 和 Version）"""
        import urllib.parse

        sorted_query = sorted(query_params.items())
        query = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_query
        )
        return f"{self.base_url}?{query}"

    def _sign_request(
        self,
        method: str,
        path: str,
        query_params: dict,
        body: str,
    ) -> dict:
        """
        生成火山引擎 Header 签名

        文档：https://www.volcengine.com/docs/6348/71161

        签名 header 包含：
        - Authorization: HMAC-SHA256 Credential=..., SignedHeaders=..., Signature=...
        - X-Date: UTC 时间
        - X-Content-Sha256: body 的 SHA256
        """
        if not self.access_key or not self.secret_key:
            return {}

        import urllib.parse

        now = datetime.utcnow()
        short_date = now.strftime("%Y%m%d")
        date_str = now.strftime("%Y%m%dT%H%M%SZ")

        host = "visual.volcengineapi.com"
        region = "cn-north-1"
        service = "cv"

        # 1. CanonicalQueryString（对参数进行 URL 编码）
        sorted_query = sorted(query_params.items())
        canonical_query = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_query
        )

        # 2. Body hash
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        # 3. CanonicalHeaders（content-type + host + x-content-sha256 + x-date，按字母序）
        canonical_headers = (
            f"content-type:application/json\n"
            f"host:{host}\n"
            f"x-content-sha256:{body_hash}\n"
            f"x-date:{date_str}\n"
        )
        signed_headers = "content-type;host;x-content-sha256;x-date"

        # 4. CanonicalRequest（注意 canonical_headers 和 signed_headers 之间要有一个换行）
        canonical_request = (
            f"{method.upper()}\n"
            f"{path}\n"
            f"{canonical_query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{body_hash}"
        )

        logger.debug("[Jimeng] CanonicalRequest: %s", repr(canonical_request))

        # 5. StringToSign
        credential_scope = f"{short_date}/{region}/{service}/request"
        canonical_request_hash = hashlib.sha256(canonical_request.encode()).hexdigest()
        string_to_sign = "\n".join(
            [
                "HMAC-SHA256",
                date_str,
                credential_scope,
                canonical_request_hash,
            ]
        )

        logger.debug("[Jimeng] StringToSign: %s", repr(string_to_sign))

        # 6. 计算签名（火山引擎要求密钥前加上前缀 "VolcSK"？）
        # 火山引擎签名算法：https://www.volcengine.com/docs/6348/71161
        secret_key_bytes = self.secret_key.encode("utf-8")

        k_date = hmac.new(
            secret_key_bytes,
            short_date.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
        signature = hmac.new(
            k_signing,
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # 7. Authorization header
        authorization = (
            f"HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        logger.debug("[Jimeng] Authorization: %s", authorization)

        return {
            "Authorization": authorization,
            "X-Date": date_str,
            "X-Content-Sha256": body_hash,
        }

    def _post_sync(
        self, query_params: dict, body: str, timeout: float = 60.0
    ) -> Tuple[int, str]:
        """
        使用 urllib 发送签名 POST 请求

        urllib 完全控制 URL、body 和 header，不会自动添加或修改任何内容。
        """
        url = self._build_url(query_params)
        body_bytes = body.encode("utf-8")
        headers = self._sign_request("POST", "/", query_params, body)
        headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url, data=body_bytes, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def model_max_pixels(self, model_id: str = None) -> int:
        """模型对应的最大像素（1K=1024, 2K=2048, 4K=4096）"""
        mid = (model_id or "").lower()
        # 按模型细分
        if "gpt-image-2" in mid or "dall-e-2" in mid:
            return 1024
        if "dall-e-3" in mid:
            return 4096
        if "gemini" in mid or "imagen" in mid:
            return 0  # 不限制
        return 4096  # 平台默认

    def _convert_ratio_to_size(self, ratio: str, model_id: str = None) -> str:
        """根据模型能力将比例转为像素尺寸"""
        from .params import calc_pixel_size

        max_px = self.model_max_pixels(model_id)
        return calc_pixel_size(ratio, max_px, separator="x") if max_px > 0 else ratio

    async def _post_signed(
        self, query_params: dict, body: str, timeout: float = 60.0
    ) -> Tuple[int, str]:
        """在异步上下文中发送签名请求"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._post_sync(query_params, body, timeout)
        )

    async def cleanup(self):
        pass

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        return GenerationResult(
            success=False,
            error_message="Jimeng does not support text generation",
        )

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        p = params or ImageGenParams()
        model_id = p.model_id if p else self.config.model_id
        if model_id == "jimeng_seedream46_cvtob":
            return await self._generate_image_v46(prompt, p)
        else:
            return await self._generate_image_v40(prompt, p)

    # ========== v40 图片生成（CVProcess 同步接口） ==========

    async def _generate_image_v40(
        self, prompt: str, p: ImageGenParams
    ) -> GenerationResult:
        try:
            model_id = p.model_id if p else "jimeng_t2i_v40"
            size = self._convert_ratio_to_size(p.ratio if p else "3:4", model_id)
            watermark = p.watermark if p else True
            ref_images = p.reference_images or []
            image = ref_images[0] if ref_images else None
            strength = 0.5

            # 验证参考图片URL是否支持（火山引擎不支持data URL）
            image_urls_to_check = []
            if isinstance(image, list):
                image_urls_to_check.extend(image)
            elif image:
                image_urls_to_check.append(image)
            if isinstance(ref_images, list):
                image_urls_to_check.extend(ref_images)

            for url in image_urls_to_check:
                if isinstance(url, str) and url.startswith("data:"):
                    logger.error(
                        "[Image] 即梦API不支持data URL（base64编码），请使用公网HTTP/HTTPS URL | url=%s...",
                        url[:100],
                    )
                    return GenerationResult(
                        success=False,
                        error_message="即梦API不支持data URL（base64编码），请确保已正确配置COS并使用公网URL",
                    )

            payload = {
                "req_key": "jimeng_high_aes_general_v21_L",
                "prompt": enhance_image_prompt(prompt),
                "model": model_id,
                "size": size,
                "watermark": watermark,
            }
            if image:
                payload["image"] = image
                payload["strength"] = strength

            body = json.dumps(payload)
            query_params = {"Action": "CVProcess", "Version": "2022-08-31"}

            logger.info(
                "[Image] 即梦v40请求 | model=%s | payload=%s",
                model_id,
                json.dumps(payload, ensure_ascii=False)[:2000],
            )

            start_time = time.time()
            status, text = await self._post_signed(query_params, body, timeout=600)
            elapsed = time.time() - start_time

            if status >= 400:
                logger.error(
                    "[Image] 即梦v40失败 | status=%d | body=%s", status, text[:500]
                )
                error_type = "server_error" if status >= 500 else "client_error"
                return GenerationResult(
                    success=False,
                    error_message=f"HTTP {status}: {text[:500]}",
                    error_type=error_type,
                )

            result = json.loads(text)
            data = result.get("data", {})
            task_status = data.get("task_status", "")

            if task_status in ["succeed", "SUCCESS"]:
                images = data.get("data", [])
                image_urls = [img.get("url") for img in images if img.get("url")]
                logger.info(
                    "[Image] 即梦v40成功 | 图片数=%d | elapsed=%.2fs",
                    len(image_urls),
                    elapsed,
                )
                return GenerationResult(
                    success=True, image_urls=image_urls or None, raw_response=result
                )
            else:
                logger.warning("[Image] 即梦v40状态: %s", task_status)
                return GenerationResult(
                    success=False,
                    error_message=f"Task status: {task_status}",
                    raw_response=result,
                    error_type="client_error",
                )

        except Exception as e:
            logger.error(f"Jimeng v40 failed: {e}")
            return self.handle_error(e)

    # ========== v46 图片生成（异步接口） ==========

    async def _generate_image_v46(
        self, prompt: str, p: ImageGenParams
    ) -> GenerationResult:
        try:
            model_id = p.model_id if p else "jimeng_seedream46_cvtob"
            start_time = time.time()

            ref_images = p.reference_images or []
            image = ref_images[0] if ref_images else None

            # 验证参考图片URL是否支持（火山引擎不支持data URL）
            image_urls_to_check = []
            if isinstance(image, list):
                image_urls_to_check.extend(image)
            elif image:
                image_urls_to_check.append(image)
            if isinstance(ref_images, list):
                image_urls_to_check.extend(ref_images)

            for url in image_urls_to_check:
                if isinstance(url, str) and url.startswith("data:"):
                    logger.error(
                        "[Image] 即梦API不支持data URL（base64编码），请使用公网HTTP/HTTPS URL | url=%s...",
                        url[:100],
                    )
                    return GenerationResult(
                        success=False,
                        error_message="即梦API不支持data URL（base64编码），请确保已正确配置COS并使用公网URL",
                    )

            payload = {
                "req_key": "jimeng_seedream46_cvtob",
                "prompt": enhance_image_prompt(prompt),
            }

            if image:
                payload["image_urls"] = (
                    image[:14] if isinstance(image, list) else [image]
                )

            raw_size = p.ratio if p else "3:4"
            if raw_size and "x" in str(raw_size):
                w, h = raw_size.split("x")
                payload["width"] = int(w)
                payload["height"] = int(h)
            else:
                size = self._convert_ratio_to_size(raw_size)
                if size and "x" in str(size):
                    w, h = size.split("x")
                    payload["width"] = int(w)
                    payload["height"] = int(h)
                else:
                    payload["width"] = 2048
                    payload["height"] = 2048

            if p and p.count == 1:
                payload["force_single"] = True

            watermark = p.watermark if p else True
            if watermark is True or (
                isinstance(watermark, str) and str(watermark).lower() == "true"
            ):
                payload["watermark"] = True

            body = json.dumps(payload)
            submit_params = {
                "Action": "CVSync2AsyncSubmitTask",
                "Version": "2022-08-31",
            }

            logger.info(
                "[Image] 即梦v46提交 | model=%s | payload=%s",
                model_id,
                json.dumps(payload, ensure_ascii=False)[:2000],
            )

            status, text = await self._post_signed(submit_params, body, timeout=60)

            if status >= 400:
                logger.error(
                    "[Image] 即梦v46提交失败 | status=%d | body=%s", status, text[:2000]
                )
                error_type = "server_error" if status >= 500 else "client_error"
                return GenerationResult(
                    success=False,
                    error_message=f"HTTP {status}: {text[:500]}",
                    error_type=error_type,
                )

            try:
                submit_result = json.loads(text)
            except json.JSONDecodeError:
                logger.error("[Image] 即梦v46提交响应JSON解析失败 | text=%s", text[:500])
                return GenerationResult(
                    success=False,
                    error_message="Submit response JSON parse failed",
                    error_type="client_error",
                )
            code = submit_result.get("code")
            message = submit_result.get("message", "")
            submit_data = submit_result.get("data") or {}
            task_id = submit_data.get("task_id") if isinstance(submit_data, dict) else None

            if code != 10000:
                logger.error(
                    "[Image] 即梦v46提交失败 | code=%s | message=%s", code, message
                )
                return GenerationResult(
                    success=False,
                    error_message=f"code={code}, message={message}",
                    error_type="client_error",
                )

            if not task_id:
                logger.error("[Image] 即梦v46提交成功但未返回 task_id")
                return GenerationResult(
                    success=False,
                    error_message="No task_id returned",
                    error_type="client_error",
                )

            logger.info("[Image] 即梦v46任务已提交 | task_id=%s", task_id)

            image_urls = await self._poll_v46_task(task_id, model_id, start_time)

            return GenerationResult(
                success=True, image_urls=image_urls or None, raw_response=submit_result
            )

        except Exception as e:
            logger.error(f"Jimeng v46 failed: {e}")
            return self.handle_error(e)

    async def _poll_v46_task(
        self,
        task_id: str,
        model_id: str,
        start_time: float,
        timeout: float = JIMENG_V46_POLL_TIMEOUT,
        interval: float = JIMENG_V46_POLL_INTERVAL,
    ) -> list:
        """轮询即梦 v46 异步任务结果"""
        poll_count = 0
        query_params = {"Action": "CVSync2AsyncGetResult", "Version": "2022-08-31"}

        while time.time() - start_time < timeout:
            poll_count += 1
            # 按文档：查询时通过 req_json 传入 return_url=true，使返回结果包含公网 URL
            req_json = json.dumps({"return_url": True})
            query_body = json.dumps(
                {
                    "req_key": "jimeng_seedream46_cvtob",
                    "task_id": task_id,
                    "req_json": req_json,
                }
            )

            status, text = await self._post_signed(query_params, query_body, timeout=60)
            if not text:
                logger.warning("[Image] 即梦v46轮询返回空响应")
                await asyncio.sleep(interval)
                continue
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("[Image] 即梦v46轮询响应JSON解析失败 | text=%s", text[:200])
                await asyncio.sleep(interval)
                continue
            code = result.get("code")
            message = result.get("message", "")
            # 文档：code!=10000 时 data 为 null，需用 or {} 处理
            resp_data = result.get("data") or {}
            resp_status = resp_data.get("status", "") if isinstance(resp_data, dict) else ""

            elapsed = time.time() - start_time
            logger.debug(
                "[Image] 即梦v46轮询 | poll#%d | status=%s | code=%s | elapsed=%.1fs",
                poll_count,
                resp_status,
                code,
                elapsed,
            )

            # 按文档：优先判断 code==10000，再判断 data.status
            if code == 10000:
                if resp_status == "done":
                    # 优先使用 image_urls（需 return_url=true），回退到 base64
                    image_urls = resp_data.get("image_urls", [])
                    if not image_urls:
                        # 尝试从 binary_data_base64 解析（兜底）
                        b64_list = resp_data.get("binary_data_base64", [])
                        if b64_list:
                            logger.info(
                                "[Image] 即梦v46完成（base64）| task_id=%s | 图片数=%d",
                                task_id,
                                len(b64_list),
                            )
                            return []  # base64 暂时不处理，返回空列表
                    logger.info(
                        "[Image] 即梦v46完成 | task_id=%s | 图片数=%d",
                        task_id,
                        len(image_urls),
                    )
                    return image_urls
                elif resp_status in ("in_queue", "generating"):
                    await asyncio.sleep(interval)
                elif resp_status == "not_found":
                    raise ValueError(f"Task not found: {task_id}")
                elif resp_status == "expired":
                    raise ValueError(f"Task expired: {task_id}")
                else:
                    logger.warning("[Image] 即梦v46未知状态: %s", resp_status)
                    await asyncio.sleep(interval)
            else:
                logger.warning(
                    "[Image] 即梦v46错误 | code=%s | message=%s", code, message
                )
                # 可重试的错误码：50429(QPS超限)、50430(并发超限)、50500(内部错误)
                if code in [50429, 50430, 50500]:
                    await asyncio.sleep(interval)
                else:
                    raise ValueError(f"Query failed: code={code}, message={message}")

        raise TimeoutError(f"Jimeng v46 timeout after {timeout}s")

    # ========== 视频生成 ==========

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model_id: Optional[str] = None,
        resolution: str = "1080p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
    ) -> GenerationResult:
        try:
            if model_id is None:
                model_id = "jimeng_ti2v_v30_pro"

            payload = {
                "model": model_id,
                "prompt": prompt,
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "seed": seed,
            }
            if image_url:
                payload["images"] = (
                    image_url if isinstance(image_url, list) else [image_url]
                )

            body = json.dumps(payload)
            query_params = {"Action": "CVProcess", "Version": "2022-08-31"}

            status, text = await self._post_signed(query_params, body, timeout=600)

            if status >= 400:
                error_type = "server_error" if status >= 500 else "client_error"
                return GenerationResult(
                    success=False,
                    error_message=f"HTTP {status}: {text[:500]}",
                    error_type=error_type,
                )

            result = json.loads(text)
            return GenerationResult(success=True, video_url=None, raw_response=result)

        except Exception as e:
            logger.error(f"Jimeng video failed: {e}")
            return self.handle_error(e)

    # ========== 其他 ==========

    async def check_availability(self) -> bool:
        return bool(self.access_key and self.secret_key)


AdapterRegistry.register("jimeng", JimengAdapter)
