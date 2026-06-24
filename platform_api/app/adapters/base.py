"""
AI 模型适配器基类 (base.py)

定义所有 AI 模型平台适配器的统一接口。

Author: Claude Code
Date: 2025
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .params import ImageGenParams, TextGenParams


@dataclass
class GenerationResult:
    """
    生成结果数据类
    """

    success: bool
    text: Optional[str] = None
    image_urls: Optional[List[str]] = None
    image_base64_list: Optional[List[str]] = (
        None  # Base64 编码的图片列表（Gemini 等返回）
    )
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = (
        None  # "server_error" / "client_error" / "network_error" / None
    )
    raw_response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None  # 扩展元数据


@dataclass
class BatchChatResult:
    """
    批量聊天结果数据类
    """

    success: bool
    batch_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ModelConfig:
    """
    模型配置数据类
    """

    platform: str
    model_id: str
    api_key: str
    base_url: Optional[str] = None
    max_concurrency: int = 5
    extra_params: Optional[Dict[str, Any]] = None


class BaseModelAdapter(ABC):
    """
    AI 模型适配器抽象基类

    所有具体的 AI 平台适配器都需要继承此类并实现其抽象方法。
    """

    def __init__(self, config: ModelConfig):
        """
        初始化适配器

        Args:
            config: 模型配置
        """
        self.config = config
        self.platform = config.platform

    @abstractmethod
    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str = None,
        params: Optional["TextGenParams"] = None,
    ) -> GenerationResult:
        """
        生成文本内容

        Args:
            user_prompt: 用户提示词（已完成的变量替换）
            system_prompt: 系统提示词（已完成变量替换）
            params: 文本生成参数（TextGenParams）

        Returns:
            GenerationResult: 生成结果
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        params: Optional["ImageGenParams"] = None,
    ) -> GenerationResult:
        """
        生成图片

        Args:
            prompt: 提示词（已完成变量替换）
            params: 图片生成参数（ImageGenParams），包含 count/ratio/quality/reference_images 等

        Returns:
            GenerationResult: 生成结果
        """
        pass

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """
        生成视频

        Args:
            prompt: 提示词（已完成变量替换）
            image_url: 参考图片URL（可选）
            **kwargs: 平台特定参数

        Returns:
            GenerationResult: 生成结果
        """
        pass

    @staticmethod
    def classify_http_error(error: Exception) -> str:
        """
        根据 HTTP 状态码分类错误

        Returns:
            "server_error" — 5xx 服务端错误（可重试）
            "client_error" — 4xx 客户端错误（通常不可重试）
            "network_error" — 连接/超时等网络层错误（可重试）
        """
        import aiohttp

        if isinstance(error, aiohttp.ClientResponseError):
            status = getattr(error, "status", 0)
            if 500 <= status < 600:
                return "server_error"
            elif 400 <= status < 500:
                return "client_error"
        if isinstance(
            error, (aiohttp.ClientConnectorError, aiohttp.ClientConnectionError)
        ):
            return "network_error"
        if isinstance(error, aiohttp.ClientError):
            return "network_error"
        return "unknown"

    def _resolve_text_params(self, params: Optional[TextGenParams]) -> TextGenParams:
        """获取文本参数（默认值由 config + param 默认值提供）"""
        p = params or TextGenParams()
        if p.model_id is None:
            p.model_id = self.config.model_id
        return p

    def _resolve_image_params(self, params: Optional[ImageGenParams]) -> ImageGenParams:
        """获取图片参数"""
        p = params or ImageGenParams()
        if p.model_id is None:
            p.model_id = self.config.model_id
        return p

    # ---- ratio → pixel 映射（2048px 上限，标准 OpenAI 格式） ----

    @abstractmethod
    def model_max_pixels(self, model_id: str = None) -> int:
        """返回模型支持的较大边最大像素（1K=1024, 2K=2048, 4K=3840）"""
        # 默认 2K
        return 2048

    def convert_ratio_to_size(
        self, ratio: str, model_id: str = None, separator: str = "x"
    ) -> str:
        """根据模型能力将比例转为像素尺寸"""
        from .params import calc_pixel_size

        max_px = self.model_max_pixels(model_id)
        return calc_pixel_size(ratio, max_px, separator)

    def format_prompt(
        self,
        prompt_template: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        格式化提示词模板

        Args:
            prompt_template: 提示词模板
            variables: 变量字典

        Returns:
            str: 格式化后的提示词
        """
        if not variables:
            return prompt_template

        try:
            return prompt_template.format(**variables)
        except KeyError:
            # 如果变量缺失，返回原始模板
            return prompt_template

    def get_concurrent_limit(self) -> int:
        """
        获取当前平台的并发限制

        Returns:
            int: 最大并发数
        """
        return self.config.max_concurrency

    def handle_error(self, error: Exception) -> GenerationResult:
        """
        统一错误处理

        Args:
            error: 异常对象

        Returns:
            GenerationResult: 错误结果
        """
        error_msg = str(error)
        # 过滤可能包含 API key 的敏感信息
        if hasattr(self, "config") and hasattr(self.config, "api_key"):
            api_key = getattr(self.config, "api_key", "")
            if api_key:
                error_msg = error_msg.replace(api_key, "[REDACTED]")
        error_type = self.classify_http_error(error)
        return GenerationResult(
            success=False,
            error_message=error_msg,
            error_type=error_type,
        )
