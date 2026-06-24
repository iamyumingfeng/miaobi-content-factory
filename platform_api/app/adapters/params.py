"""
标准化参数模型 (params.py)

定义文本生成和图片生成的统一参数接口，替代各适配器中的 **kwargs 传递。

Author: Claude Code
Date: 2026-05-13
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# 支持的图片比例列表
SUPPORTED_RATIOS = ["1:1", "4:3", "16:9", "3:4", "9:16", "3:2", "2:3", "21:9"]


def calc_pixel_size(ratio: str, max_pixels: int, separator: str = "x") -> str:
    """
    根据比例和模型最大像素计算像素尺寸。

    Args:
        ratio: 图片比例，如 "3:4"
        max_pixels: 较大边最大像素（1024=1K, 2048=2K, 3840=4K）
        separator: 宽高分隔符（"x" 或 "*"）

    Returns:
        str: 像素尺寸，如 "1536x2048"
    """
    w_ratio, h_ratio = map(int, ratio.split(":"))
    if w_ratio >= h_ratio:
        w = max_pixels
        h = round(max_pixels * h_ratio / w_ratio)
    else:
        h = max_pixels
        w = round(max_pixels * w_ratio / h_ratio)
    return f"{w}{separator}{h}"


class TextGenParams(BaseModel):
    """文本生成标准参数"""
    model_id: Optional[str] = Field(default=None, description="模型 ID（默认使用 config.model_id）")
    max_tokens: int = Field(default=32000, description="最大输出 token 数")
    temperature: float = Field(default=0.7, description="温度参数")
    top_p: float = Field(default=0.8, description="Top-p 采样参数")
    enable_thinking: bool = Field(default=True, description="是否启用思考模式（bailian 专用）")


class ImageGenParams(BaseModel):
    """图片生成标准参数"""
    model_id: Optional[str] = Field(default=None, description="模型 ID（默认使用 config.model_id）")
    count: int = Field(default=1, ge=1, description="生成数量")
    ratio: str = Field(default="3:4", description=f"图片比例，支持: {SUPPORTED_RATIOS}")
    quality: str = Field(default="high", description="图片质量：low / medium / high")
    watermark: bool = Field(default=False, description="是否添加水印")
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="参考图本地路径列表（等比例缩放图），适配器自行转为 URL/Base64"
    )
    benchmark_image_count: int = Field(default=0, ge=0, description="参考图中对标图的数量（前N张为对标图）")
