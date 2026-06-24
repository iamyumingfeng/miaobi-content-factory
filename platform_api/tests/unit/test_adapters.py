"""
模型适配器模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock

from app.adapters.base import (
    GenerationResult,
    ModelConfig,
    BaseModelAdapter,
)


@pytest.mark.unit
class TestGenerationResult:
    """GenerationResult 数据类测试"""

    def test_generation_result_success_text(self) -> None:
        """测试成功的文本生成结果"""
        result = GenerationResult(
            success=True,
            text="生成的文本内容",
            image_urls=None,
            video_url=None,
            error_message=None,
            raw_response=None
        )
        assert result.success is True
        assert result.text == "生成的文本内容"
        assert result.image_urls is None
        assert result.video_url is None
        assert result.error_message is None
        assert result.raw_response is None

    def test_generation_result_success_images(self) -> None:
        """测试成功的图片生成结果"""
        image_urls: List[str] = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
        result = GenerationResult(
            success=True,
            text=None,
            image_urls=image_urls,
            video_url=None,
            error_message=None,
            raw_response=None
        )
        assert result.success is True
        assert result.image_urls == [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg"
        ]

    def test_generation_result_success_video(self) -> None:
        """测试成功的视频生成结果"""
        result = GenerationResult(
            success=True,
            text=None,
            image_urls=None,
            video_url="https://example.com/video.mp4",
            error_message=None,
            raw_response=None
        )
        assert result.success is True
        assert result.video_url == "https://example.com/video.mp4"

    def test_generation_result_failure(self) -> None:
        """测试失败的生成结果"""
        raw_response: Dict[str, str] = {"error": "rate_limit_exceeded"}
        result = GenerationResult(
            success=False,
            text=None,
            image_urls=None,
            video_url=None,
            error_message="API 调用失败",
            raw_response=raw_response
        )
        assert result.success is False
        assert result.error_message == "API 调用失败"
        assert result.raw_response == {"error": "rate_limit_exceeded"}

    def test_generation_result_with_all_fields(self) -> None:
        """测试带所有字段的生成结果"""
        raw_response: Dict[str, str] = {"status": "ok"}
        image_urls: List[str] = ["https://example.com/img.jpg"]
        result = GenerationResult(
            success=True,
            text="描述文本",
            image_urls=image_urls,
            video_url="https://example.com/video.mp4",
            error_message=None,
            raw_response=raw_response
        )
        assert result.success is True
        assert result.text == "描述文本"
        assert len(result.image_urls) == 1
        assert result.video_url is not None
        assert result.raw_response is not None


@pytest.mark.unit
class TestModelConfig:
    """ModelConfig 数据类测试"""

    def test_model_config_basic(self) -> None:
        """测试基本模型配置"""
        config = ModelConfig(
            platform="bailian",
            model_id="qwen-max",
            api_key="test-api-key-123"
        )
        assert config.platform == "bailian"
        assert config.model_id == "qwen-max"
        assert config.api_key == "test-api-key-123"
        assert config.base_url is None
        assert config.max_concurrency == 5
        assert config.extra_params is None

    def test_model_config_with_base_url(self) -> None:
        """测试带 Base URL 的模型配置"""
        config = ModelConfig(
            platform="custom",
            model_id="custom-model",
            api_key="test-key",
            base_url="https://api.example.com/v1"
        )
        assert config.base_url == "https://api.example.com/v1"

    def test_model_config_with_custom_concurrency(self) -> None:
        """测试自定义并发数的模型配置"""
        config = ModelConfig(
            platform="volcengine",
            model_id="doubao-pro",
            api_key="test-key",
            max_concurrency=10
        )
        assert config.max_concurrency == 10

    def test_model_config_with_extra_params(self) -> None:
        """测试带额外参数的模型配置"""
        extra: Dict[str, float] = {"temperature": 0.7, "top_p": 0.9}
        config = ModelConfig(
            platform="deepseek",
            model_id="deepseek-chat",
            api_key="test-key",
            extra_params=extra
        )
        assert config.extra_params == extra


@pytest.mark.unit
class TestBaseModelAdapter:
    """BaseModelAdapter 抽象基类测试"""

    class ConcreteAdapter(BaseModelAdapter):
        """用于测试的具体适配器实现"""

        async def generate_text(
            self,
            prompt: str,
            variables: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
        ) -> GenerationResult:
            return GenerationResult(success=True, text=f"Generated: {prompt}")

        async def generate_image(
            self,
            prompt: str,
            variables: Optional[Dict[str, Any]] = None,
            count: int = 1,
            **kwargs: Any,
        ) -> GenerationResult:
            return GenerationResult(success=True, image_urls=["https://test.com/img.jpg"])

        async def generate_video(
            self,
            prompt: str,
            variables: Optional[Dict[str, Any]] = None,
            image_url: Optional[str] = None,
            **kwargs: Any,
        ) -> GenerationResult:
            return GenerationResult(success=True, video_url="https://test.com/video.mp4")

        async def check_availability(self) -> bool:
            return True

        async def get_concurrent_limit(self) -> int:
            return self.config.max_concurrency

    def test_adapter_initialization(self) -> None:
        """测试适配器初始化"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        assert adapter.config == config
        assert adapter.platform == "test"

    def test_format_prompt_without_variables(self) -> None:
        """测试无变量的提示词格式化"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        prompt = "这是一个测试提示词"
        formatted = adapter.format_prompt(prompt)
        assert formatted == prompt

    def test_format_prompt_with_variables(self) -> None:
        """测试带变量的提示词格式化"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        prompt = "你好，{name}！今天是{day}。"
        variables: Dict[str, str] = {"name": "张三", "day": "周一"}
        formatted = adapter.format_prompt(prompt, variables)
        assert formatted == "你好，张三！今天是周一。"

    def test_format_prompt_missing_variables(self) -> None:
        """测试缺失变量的提示词格式化"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        prompt = "你好，{name}！"
        variables: Dict[str, Any] = {}  # 缺少 name 变量
        formatted = adapter.format_prompt(prompt, variables)
        # 应该返回原始模板而不是抛出异常
        assert formatted == prompt

    def test_handle_error(self) -> None:
        """测试错误处理"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        error = Exception("测试错误")
        result = adapter.handle_error(error)
        assert result.success is False
        assert result.error_message == "测试错误"

    @pytest.mark.asyncio
    async def test_generate_text(self) -> None:
        """测试生成文本"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        result = await adapter.generate_text("测试提示")
        assert result.success is True
        assert result.text == "Generated: 测试提示"

    @pytest.mark.asyncio
    async def test_generate_image(self) -> None:
        """测试生成图片"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        result = await adapter.generate_image("生成一张图片")
        assert result.success is True
        assert len(result.image_urls) == 1

    @pytest.mark.asyncio
    async def test_generate_video(self) -> None:
        """测试生成视频"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        result = await adapter.generate_video("生成一段视频")
        assert result.success is True
        assert result.video_url is not None

    @pytest.mark.asyncio
    async def test_check_availability(self) -> None:
        """测试检查可用性"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key"
        )
        adapter = self.ConcreteAdapter(config)
        available = await adapter.check_availability()
        assert available is True

    @pytest.mark.asyncio
    async def test_get_concurrent_limit(self) -> None:
        """测试获取并发限制"""
        config = ModelConfig(
            platform="test",
            model_id="test-model",
            api_key="test-key",
            max_concurrency=15
        )
        adapter = self.ConcreteAdapter(config)
        limit = await adapter.get_concurrent_limit()
        assert limit == 15
