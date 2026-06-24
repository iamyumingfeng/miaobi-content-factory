"""
可灵 AI 模型适配器 (kling.py)

实现可灵平台的图片生成功能。

支持模型（根据 https://klingai.com/document-api/apiReference/model/imageModels）：

【标准图像生成】/v1/images/generations
- kling-v1: 基础版，文生图 + 图生图
- kling-v1.5: 增强版，支持 face/subject 参考类型
- kling-v2: 多图参考生图
- kling-v2-new / kling-v2-1: v2 增强版本
- kling-v3: 最新版图像生成

【Omni 全模态生成】/v1/images/omni-image
- kling-image-o1: 全模态图像生成（多图输入、主体参考、组图模式）
- kling-v3-omni: v3 版本全模态

【多图参考生图】/v1/images/multi-image2image
- kling-v2 系列：主体图+场景图+风格图组合生图

认证方式（参考 https://klingai.com/document-api/apiReference/commonInfo）：
- 使用 JWT (HS256) 动态生成 Token
- 需要配置 access_key_id + access_key_secret（非静态 API Key）
- Token 有效期 30 分钟，自动缓存和刷新

API 端点：https://api.klingai.com
文档参考：
- https://klingai.com/document-api/apiReference/model/imageGeneration
- https://klingai.com/document-api/apiReference/model/OmniImage
- https://klingai.com/document-api/apiReference/model/multiImageToImage

Author: Claude Code
Date: 2025
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import aiohttp

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None

from .base import BaseModelAdapter, GenerationResult, ModelConfig
from .factory import AdapterRegistry
from .image_prompts import enhance_image_prompt, get_negative_prompt
from .params import ImageGenParams, TextGenParams

logger = logging.getLogger(__name__)

# JWT Token 默认有效期（秒）
KLING_TOKEN_EXPIRE_SECONDS = 1800  # 30 分钟

# 异步任务轮询配置
KLING_POLL_INTERVAL = 5  # 轮询间隔（秒）
KLING_POLL_TIMEOUT = 300  # 轮询超时（秒，5 分钟）
KLING_POLL_MAX_ATTEMPTS = 60  # 最大轮询次数


class KlingAdapter(BaseModelAdapter):
    """
    可灵 AI 模型适配器

    支持标准图像生成、Omni 全模态生成、多图参考生图。

    认证：使用 AccessKey ID + SecretKey 动态生成 JWT Token。
    """

    # 默认 API 端点
    DEFAULT_BASE_URL = "https://api.klingai.com"

    # ========== 模型配置表 ==========
    # 来源：https://klingai.com/document-api/apiReference/model/imageModels
    MODELS = {
        # --- 标准图像生成系列 ---
        "kling-v1": {
            "endpoint": "/v1/images/generations",
            "type": "standard",
            "description": "基础版图像生成",
        },
        "kling-v1.5": {
            "endpoint": "/v1/images/generations",
            "type": "standard",
            "description": "增强版（支持face/subject参考）",
        },
        "kling-v2-new": {
            "endpoint": "/v1/images/generations",
            "type": "standard",
            "description": "V2 新版",
        },
        "kling-v3": {
            "endpoint": "/v1/images/generations",
            "type": "standard",
            "description": "最新 V3 图像生成",
        },
        # --- Omni 全模态系列 ---
        "kling-image-o1": {
            "endpoint": "/v1/images/omni-image",
            "type": "omni",
            "description": "Omni 全模态图像生成",
        },
        "kling-v3-omni": {
            "endpoint": "/v1/images/omni-image",
            "type": "omni",
            "description": "V3 全模态图像生成",
        },
        # --- 多图参考生图 ---
        "kling-v2": {
            "endpoint": "/v1/images/multi-image2image",
            "type": "multi",
            "description": "多图参考生图（主体+场景+风格）",
        },
        "kling-v2-1": {
            "endpoint": "/v1/images/multi-image2image",
            "type": "multi",
            "description": "多图参考生图（主体+场景+风格）",
        },
    }

    # 标准生成的 aspect_ratio 映射到可灵格式
    ASPECT_RATIO_MAP = {
        "1:1": "1:1",
        "4:3": "4:3",
        "16:9": "16:9",
        "3:4": "3:4",
        "9:16": "9:16",
        "3:2": "3:2",  # 可灵额外支持
        "2:3": "2:3",  # 可灵额外支持
        "21:9": "21:9",  # 可灵额外支持
    }

    # 各模型默认分辨率
    DEFAULT_RESOLUTIONS = {
        "kling-v3-omni": "4k",
        "kling-image-o1": "2k",
        "kling-v3": "2k",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or self.DEFAULT_BASE_URL
        self.platform = "kling"

        # 从 extra_params 提取 AccessKey（可灵使用动态 JWT Token 认证）
        self._access_key_id: str = ""
        self._access_key_secret: str = ""
        if config.extra_params:
            self._access_key_id = config.extra_params.get("access_key_id", "")
            self._access_key_secret = config.extra_params.get("access_key_secret", "")

        # JWT Token 缓存
        self._cached_token: Optional[str] = None
        self._token_expire_time: float = 0  # token 过期时间戳

    def model_max_pixels(self, model_id: str = None) -> int:
        """
        返回模型支持的较大边最大像素

        可灵模型像素限制：
        - kling-v3-omni: 4K (3840px)
        - kling-image-o1: 2K (2048px)
        - kling-v3: 2K (2048px)
        - 其他: 2K (2048px)
        """
        model = model_id or self.config.model_id
        resolution = self.DEFAULT_RESOLUTIONS.get(model, "2k")

        # 分辨率到像素的映射
        pixel_map = {
            "4k": 3840,
            "2k": 2048,
            "1k": 1024,
        }
        return pixel_map.get(resolution, 2048)

    async def _get_session(self):
        """创建临时会话"""
        timeout = aiohttp.ClientTimeout(total=600.0)
        return aiohttp.ClientSession(timeout=timeout)

    async def _close_session(self, session: aiohttp.ClientSession):
        """关闭临时会话"""
        if session and not session.closed:
            await session.close()

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional[TextGenParams] = None,
    ) -> GenerationResult:
        """生成文本（可灵不支持文本生成）"""
        return GenerationResult(
            success=False,
            error_message="Kling does not support text generation",
        )

    def _resolve_model_config(self, model_id: str) -> Dict[str, Any]:
        """解析模型配置，支持前缀匹配"""
        if model_id in self.MODELS:
            return self.MODELS[model_id]

        # 前缀匹配
        for key in sorted(self.MODELS.keys(), key=len, reverse=True):
            if model_id.startswith(key) and not key.endswith("multi"):
                return self.MODELS[key]

        # 兼容旧版命名
        legacy_map = {
            "kling-v2": {"endpoint": "/v1/images/multi-image2image", "type": "multi"},
        }
        if model_id.startswith("kling-v2") and "multi" in model_id:
            return legacy_map["kling-v2"]

        # 默认使用 kling-v2-1
        logger.warning("[Kling] 未识别的模型 %s，默认使用 kling-v2-1 配置", model_id)
        return self.MODELS["kling-v2-1"]

    def _build_common_headers(self) -> Dict[str, str]:
        """构建通用请求头（使用动态 JWT Token）"""
        token = self._get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get_valid_token(self) -> str:
        """
        获取有效的 JWT Token

        优先使用缓存的 Token，过期或不存在时重新生成。
        可灵 API 使用 AccessKey ID + SecretKey 签名生成 JWT。

        Returns:
            str: 有效的 Bearer Token
        """
        now = time.time()

        # 检查缓存是否有效（提前 60 秒刷新，留余量）
        if self._cached_token and now < (self._token_expire_time - 60):
            return self._cached_token

        # 需要重新生成
        new_token = self._generate_jwt_token()
        if new_token:
            self._cached_token = new_token
            self._token_expire_time = now + KLING_TOKEN_EXPIRE_SECONDS
            logger.debug(
                "[Kling] JWT Token 已刷新 | 有效期 %d 秒 | 过期时间: %.0f",
                KLING_TOKEN_EXPIRE_SECONDS,
                self._token_expire_time,
            )
            return new_token

        # 回退：如果无法生成 JWT，尝试直接使用 api_key
        if self.config.api_key:
            logger.warning("[Kling] 无法生成 JWT Token，回退使用静态 api_key")
            return self.config.api_key

        # 详细诊断日志
        logger.error(
            "[Kling] 认证参数缺失 | access_key_id=%s | access_key_secret=%s | api_key=%s | extra_params_keys=%s",
            bool(self._access_key_id),
            bool(self._access_key_secret),
            bool(self.config.api_key),
            list(self.config.extra_params.keys()) if self.config.extra_params else [],
        )
        raise ValueError(
            "可灵认证失败：缺少 access_key_id / access_key_secret 或 api_key。请检查模型配置中的认证信息是否正确填写（需要在 config_json 中配置 access_key_id 和 access_key_secret）。"
        )

    def _generate_jwt_token(self) -> Optional[str]:
        """
        使用 AccessKey + SecretKey 生成可灵 API 的 JWT Token

        JWT Payload 结构：
        - iss: access_key_id (签发者)
        - exp: 当前时间 + 过期秒数
        - nbf: 当前时间 - 5秒 (时钟偏差容错)

        签名算法：HS256，密钥为 access_key_secret

        文档参考：https://klingai.com/document-api/apiReference/commonInfo

        Returns:
            str: JWT Token 字符串，或 None（缺少依赖/配置）
        """
        if not pyjwt:
            logger.error(
                "[Kling] PyJWT 未安装，无法生成 JWT Token。请执行: pip install PyJWT"
            )
            return None

        if not self._access_key_id or not self._access_key_secret:
            logger.warning(
                "[Kling] 缺少 access_key_id 或 access_key_secret，无法生成 JWT Token"
            )
            return None

        try:
            now = int(time.time())
            payload = {
                "iss": self._access_key_id,
                "exp": now + KLING_TOKEN_EXPIRE_SECONDS,
                "nbf": now - 5,
            }

            token = pyjwt.encode(
                payload,
                self._access_key_secret,
                algorithm="HS256",
                headers={"alg": "HS256", "typ": "JWT"},
            )

            # PyJWT >=2.0 返回 str，<2.0 返回 bytes
            if isinstance(token, bytes):
                token = token.decode("utf-8")

            logger.debug(
                "[Kling] JWT Token 生成成功 | iss=%s | exp=%s",
                self._access_key_id[:8] + "...",
                payload["exp"],
            )
            return token

        except Exception as e:
            logger.error(f"[Kling] JWT Token 生成失败: {e}")
            return None

    def _convert_aspect_ratio(self, ratio: str) -> str:
        """转换宽高比为可灵格式"""
        return self.ASPECT_RATIO_MAP.get(ratio, ratio)

    def _clean_image_input(self, img: str) -> Dict[str, Any]:
        """
        清理图片输入，适配 Kling Omni API 格式

        Kling Omni API 的 image_list 元素支持：
        - URL 字符串（http/https 开头）
        - 纯 Base64 字符串（不含 data:image/...;base64, 前缀）

        返回格式：{"image": "<url_or_clean_base64>"}
        """
        # URL 直接返回
        if img.startswith(("http://", "https://")):
            return {"image": img}

        # Data URI 格式：剥离前缀，提取纯 Base64
        if img.startswith("data:image/"):
            match = re.match(r"data:image/[^;]+;base64,(.+)", img)
            if match:
                clean_b64 = match.group(1)
                logger.debug(
                    "[Image] 已剥离 Data URI 前缀 | 原始长度=%d | 纯Base64长度=%d",
                    len(img),
                    len(clean_b64),
                )
                return {"image": clean_b64}
            else:
                logger.warning(
                    "[Image] 无法解析 Data URI 格式，使用原始值 | length=%d", len(img)
                )
                return {"image": img}

        # 已经是纯 Base64 或其他格式，直接使用
        return {"image": img}

    async def _query_task(self, task_id: str) -> Dict[str, Any]:
        """
        查询可灵图片任务状态

        Kling API 没有统一的 /v1/images/tasks/{id} 端点，
        各模型使用各自的查询端点：
        - Standard: GET /v1/images/generations/{task_id}
        - Omni:     GET /v1/images/omni-image/{task_id}
        - Multi:    GET /v1/images/multi-image2image/{task_id}

        文档：https://klingai.com/document-api/apiReference/model/imageGeneration

        Returns:
            任务详情 data 节点（包含 task_status, task_result 等）
        """
        headers = self._build_common_headers()

        # 候选查询端点（按优先级排序）
        candidate_urls = [
            f"{self.base_url}/v1/images/generations/{task_id}",
            f"{self.base_url}/v1/images/omni-image/{task_id}",
            f"{self.base_url}/v1/images/multi-image2image/{task_id}",
        ]

        session = await self._get_session()
        try:
            for url in candidate_urls:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        continue  # 此端点不存在，尝试下一个
                    if response.status >= 400:
                        error_body = await response.text()
                        logger.error(
                            "[Image] 可灵任务查询失败 | task_id=%s | url=%s | status=%s | body=%s",
                            task_id,
                            url,
                            response.status,
                            error_body[:500],
                        )
                        response.raise_for_status()
                    result = await response.json()
                    logger.debug(
                        "[Image] 可灵任务查询成功 | task_id=%s | url=%s", task_id, url
                    )

                    # 返回 data 节点
                    return result.get("data", {})

            # 所有端点都返回 404，回退到列表查询
            logger.info(
                "[Image] 单任务查询端点均不可用，回退到列表查询 | task_id=%s", task_id
            )
            return await self._query_task_from_list(task_id, session, headers)
        finally:
            await self._close_session(session)

    async def _query_task_from_list(
        self, task_id: str, session: aiohttp.ClientSession, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        从任务列表分页查询中匹配 task_id（备用方案）
        """
        url = f"{self.base_url}/v1/images/generations"
        params = {"pageSize": 500}

        async with session.get(url, headers=headers, params=params) as response:
            if response.status >= 400:
                error_body = await response.text()
                logger.error(
                    "[Image] 可灵任务列表查询失败 | status=%s | body=%s",
                    response.status,
                    error_body[:500],
                )
                return {"task_status": "unknown", "task_id": task_id}
            result = await response.json()
            tasks = result.get("data", [])
            logger.info(
                "[Image] 可灵任务列表查询 | 总任务数=%d | 查找 task_id=%s",
                len(tasks),
                task_id,
            )
            for task in tasks:
                if task.get("task_id") == task_id:
                    return task
            return {"task_status": "unknown", "task_id": task_id}

    async def _poll_task_until_complete(
        self,
        task_id: str,
        timeout: float = KLING_POLL_TIMEOUT,
        interval: float = KLING_POLL_INTERVAL,
    ) -> GenerationResult:
        """
        轮询可灵任务直到完成或超时

        Args:
            task_id: 任务 ID
            timeout: 最大等待时间（秒）
            interval: 轮询间隔（秒）

        Returns:
            GenerationResult: 成功时包含图片 URL 列表，失败时包含错误信息
        """
        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < timeout:
            poll_count += 1
            task = await self._query_task(task_id)

            task_status = task.get("task_status", "")

            logger.debug(
                "[Image] 可灵任务轮询 | task_id=%s | poll#%d | status=%s | elapsed=%.1fs",
                task_id,
                poll_count,
                task_status,
                time.time() - start_time,
            )

            if task_status in ("succeed", "SUCCESS"):
                # 提取图片 URL（支持 images 和 series_images）
                task_result = task.get("task_result", {}) or task.get("output", {})
                images = task_result.get("images", []) or task.get("images", [])
                series_images = task_result.get("series_images", [])
                image_urls = []
                for img in images + series_images:
                    if isinstance(img, dict):
                        url = img.get("url") or img.get("image_url")
                        if url:
                            image_urls.append(url)
                    elif isinstance(img, str):
                        image_urls.append(img)

                logger.info(
                    "[Image] 可灵任务完成 | task_id=%s | 图片数=%d",
                    task_id,
                    len(image_urls),
                )
                return GenerationResult(
                    success=True,
                    image_urls=image_urls if image_urls else None,
                    raw_response=task,
                )

            elif task_status in ("failed", "FAILED"):
                # 提取错误信息
                error_msg = task.get("task_status_msg", "") or task.get(
                    "error_message", "任务失败"
                )
                logger.error(
                    "[Image] 可灵任务失败 | task_id=%s | error=%s", task_id, error_msg
                )
                return GenerationResult(
                    success=False,
                    error_message=f"Kling task failed: {error_msg}",
                    raw_response=task,
                )

            elif task_status in ("submitted", "processing", "PENDING", "RUNNING"):
                # 继续轮询
                await asyncio.sleep(interval)
            else:
                logger.warning(
                    "[Image] 可灵未知任务状态: %s | task_id=%s", task_status, task_id
                )
                await asyncio.sleep(interval)

        # 超时
        logger.error(
            "[Image] 可灵任务超时 | task_id=%s | elapsed=%.1fs | timeout=%ds",
            task_id,
            time.time() - start_time,
            timeout,
        )
        return GenerationResult(
            success=False,
            error_message=f"Kling task timeout after {timeout}s",
        )

    async def generate_image(
        self,
        prompt: str,
        params: Optional[ImageGenParams] = None,
    ) -> GenerationResult:
        """生成图片（主入口），根据 model 自动路由"""
        p = params or ImageGenParams()
        p.model_id = p.model_id or self.config.model_id
        model_config = self._resolve_model_config(p.model_id)

        ref_images = p.reference_images or []
        n_benchmark = p.benchmark_image_count or 0

        # kling-v2 和 kling-v2-1 使用多图参考接口，根据对标图数量分配图片
        # 但如果多图接口不可用（404/500等错误），则回退到 Omni 接口
        if model_config["type"] == "multi" or p.model_id in ["kling-v2", "kling-v2-1"]:
            logger.info(
                f"[Kling] 多图参考接口 | model={p.model_id} | 参考图={len(ref_images)}张 | 对标图={n_benchmark}张"
            )
            result = await self._generate_multi_image(prompt, p)
            # 如果失败（任何错误），回退到 Omni 接口
            if not result.success:
                error_code = ""
                if "404" in str(result.error_message):
                    error_code = "404"
                elif "500" in str(result.error_message):
                    error_code = "500"
                else:
                    error_code = "其他错误"
                logger.warning(
                    f"[Kling] ⚠️ 多图参考接口失败({error_code})，| error={result.error_message[:100]}"
                )
                return result
            logger.info("[Kling] ✅ 多图参考接口成功，无需回退")
            return result

        if model_config["type"] == "omni":
            return await self._generate_omni_image(prompt, p)
        return await self._generate_standard_image(prompt, p)

    async def _generate_standard_image(
        self,
        prompt: str,
        p: ImageGenParams = None,
    ) -> GenerationResult:
        """
        使用标准图像生成接口 (/v1/images/generations)

        文档：https://klingai.com/document-api/apiReference/model/imageGeneration

        支持模型：kling-v1, kling-v1.5, kling-v2, kling-v2-new, kling-v2-1, kling-v3

        V4.0 真实感增强优化：
        - 自动添加高质量负向提示词
        - 优化参考图保真度参数
        - 优先使用高分辨率模型
        - 增强人物和产品真实感
        """
        session = None
        try:
            url = f"{self.base_url}/v1/images/generations"

            model_id = p.model_id

            # === 参数构建 - V4.0 真实感增强版 ===
            payload: Dict[str, Any] = {
                "model_name": model_id,
                "prompt": prompt,
                "n": min(p.count, 9),
            }

            # === 负向提示词 - V4.0 增强版 ===
            # 自动添加高质量负向提示词，防止 AI 假人感
            payload["negative_prompt"] = get_negative_prompt("")

            # === 参考图片（图生图）V4.0 增强版 ===
            ref_images = p.reference_images or []
            image = ref_images[0] if ref_images else None
            if image and isinstance(image, str):
                cleaned = self._clean_image_input(image)
                payload["image"] = cleaned["image"]

                # === 参考图保真度优化 - V4.0 ===
                # 对于有参考图的情况，默认使用更高的保真度
                payload["image_fidelity"] = 0.65
                if model_id in ["kling-v1.5", "kling-v2", "kling-v2-1", "kling-v3"]:
                    # 默认使用主体参考模式
                    payload["image_reference"] = "subject"

            # 图片参考类型（用户仍可覆盖）
            # image_reference not in ImageGenParams, use defaults

            # image_fidelity not in ImageGenParams, skip

            # human_fidelity not in ImageGenParams, skip

            # === 分辨率优化 - V4.0 ===
            # 优先使用高分辨率，提升细节表现
            # kling-v3-omni=4k, kling-image-o1=2k, 其他默认 2k
            if model_id in ["kling-v3", "kling-v2-1"]:
                default_res = "2k"
            elif model_id in ["kling-v2"]:
                default_res = "1k"
            else:
                default_res = self.DEFAULT_RESOLUTIONS.get(model_id, "2k")
            payload["resolution"] = default_res

            # 宽高比
            aspect_ratio_raw = p.ratio  # from ImageGenParams  # 默认改为 3:4 竖屏
            aspect_ratio = self._convert_aspect_ratio(aspect_ratio_raw)
            payload["aspect_ratio"] = aspect_ratio

            # 水印（仅显式启用时添加，默认不加）
            watermark = p.watermark
            if watermark is True or (
                isinstance(watermark, str) and watermark.lower() == "true"
            ):
                payload["watermark_info"] = {"enabled": True}

            # callback_url / external_task_id not in ImageGenParams, skip

            headers = self._build_common_headers()

            logger.info(
                "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            )
            logger.info(
                "[Image] 可灵Standard生成请求 | model=%s | url=%s | n=%s",
                model_id,
                url,
                p.count,
            )
            # Base64 日志优化：仅替换 Base64 数据为长度标记，其余 payload 完整输出
            # 1) Data URI 前缀格式
            # 2) 纯 Base64 格式（Kling API 不带 data: 前缀，仅匹配 "image" 相关字段的长 Base64）
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(
                r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                lambda m: f"<Base64 {len(m.group(0))} chars>",
                payload_str,
            )
            _base64_pat = re.compile(
                r'("(?:image|subject_image|scene_image|style_image)":\s*")([A-Za-z0-9+/=]{200,})(?=")'
            )
            payload_str = _base64_pat.sub(
                lambda m: m.group(1) + f"<Base64 {len(m.group(2))} chars>", payload_str
            )
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:

                # 错误处理
                if response.status >= 400:
                    error_body = ""
                    try:
                        error_body = await response.text()
                        logger.error(
                            "[Image] 可灵API错误 | status=%s | body=%s",
                            response.status,
                            error_body[:2000],
                        )
                    except Exception:
                        pass
                    response.raise_for_status()

                result = await response.json()
                elapsed = time.time() - start_time

                logger.info(
                    "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[Image] 可灵Standard响应 | elapsed=%.2fs | model=%s",
                    elapsed,
                    model_id,
                )
                logger.info(
                    "[Image] 响应内容: %s",
                    json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                )

                # 可灵 API 为异步任务，检查任务状态
                data = result.get("data", {})
                task_status = data.get("task_status", "")
                task_id = data.get("task_id")

                if task_id and task_status in (
                    "submitted",
                    "processing",
                    "PENDING",
                    "RUNNING",
                ):
                    logger.info(
                        "[Image] 可灵异步任务 | task_id=%s | status=%s | 开始轮询...",
                        task_id,
                        task_status,
                    )
                    return await self._poll_task_until_complete(task_id)

                # 同步响应：直接解析结果
                image_urls = self._parse_generation_result(result)

                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls if image_urls else None,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"[Kling] Standard HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[Kling] Standard image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

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

    async def _generate_omni_image(
        self,
        prompt: str,
        p: ImageGenParams = None,
    ) -> GenerationResult:
        """
        使用 Omni 全模态接口 (/v1/images/omni-image)

        文档：https://klingai.com/document-api/apiReference/model/OmniImage

        支持模型：kling-image-o1, kling-v3-omni

        特性：
        - 多图输入（最多10张）
        - 主体一致性参考（element_list）
        - 组图/分镜模式
        - 最高 4K 分辨率

        V4.0 真实感增强：
        - 自动检测短提示词并添加真实感要素
        - 添加高质量负向提示词
        - 优化参考图保真度
        """
        session = None
        try:
            formatted_prompt = prompt
            url = f"{self.base_url}/v1/images/omni-image"

            model_id = p.model_id

            # === V4.0 真实感增强：自动补全高质量要素 ===
            ref_images = p.reference_images or []
            has_reference = len(ref_images) > 0
            has_pair_instruction = "【参考图说明】" in formatted_prompt
            enhanced_prompt = self._enhance_image_prompt(
                formatted_prompt,
                has_reference=has_reference and not has_pair_instruction,
            )

            # === 参数构建 - V4.0 真实感增强版 ===
            payload: Dict[str, Any] = {
                "model_name": model_id,
                "prompt": enhanced_prompt,
                "n": min(p.count, 9),
            }

            # === 负向提示词 - V4.0 增强版 ===
            # 自动添加高质量负向提示词，防止 AI 假人感
            payload["negative_prompt"] = get_negative_prompt("")

            # 参考图列表（最多10张）- 直接从 ImageGenParams 获取
            ref_images = p.reference_images or []
            if ref_images:
                image_list = []
                for img in ref_images[:10]:
                    if isinstance(img, str):
                        image_list.append(self._clean_image_input(img))
                if image_list:
                    payload["image_list"] = image_list

            # 主体参考列表（用于保持角色/物体一致性）
            element_list = None
            if element_list:
                payload["element_list"] = element_list

            # 结果类型：single（单图）或 series（组图/分镜）
            result_type = "single"
            if result_type:
                payload["result_type"] = result_type

            # 组图模式下输出数量 [2, 9]
            series_amount = None
            if series_amount and result_type == "series":
                payload["series_amount"] = min(int(series_amount), 9)

            # 分辨率：按模型默认，kling-v3-omni=4k, kling-image-o1=2k
            default_res = self.DEFAULT_RESOLUTIONS.get(model_id, "2k")
            payload["resolution"] = default_res

            # 宽高比
            aspect_ratio_raw = p.ratio  # from ImageGenParams
            aspect_ratio = self._convert_aspect_ratio(aspect_ratio_raw)
            payload["aspect_ratio"] = aspect_ratio

            # 水印（仅显式启用时添加）
            watermark = p.watermark
            if watermark is True or (
                isinstance(watermark, str) and watermark.lower() == "true"
            ):
                payload["watermark_info"] = {"enabled": True}

            # callback_url / external_task_id not in ImageGenParams, skip

            headers = self._build_common_headers()

            logger.info(
                "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            )
            logger.info(
                "[Image] 可灵Omni-Image生成请求 | model=%s | url=%s | n=%s | result_type=%s",
                model_id,
                url,
                p.count,
                result_type,
            )
            # Base64 日志优化：仅替换 Base64 数据为长度标记，其余 payload 完整输出
            # 1) Data URI 前缀格式
            # 2) 纯 Base64 格式（Kling API 不带 data: 前缀，仅匹配 "image" 相关字段的长 Base64）
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(
                r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                lambda m: f"<Base64 {len(m.group(0))} chars>",
                payload_str,
            )
            _base64_pat = re.compile(
                r'("(?:image|subject_image|scene_image|style_image)":\s*")([A-Za-z0-9+/=]{200,})(?=")'
            )
            payload_str = _base64_pat.sub(
                lambda m: m.group(1) + f"<Base64 {len(m.group(2))} chars>", payload_str
            )
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:

                if response.status >= 400:
                    error_body = ""
                    try:
                        error_body = await response.text()
                        logger.error(
                            "[Image] 可灵API错误 | status=%s | body=%s",
                            response.status,
                            error_body[:2000],
                        )
                    except Exception:
                        pass
                    response.raise_for_status()

                result = await response.json()
                elapsed = time.time() - start_time

                logger.info(
                    "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[Image] 可灵Omni-Image响应 | elapsed=%.2fs | model=%s",
                    elapsed,
                    model_id,
                )
                logger.info(
                    "[Image] 响应内容: %s",
                    json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                )

                # 可灵 API 为异步任务，检查任务状态
                data = result.get("data", {})
                task_status = data.get("task_status", "")
                task_id = data.get("task_id")

                if task_id and task_status in (
                    "submitted",
                    "processing",
                    "PENDING",
                    "RUNNING",
                ):
                    logger.info(
                        "[Image] 可灵异步任务 | task_id=%s | status=%s | 开始轮询...",
                        task_id,
                        task_status,
                    )
                    return await self._poll_task_until_complete(task_id)

                # 同步响应：直接解析结果
                image_urls = self._parse_generation_result(result)

                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls if image_urls else None,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"[Kling] Omni HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[Kling] Omni image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    async def _generate_multi_image(
        self,
        prompt: str,
        p: ImageGenParams = None,
    ) -> GenerationResult:
        """
        使用多图参考生图接口 (/v1/images/multi-image2image)

        文档：https://klingai.com/document-api/apiReference/model/multiImageToImage

        特性：
        - 主体图（保持人物/物体特征）
        - 场景图（背景场景参考）
        - 风格图（画风/色调参考）
        """
        session = None
        try:
            formatted_prompt = prompt
            url = f"{self.base_url}/v1/images/multi-image2image"

            model_id = p.model_id

            # === 参数构建 ===
            payload: Dict[str, Any] = {
                "model_name": model_id,
                "n": min(p.count, 9),
            }

            # 提示词（可选）
            if formatted_prompt:
                payload["prompt"] = formatted_prompt

            # === 参考图分配逻辑 ===
            # 根据 benchmark_image_count 分配图片：
            # - 有对标图（n_benchmark > 0）：图1 → scene_image，图2、3 → subject_image_list
            # - 无对标图（n_benchmark == 0）：图1、2 → subject_image_list
            ref_images = p.reference_images or []
            n_benchmark = p.benchmark_image_count or 0

            if ref_images:
                # 分离对标图和产品图
                benchmark_images = ref_images[:n_benchmark] if n_benchmark > 0 else []
                product_images = (
                    ref_images[n_benchmark:] if n_benchmark > 0 else ref_images
                )

                # 场景图：使用第1张对标图（如果有）
                if benchmark_images:
                    scene_image = self._clean_image_input(benchmark_images[0])
                    payload["scene_image"] = scene_image["image"]
                    logger.info("[Kling Multi] 场景图设置 | 对标图索引=0")

                # 主体图列表：使用产品图（保持产品特征）
                if product_images:
                    subject_image_list = []
                    for idx, img in enumerate(product_images):
                        cleaned = self._clean_image_input(img)
                        subject_image_list.append({"subject_image": cleaned["image"]})
                    payload["subject_image_list"] = subject_image_list
                    logger.info(
                        f"[Kling Multi] 主体图列表设置 | 产品图数量={len(product_images)}"
                    )

            # 宽高比
            aspect_ratio_raw = p.ratio  # from ImageGenParams
            aspect_ratio = self._convert_aspect_ratio(aspect_ratio_raw)
            payload["aspect_ratio"] = aspect_ratio

            # callback_url / external_task_id not in ImageGenParams, skip

            headers = self._build_common_headers()

            logger.info(
                "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            )
            logger.info(
                "[Image] 可灵Multi-Image生成请求 | model=%s | url=%s | n=%s",
                model_id,
                url,
                p.count,
            )
            # Base64 日志优化：仅替换 Base64 数据为长度标记，其余 payload 完整输出
            # 1) Data URI 前缀格式
            # 2) 纯 Base64 格式（Kling API 不带 data: 前缀，仅匹配 "image" 相关字段的长 Base64）
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
            payload_str = re.sub(
                r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
                lambda m: f"<Base64 {len(m.group(0))} chars>",
                payload_str,
            )
            _base64_pat = re.compile(
                r'("(?:image|subject_image|scene_image|style_image)":\s*")([A-Za-z0-9+/=]{200,})(?=")'
            )
            payload_str = _base64_pat.sub(
                lambda m: m.group(1) + f"<Base64 {len(m.group(2))} chars>", payload_str
            )
            logger.info("[Image] 请求 payload: %s", payload_str)

            start_time = time.time()
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:

                if response.status >= 400:
                    error_body = ""
                    try:
                        error_body = await response.text()
                        logger.error(
                            "[Image] 可灵API错误 | status=%s | body=%s",
                            response.status,
                            error_body[:2000],
                        )
                    except Exception:
                        pass
                    response.raise_for_status()

                result = await response.json()
                elapsed = time.time() - start_time

                logger.info(
                    "[Image] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
                logger.info(
                    "[Image] 可灵Multi-Image响应 | elapsed=%.2fs | model=%s",
                    elapsed,
                    model_id,
                )
                logger.info(
                    "[Image] 响应内容: %s",
                    json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                )

                # 可灵 API 为异步任务，检查任务状态
                data = result.get("data", {})
                task_status = data.get("task_status", "")
                task_id = data.get("task_id")

                if task_id and task_status in (
                    "submitted",
                    "processing",
                    "PENDING",
                    "RUNNING",
                ):
                    logger.info(
                        "[Image] 可灵异步任务 | task_id=%s | status=%s | 开始轮询...",
                        task_id,
                        task_status,
                    )
                    return await self._poll_task_until_complete(task_id)

                # 同步响应：直接解析结果
                image_urls = self._parse_generation_result(result)

                logger.info(
                    "[Image] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                )

                return GenerationResult(
                    success=True,
                    image_urls=image_urls if image_urls else None,
                    raw_response=result,
                )

        except aiohttp.ClientError as e:
            logger.error(f"[Kling] Multi-Image HTTP request failed: {e}")
            return self.handle_error(e)
        except Exception as e:
            logger.error(f"[Kling] Multi-Image generation failed: {e}")
            return self.handle_error(e)
        finally:
            if session:
                await self._close_session(session)

    def _parse_generation_result(self, result: Dict) -> List[str]:
        """
        统一解析可灵 API 的返回结果

        可灵返回格式（异步任务）：
        {
          "data": {
            "task_status": "succeed",  // submitted/processing/succeed/failed
            "task_result": {
              "images": [{"url": "..."}],
              ...
            },
            "task_id": "..."
          }
        }
        """
        image_urls = []

        # 尝试多种可能的响应结构
        data = result.get("data", {})
        task_status = data.get("task_status", "")

        # 成功状态判断
        success_statuses = ["succeed", "SUCCESS", "SUCCEEDED", 100]

        if task_status in success_statuses:
            # 从 data.task_result.images 提取
            task_result = data.get("task_result", {}) or data.get("output", {})
            images = task_result.get("images", []) or data.get("images", [])
            for img in images:
                if isinstance(img, dict):
                    url = img.get("url") or img.get("image_url")
                    if url:
                        image_urls.append(url)
                elif isinstance(img, str):
                    image_urls.append(img)

            logger.info(
                "[Image] 可灵生成成功 | status=%s | 图片数=%d",
                task_status,
                len(image_urls),
            )
        elif task_status and task_status not in (
            "submitted",
            "processing",
            "PENDING",
            "RUNNING",
        ):
            logger.warning("[Image] 可灵任务异常状态: %s", task_status)

        return image_urls

    async def generate_video(
        self,
        prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
    ) -> GenerationResult:
        """生成视频（可灵暂不支持，需要单独实现）"""
        return GenerationResult(
            success=False,
            error_message="Kling video generation requires separate implementation. Please use Kling video API directly.",
        )

    async def check_availability(self) -> bool:
        """检查模型平台是否可用（使用动态 JWT Token）"""
        session = None
        try:
            url = f"{self.base_url}/v1/models"
            headers = self._build_common_headers()  # 使用 JWT Token
            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            error_msg = str(e)
            # 脱敏处理
            for sensitive in [
                self.config.api_key,
                self._access_key_id,
                self._access_key_secret,
            ]:
                if sensitive and sensitive in error_msg:
                    error_msg = error_msg.replace(sensitive, "[REDACTED]")
            logger.warning(f"[Kling] Availability check failed: {error_msg}")
            return False
        finally:
            if session:
                await self._close_session(session)


# 注册适配器
AdapterRegistry.register("kling", KlingAdapter)
