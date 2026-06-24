"""
生成任务上下文数据容器 (generation_context.py)

用于分阶段事务架构中，在不同阶段之间传递数据。
确保 AI 生成阶段不需要持有数据库连接。

设计原则：
- 阶段1：读取数据 → 填充 context → 关闭连接
- 阶段2：AI 生成 → 使用 context 中的数据 → 无数据库连接
- 阶段3：保存结果 → 从 context 提取结果 → 关闭连接

Author: Claude Code
Date: 2026-05-10
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class GenerationInputData:
    """
    生成任务输入数据容器

    在阶段1（读取数据）中填充，供阶段2（AI生成）使用。
    包含所有 AI 生成所需的数据，无需数据库连接。
    """
    # ========== 任务基础信息 ==========
    task_id: int
    item_id: int
    owner_operator_id: int
    sub_user_id: Optional[int] = None

    # ========== 内容类型和配置 ==========
    content_type: str = "text"  # text, image_text, video
    image_count: int = 4
    viral_type: Optional[str] = None  # 爆款类型

    # ========== 模板数据 ==========
    template_id: Optional[int] = None
    template_name: Optional[str] = None
    template_prompt: Optional[str] = None  # 模板提示词
    template_instruction: Optional[str] = None  # 模板指令
    template_creative: Optional[str] = None  # 模板创意
    template_content_type: Optional[str] = None
    template_platform: Optional[str] = None
    template_style: Optional[str] = None
    template_product_name: Optional[str] = None  # 产品名称（必填，用于提示词）
    template_product_selling_points: List[str] = field(default_factory=list)
    template_seeds: List[Dict[str, Any]] = field(default_factory=list)  # 创意种子（实际为 Dict）
    # 种子候选池：记录哪些种子类型原本是 "auto" 以及可选的全部候选项
    # 用于去重重试时重新随机选取不同的种子，产生不同的提示词
    seed_candidates_for_auto: Optional[Dict[str, List[Dict[str, str]]]] = None  # {seed_type: [{name, template}, ...]}
    # 原始 seed_id_map（含 "auto" 值），用于去重重试时判断哪些需要重新随机
    raw_seed_config: Optional[Dict[str, Optional[str]]] = None
    template_image_size_ratio: Optional[str] = None  # 图片比例
    template_add_watermark: bool = True  # 是否添加水印

    # ========== 素材数据 ==========
    material_id: Optional[int] = None
    material_title: Optional[str] = None
    material_text_content: Optional[str] = None
    material_platform: Optional[str] = None
    material_images: List[str] = field(default_factory=list)

    # ========== 模板产品图（来自 TemplateAttachment，用于生图时主体外观参考） ==========
    template_product_images: List[str] = field(default_factory=list)

    # ========== 对标素材数据 ==========
    benchmark_material_id: Optional[int] = None
    benchmark_material_title: Optional[str] = None
    benchmark_material_text: Optional[str] = None
    benchmark_material_images: List[str] = field(default_factory=list)
    benchmark_text_enabled: bool = False
    benchmark_image_enabled: bool = False
    benchmark_image_reference_options: Optional[Dict[str, Any]] = None
    benchmark_image_roles: List[Dict[str, str]] = field(default_factory=list)

    # ========== 创作者数据 ==========
    sub_user_nickname: Optional[str] = None
    sub_user_follower_profile: Optional[str] = None  # 粉丝画像
    sub_user_account_positioning: Optional[str] = None  # 账号定位
    sub_user_content_style: Optional[str] = None  # 内容风格

    # ========== 模型配置 ==========
    model_platform: Optional[str] = None
    model_id: Optional[str] = None
    image_model_platform: Optional[str] = None  # 图片生成模型平台
    image_model_id: Optional[str] = None  # 图片生成模型ID

    # ========== 预加载的模型配置对象（避免 Phase2 打开 DB 连接）==========
    text_model_config: Optional[Any] = None   # ModelConfig 实例
    image_model_config: Optional[Any] = None  # ModelConfig 实例（图片生成用）

    # ========== 去重配置 ==========
    dedup_enabled: bool = False
    dedup_threshold: float = 0.9
    dedup_retry_count: int = 3
    dedup_scope: List[str] = field(default_factory=lambda: ["subuser_history"])
    # 图片去重配置（独立于文案去重）
    image_dedup_enabled: bool = False
    image_dedup_threshold: float = 0.9
    image_dedup_retry_count: int = 3
    image_dedup_scope: List[str] = field(default_factory=lambda: ["subuser_image_history"])

    # ========== 历史参考（用于去重提示）==========
    historical_texts: List[str] = field(default_factory=list)

    # ========== 变量值 ==========
    variable_values: Dict[str, Any] = field(default_factory=dict)

    # ========== 图片角色映射 ==========
    template_product_mapping: Dict[str, str] = field(default_factory=dict)

    # ========== 时间戳 ==========
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于日志记录）"""
        return {
            "task_id": self.task_id,
            "item_id": self.item_id,
            "content_type": self.content_type,
            "template_id": self.template_id,
            "material_id": self.material_id,
            "sub_user_id": self.sub_user_id,
            "model_platform": self.model_platform,
            "model_id": self.model_id,
        }


