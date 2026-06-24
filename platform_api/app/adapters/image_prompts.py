"""
图像生成提示词统一管理 (image_prompts.py)

集中管理所有图像生成平台的质量增强提示词和负向提示词，
避免在各个适配器中重复定义相同的内容。

支持的功能：
- 真实感增强提示词
- 负向提示词（防止低质量、假人感）
- 提示词增强函数

Author: Claude Code
Date: 2026
"""

from typing import Optional

# ========== 真实感增强提示词 ==========
# 用于自动为图像生成提示词添加专业摄影质量要素
REALISM_ENHANCEMENT_SUFFIX = (
    ". Realistic photography, natural soft light, "
    "high detail, sharp focus, authentic texture, "
    "professional color grading, cinematic composition, high resolution"
)

# 当有参考图片时，额外添加保持一致性的强调
REFERENCE_CONSISTENCY_NOTE = (
    ". Keep subject appearance consistent with reference image, "
    "preserve product details, maintain original character features"
)

# 检查提示词是否已经包含真实感/质量要素的关键词（中英文）
# 只要命中任意一个，即跳过增强，避免重复追加
REALISM_KEYWORDS = [
    # 英文
    "realistic photography",
    "real photo",
    "skin texture",
    "authentic texture",
    "natural soft light",
    "cinematic composition",
    "professional color grading",
    "high resolution",
    # 中文（与LLM生成的质量指令对应）
    "【质量指令】",
    "真实感",
    "材质纹理",
    "皮肤纹理",
    "毛孔",
    "塑料感皮肤",
    "畸形手",
    "自然光",
    "商业摄影",
    "写实摄影",
    "黄金分割",
    "禁止AI痕迹",
    "过度磨皮",
]


# ========== 负向提示词 ==========
# 高质量负向提示词，防止低质量、假人感、变形等问题
BASE_NEGATIVE_PROMPT = (
    "low quality, worst quality, blurry, pixelated, grainy, overexposed, underexposed, "
    "plastic skin, wax figure, fake, unrealistic, uncanny valley, "
    "deformed, distorted, disfigured, bad anatomy, bad proportions, "
    "extra limbs, extra fingers, missing fingers, fused fingers, malformed hands, "
    "mutated hands and fingers, mangled, twisted, malformed limbs, "
    "long neck, bad hands, bad feet, ugly, deformed face, asymmetric face, "
    "bad teeth, bad eyes, crossed eyes, weird eyes, "
    "text, watermark, logo, signature, jpeg artifacts, "
    "cartoon, anime, 3d render, CGI, illustration, painting, drawing, "
    "overprocessed, oversharpen, oversmooth, overfiltered"
)


# ========== 公共函数 ==========


def enhance_image_prompt(prompt: str, has_reference: bool = False) -> str:
    """
    V4.0 真实感增强：自动为短提示词补全高质量要素

    如果提示词中已经包含足够的真实感要素，则不重复添加。

    Args:
        prompt: 原始提示词
        has_reference: 是否有参考图片

    Returns:
        增强后的提示词
    """
    # 检查是否已经有足够的真实感要素
    has_realism_terms = any(keyword in prompt.lower() for keyword in REALISM_KEYWORDS)

    # 如果已经有完整的真实感要素，直接返回
    if has_realism_terms:
        return prompt

    # 构建增强后的提示词
    enhanced_prompt = prompt + REALISM_ENHANCEMENT_SUFFIX

    # 如果有参考图片，添加保持一致性的强调
    if has_reference:
        enhanced_prompt = enhanced_prompt + REFERENCE_CONSISTENCY_NOTE

    return enhanced_prompt


def get_negative_prompt(user_negative_prompt: Optional[str] = None) -> str:
    """
    获取完整的负向提示词

    Args:
        user_negative_prompt: 用户自定义的额外负向提示词（可选）

    Returns:
        合并后的负向提示词
    """
    if user_negative_prompt:
        return f"{BASE_NEGATIVE_PROMPT}, {user_negative_prompt}"
    return BASE_NEGATIVE_PROMPT


def get_realism_suffix() -> str:
    """获取真实感增强后缀（用于手动拼接）"""
    return REALISM_ENHANCEMENT_SUFFIX


def get_reference_consistency_note() -> str:
    """获取参考图片一致性提示"""
    return REFERENCE_CONSISTENCY_NOTE
