"""
创意种子库模型 (creative_seed.py)

支持创作管理员自定义管理创意种子，用于自媒体文案生成差异化。

种子类型：
- opening（开头模式）：控制文案开头风格
- emotion（情感基调）：控制文案情感表达
- ending（结尾模式）：控制文案收尾方式

Author: Claude Code
Date: 2026
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime, Enum, ForeignKey, Boolean, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import Base


class CreativeSeed(Base):
    """
    创意种子库表

    支持创作管理员自定义管理开头模式、情感基调、结尾模式等创意种子。
    系统预置基础种子，管理员可增删改查自定义种子。
    """
    __tablename__ = "creative_seed"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")

    # 基本信息
    name = Column(String(100), nullable=False, comment="种子名称（如：反常识开头、轻松吐槽基调）")
    seed_type = Column(
        Enum("opening", "emotion", "ending", name="creative_seed_type_enum"),
        nullable=False,
        comment="种子类型：opening（开头模式）/ emotion（情感基调）/ ending（结尾模式）"
    )

    # 模板内容
    template = Column(Text, nullable=False, comment="模板示例（JSON数组格式，如：['没想到这个xxx居然...', '谁能想到xxx竟然...']）")
    description = Column(Text, nullable=True, comment="使用说明")

    # 禁止和推荐内容
    forbidden_patterns = Column(Text, nullable=True, comment="禁止使用的模式（JSON数组）")
    example_phrases = Column(Text, nullable=True, comment="典型表达示例（JSON数组）")
    avoid_phrases = Column(Text, nullable=True, comment="避免的表达（JSON数组）")

    # 适用范围
    category = Column(String(50), nullable=True, default="通用", comment="适用品类：3C/美妆/美食/家居/通用")

    # 状态和归属
    status = Column(
        Enum("enabled", "disabled", name="creative_seed_status_enum"),
        nullable=False,
        default="enabled",
        comment="状态：enabled（启用）/ disabled（禁用）"
    )
    is_system = Column(Boolean, nullable=False, default=False, comment="是否系统预置（系统种子不可删除）")
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=True,
        comment="所属创作管理员ID（NULL为系统级种子）"
    )

    # 统计信息
    use_count = Column(BigInteger, nullable=False, default=0, comment="使用次数统计")
    success_rate = Column(Float, nullable=True, comment="成功率（通过去重的比例）")

    # 时间字段
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<CreativeSeed(id={self.id}, name={self.name}, type={self.seed_type})>"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        import json
        return {
            "id": self.id,
            "name": self.name,
            "seed_type": self.seed_type,
            "template": self.template,
            "description": self.description,
            "forbidden_patterns": json.loads(self.forbidden_patterns) if self.forbidden_patterns else [],
            "example_phrases": json.loads(self.example_phrases) if self.example_phrases else [],
            "avoid_phrases": json.loads(self.avoid_phrases) if self.avoid_phrases else [],
            "category": self.category,
            "status": self.status,
            "is_system": self.is_system,
            "owner_operator_id": self.owner_operator_id,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_prompt(self) -> str:
        """
        转换为提示词格式（用于文案生成）

        强调：参考风格思路，不要直接套用模板

        Returns:
            str: 创意种子的提示词表示
        """
        import json
        import random

        def safe_json_parse(value, default=None):
            """安全解析 JSON，兼容旧格式（单个字符串）和新格式（数组）"""
            if not value:
                return default or []
            try:
                parsed = json.loads(value)
                # 如果解析成功，返回解析结果
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, str):
                    # 单个字符串，转换为列表
                    return [parsed]
                else:
                    return default or []
            except (json.JSONDecodeError, TypeError, ValueError):
                # JSON 解析失败，当作单个字符串处理
                if isinstance(value, str):
                    return [value]
                return default or []

        prompt_parts = [f"【{self.seed_type}模式：{self.name}】"]

        # 核心要求：参考思路，不要照搬
        prompt_parts.append("⚠️ 重要：以下为参考示例，请理解其风格和思路，根据具体场景灵活创作，不要直接套用！")

        if self.description:
            prompt_parts.append(f"创作思路：{self.description}")

        # 从多个模板中随机选择一个作为参考
        templates = safe_json_parse(self.template, [])
        if templates:
            # 随机选择1-2个模板作为参考
            selected_templates = random.sample(templates, min(2, len(templates)))
            prompt_parts.append(f"参考风格示例（仅供参考，请灵活变化）：")
            for i, tmpl in enumerate(selected_templates, 1):
                prompt_parts.append(f"  {i}. {tmpl}")

        # 提供多个示例，让AI参考不同的表达方式
        examples = safe_json_parse(self.example_phrases, [])
        if examples:
            # 随机选择3-5个示例
            selected_examples = random.sample(examples, min(5, len(examples)))
            prompt_parts.append(f"参考表达方式（请学习其风格，不要照搬）：")
            for i, ex in enumerate(selected_examples, 1):
                prompt_parts.append(f"  {i}. {ex}")

        # 禁止使用的模式
        forbidden = safe_json_parse(self.forbidden_patterns, [])
        if forbidden:
            forbidden_text = "\n".join(f"- {p}" for p in forbidden)
            prompt_parts.append(f"禁止使用以下模式：\n{forbidden_text}")

        # 需要避免的表达
        avoids = safe_json_parse(self.avoid_phrases, [])
        if avoids:
            prompt_parts.append(f"避免以下表达方式：{', '.join(avoids)}")

        # 强调创作自由度
        prompt_parts.append("\n💡 提示：以上示例仅供参考，请根据具体产品、场景、用户画像灵活调整，创作出符合风格但内容新颖的文案。")

        return "\n".join(prompt_parts)


# 导入 Float 类型
from sqlalchemy import Float