@dataclass
class GenerationOutputData:
    """
    生成任务输出数据容器

    在阶段2（AI生成）中填充，供阶段3（保存结果）使用。
    包含所有生成结果，用于写入数据库。
    """
    # ========== 任务标识 ==========
    task_id: int
    item_id: int
    owner_operator_id: int

    # ========== 生成结果 ==========
    success: bool = False
    error_message: Optional[str] = None

    # ========== 文案结果 ==========
    generated_title: Optional[str] = None
    generated_text: Optional[str] = None
    generated_topics: List[str] = field(default_factory=list)

    # ========== 图片结果 ==========
    generated_image_urls: List[str] = field(default_factory=list)
    generated_image_thumbnail_urls: List[str] = field(default_factory=list)

    # ========== 提示词记录 ==========
    aigc_user_text_prompt: Optional[str] = None
    aigc_system_text_prompt: Optional[str] = None
    aigc_image_prompts: List[str] = field(default_factory=list)
    output_user_text_prompt: Optional[str] = None
    output_user_image_prompt: Optional[str] = None
    output_system_text_prompt: Optional[str] = None

    # ========== Embedding 数据（用于去重）==========
    text_embedding: Optional[List[float]] = None
    image_embeddings: List[List[float]] = field(default_factory=list)

    # ========== 去重结果 ==========
    dedup_passed: bool = True
    dedup_similarity: float = 0.0
    dedup_references: List[Dict[str, Any]] = field(default_factory=list)

    # ========== 执行统计 ==========
    execution_started_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None
    llm_calls_count: int = 0
    image_calls_count: int = 0

    # ========== 时间戳 ==========
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于日志记录）"""
        return {
            "task_id": self.task_id,
            "item_id": self.item_id,
            "success": self.success,
            "title_len": len(self.generated_title) if self.generated_title else 0,
            "text_len": len(self.generated_text) if self.generated_text else 0,
            "image_count": len(self.generated_image_urls),
            "llm_calls": self.llm_calls_count,
            "image_calls": self.image_calls_count,
        }


class GenerationContext:
    """
    生成任务上下文管理器

    管理输入和输出数据容器，确保数据在各阶段间正确传递。
    """

    def __init__(self):
        self.input_data: Optional[GenerationInputData] = None
        self.output_data: Optional[GenerationOutputData] = None

    def set_input(self, data: GenerationInputData) -> None:
        """设置输入数据"""
        self.input_data = data

    def set_output(self, data: GenerationOutputData) -> None:
        """设置输出数据"""
        self.output_data = data
