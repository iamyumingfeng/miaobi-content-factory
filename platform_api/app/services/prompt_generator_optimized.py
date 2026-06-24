"""
优化版 AIGC 提示词生成器服务 (prompt_generator_optimized.py)

通过合并中间步骤，将 LLM 调用次数从 7-9+ 次减少到 1-5 次：
1. 移除独立的 "提示词生成器" 步骤
2. 直接生成最终文案（内置去 AI 味、爆款属性）
3. 图片提示词直接附在主调用中（可选分离）
4. 整合所有新模板字段：爆款类型、产品卖点、创意种子

Author: Claude Code
Date: 2026
"""

import json
import logging
import random
from typing import Optional, Dict, Any, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import CreativeSeed
from app.adapters.base import GenerationResult
from app.adapters.params import TextGenParams, ImageGenParams
from app.adapters.factory import ModelAdapterFactory
from app.adapters.config import get_model_config_manager
from app.services.creative_seeds import get_creative_seeds_for_generation_async

logger = logging.getLogger(__name__)


class OptimizedContentGenerator:
    """
    优化版内容生成器 - 直接生成最终内容，减少 LLM 调用次数

    核心优化：
    1. 一次性生成最终文案（含去 AI 味、爆款属性）
    2. 同时生成图片提示词（可选分离）
    3. 整合创意种子、爆款类型、产品卖点
    4. 内置创作者账号定位适配
    """

    # 平台合规规则（直接嵌入主提示词）
    PLATFORM_COMPLIANCE_RULES = """
【平台合规 - 必须严格遵守】
✅ 广告法：不用最高级（第一、最佳、顶级），用个人感受替代
✅ 医疗宣称：护肤品只讲使用感受，不涉及疗效
✅ 诱导互动：不用"求关注、互赞"，用自然讨论替代
✅ AI 原创：保持高原创度，不伪装成真人商家
"""

    # 去 AI 味核心指令（直接嵌入主提示词）
    HUMANIZE_INSTRUCTIONS = """
【去 AI 味 - 像真人在微信群里吐槽，别写成范文】

❌ 严禁以下 AI 高频用语（被发现会掉信任感）：
  - 用词：宝子们、姐妹们、家人们、集美们、绝绝子、YYDS、狠狠心动、拿捏住
  - 开头：最近买了xxx、今天给大家推荐、大家好、自从换了xxx
  - 过渡：首先其次最后、①②③序号、总的来说、综上所述、总体来看
  - 结尾：评论区告诉我、你们觉得呢、你们会选哪个、欢迎留言讨论
  - 句式：「无论是...还是...都能...」「不仅...而且...更...」「对...来说」

❌ 严禁以下 AI 体写作习惯：
  - 每句话结构相同，段落工整得像四六级作文
  - 卖点依次罗列：「3个让我惊艳的点」「5个理由告诉你」
  - 开头讲背景、中间讲体验、结尾给建议 —— 太像说明书
  - 每段 3-4 句，篇幅均匀 —— 真人说话有长有短

✅ 优秀真人写法的特征：
  - 语气像在微信群里跟朋友分享，不是写作文
  - 有废话：突然跑题说一句「啊对了，快递盒拆开差点把充电器扔了」
  - 有态度：可以有偏见、敢说「我觉得这功能鸡肋」「颜色是真的丑」
  - 段落不平均：有时一句话就是一段，有时一口气写一大段
  - 细节具体到位：不说「散热好」，说「开 3 个表格 + 微信 + 飞书，D 面还是凉飕飕的」
  - 配图的提示词不要写成「场景：xxx 主体：xxx 氛围：xxx 构图：xxx 质量：xxx」这种模板格式，用一句通顺的英文句子融合所有信息

【写作执行清单 — 每条都要做到】
1. 开头不用铺垫，直接从具体场景砸进来（时间地点人物+痛点）
2. 至少写一个缺点 or 犹豫点，还得是具体的（比如「接口砍到只剩 2 个 C 口，插 U 盘还得翻拓展坞，烦」）
3. 加入一个与主题无关的废话细节（拆快递发现赠品、同事路过瞥了一眼说xx等）
4. 有一句话要带强烈情绪（烦、无语、真服了、早知道就...）
5. 段落长短不一：允许一句话成段，允许有段落只有感叹词
6. 结尾别提问，别总结，可以直接断掉或留一个开放的态度句
7. 少用逗号串联长句，多用句号断开，像说话节奏
"""

    # 爆款类型配置
    VIRAL_TYPE_CONFIGS = {
        "seeding": {
            "name": "种草安利型",
            "structure": "痛点 → 发现 → 体验 → 安利",
            "tips": "强调使用前后的对比、细节场景、个人真实感受"
        },
        "review": {
            "name": "测评对比型",
            "structure": "横向对比 → 优缺点分析 → 选购建议",
            "tips": "客观中立、有数据/事实支撑、给出明确适用人群"
        },
        "tutorial": {
            "name": "教程攻略型",
            "structure": "问题 → 步骤讲解 → 避坑指南 → 效果展示",
            "tips": "清晰易懂、有步骤感、实用可操作"
        },
        "sharing": {
            "name": "好物分享型",
            "structure": "日常场景 → 偶遇好物 → 深度体验 → 推荐理由",
            "tips": "自然随意、像朋友圈分享、有生活感"
        },
        "pain_point": {
            "name": "痛点解决方案型",
            "structure": "戳中痛点 → 痛苦场景 → 解决方案 → 使用反馈",
            "tips": "痛点要具体、场景要真实、方案要可信"
        },
        "story": {
            "name": "故事叙述型",
            "structure": "背景故事 → 转折发现 → 使用历程 → 现状",
            "tips": "有情节、有情感、有细节、让人想听完"
        },
        "lifestyle": {
            "name": "生活场景型",
            "structure": "日常片段 → 好物融入 → 生活改变 → 态度表达",
            "tips": "有画面感、生活气息浓、体现生活态度"
        },
        "before_after": {
            "name": "前后对比型",
            "structure": "之前状态 → 使用中 → 之后变化 → 总结",
            "tips": "对比要明显、真实可信、细节具体"
        },
        "unboxing": {
            "name": "开箱体验型",
            "structure": "快递开箱 → 第一印象 → 细节发现 → 使用初体验",
            "tips": "有仪式感、细节描写、真实情绪流露"
        },
        "faq": {
            "name": "答疑解惑型",
            "structure": "常见疑问 → 逐一解答 → 总结推荐",
            "tips": "问题精准、解答专业、态度诚恳"
        },
        "daily": {
            "name": "日常记录型",
            "structure": "时间线 → 当日片段 → 好物出镜 → 自然植入",
            "tips": "真实自然、不刻意、像流水账但有重点"
        },
        "collection": {
            "name": "合集盘点型",
            "structure": "主题引入 → 逐一盘点 → 对比总结 → 选购指南",
            "tips": "信息密度高、有观点、有个人偏好"
        },
        "hidden_gem": {
            "name": "宝藏发现型",
            "structure": "偶然发现 → 不看好 → 惊艳体验 → 宝藏推荐",
            "tips": "有反差感、强调小众/不为人知、推荐有说服力"
        },
        "guide": {
            "name": "新手指南型",
            "structure": "新手困境 → 从零开始 → 心得总结 → 避坑建议",
            "tips": "共情新手、语言接地气、有可操作性"
        },
        "transform": {
            "name": "改造焕新型",
            "structure": "改造前 → 改造过程 → 改造后 → 心得",
            "tips": "视觉感强、有过程、有成就感"
        },
        "hack": {
            "name": "小妙招型",
            "structure": "问题困扰 → 发现妙招 → 实践验证 → 效果展示",
            "tips": "巧妙实用、有智慧感、可复制"
        },
        "wishlist": {
            "name": "许愿清单型",
            "structure": "种草背景 → 清单内容 → 逐个分析 → 选购规划",
            "tips": "有期待感、有理有据、引发共鸣"
        },
        "comparison": {
            "name": "横评选购型",
            "structure": "选购标准 → 逐个分析 → 适用人群 → 最终推荐",
            "tips": "维度清晰、立场客观、给出明确建议"
        },
        "diary": {
            "name": "日记打卡型",
            "structure": "第1天 → 第N天 → 变化过程 → 总结",
            "tips": "有时间线、真实记录、有成长感"
        },
        "trend": {
            "name": "热门趋势型",
            "structure": "趋势介绍 → 趋势分析 → 个人体验 → 建议",
            "tips": "有前瞻性、有观点、有个人判断"
        }
    }

    @classmethod
    async def generate_content_directly(
        cls,
        db: AsyncSession,
        template: Optional[Any],
        material: Optional[Any],
        sub_user: Optional[Any],
        benchmark_material: Optional[Any],
        owner_operator_id: Optional[int] = None,
        model_platform: Optional[str] = None,
        model_id: Optional[str] = None,
        image_count: int = 4,
        benchmark_text_enabled: bool = True,
        benchmark_image_enabled: bool = True,
        benchmark_image_reference_options: Optional[List[str]] = None,
        benchmark_image_roles: Optional[Dict[str, List[str]]] = None,
        template_product_mapping: Optional[Dict[str, str]] = None,
        benchmark_images: Optional[List[str]] = None,
        template_images: Optional[List[str]] = None,
        creative_seed_override: Optional[CreativeSeed] = None,
        dedup_diversity_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        直接生成最终内容 - 优化版核心入口

        整合所有步骤，一次性生成：
        - 文案（含去 AI 味、爆款属性）
        - 图片提示词（可选）
        - 话题标签

        减少 LLM 调用：从 7-9+ 次 → 1-5 次
        """
        logger.info("[OptimizedGenerator] 开始直接生成内容")

        # 步骤 1: 获取并构建所有配置
        config = await cls._build_generation_config(
            db, template, material, sub_user, benchmark_material,
            owner_operator_id, image_count, creative_seed_override,
            dedup_diversity_hint
        )

        # 步骤 2: 构建主提示词（整合所有要求）
        system_prompt, user_prompt = cls._build_combined_prompts(config)

        # 步骤 3: 调用 LLM 一次性生成
        result = await cls._call_llm_directly(
            db, system_prompt, user_prompt,
            model_platform, model_id, owner_operator_id
        )

        if not result.success or not result.text:
            logger.error(f"[OptimizedGenerator] 主生成失败: {result.error_message}")
            return {
                "success": False,
                "error": result.error_message or "生成失败",
                "text": None,
                "title": None,
                "topics": [],
                "image_prompts": [],
                "creative_seed_used": config.get("creative_seed_ids", []),
            }

        # 步骤 4: 解析结果
        parsed = cls._parse_combined_result(result.text)

        logger.info(f"[OptimizedGenerator] 直接生成完成 | title_len={len(parsed.get('title', ''))} | text_len={len(parsed.get('content', ''))}")

        return {
            "success": True,
            "title": parsed.get("title"),
            "content": parsed.get("content"),  # 使用 content 而非 text，保持一致性
            "topics": parsed.get("topics", []),
            "image_prompts": parsed.get("image_prompts", []),
            "creative_seed_used": config.get("creative_seed_ids", []),
            "viral_type_used": config.get("viral_type"),
            "config_used": config,
        }

    @classmethod
    async def _build_generation_config(
        cls,
        db: AsyncSession,
        template: Optional[Any],
        material: Optional[Any],
        sub_user: Optional[Any],
        benchmark_material: Optional[Any],
        owner_operator_id: Optional[int],
        image_count: int,
        creative_seed_override: Optional[CreativeSeed],
        dedup_diversity_hint: Optional[str],
    ) -> Dict[str, Any]:
        """
        构建生成配置 - 整合所有模板字段、素材、创作者画像
        """
        config = {}

        # 内容平台（从模板平台推断）
        platform_name = "小红书"
        if template and hasattr(template, 'platform_id') and template.platform_id:
            from app.models import TemplatePlatform
            tp_result = await db.execute(select(TemplatePlatform).where(TemplatePlatform.id == template.platform_id))
            tp = tp_result.scalar_one_or_none()
            if tp:
                platform_name = tp.name
        config["platform"] = platform_name

        # 内容类型
        content_type = "图文"
        if template and hasattr(template, "content_type"):
            ct_map = {"text": "文案", "image_text": "图文", "video_text": "视频"}
            content_type = ct_map.get(template.content_type, template.content_type)
        config["content_type"] = content_type

        # 爆款类型（新增字段）
        viral_type = "seeding"  # 默认种草型
        viral_config = None
        if template and hasattr(template, "viral_type") and template.viral_type:
            if template.viral_type == "auto":
                # 随机选择一个爆款类型
                viral_type = random.choice(list(cls.VIRAL_TYPE_CONFIGS.keys()))
                viral_config = cls.VIRAL_TYPE_CONFIGS.get(viral_type)
                logger.debug(f"[OptimizedGenerator] 爆款类型设置为 auto，随机选择: {viral_type}")
            else:
                viral_type = template.viral_type
                viral_config = cls.VIRAL_TYPE_CONFIGS.get(viral_type)
        config["viral_type"] = viral_type
        config["viral_config"] = viral_config

        # 产品卖点（新增字段）
        product_selling_points = None
        if template and hasattr(template, "product_selling_points") and template.product_selling_points:
            product_selling_points = template.product_selling_points
        config["product_selling_points"] = product_selling_points

        # 创意种子（新增字段 - 从模板获取或随机选择）
        creative_seeds = {}
        seed_ids = []
        if template:
            # 获取指定的种子或随机选择
            if creative_seed_override:
                # 使用覆盖指定的种子（用于去重重试）
                if creative_seed_override.seed_type == "opening":
                    creative_seeds["opening"] = creative_seed_override
                elif creative_seed_override.seed_type == "emotion":
                    creative_seeds["emotion"] = creative_seed_override
                elif creative_seed_override.seed_type == "ending":
                    creative_seeds["ending"] = creative_seed_override
                seed_ids.append(str(creative_seed_override.id))
            else:
                # 从模板指定或随机选择
                for seed_type in ["opening", "emotion", "ending"]:
                    seed_id_field = f"{seed_type}_seed_id"
                    specified_seed = None
                    use_random = False

                    if hasattr(template, seed_id_field):
                        seed_id = getattr(template, seed_id_field)
                        # seed_id 为 "auto" 表示随机选择，为数字字符串表示指定种子ID
                        if seed_id == "auto":
                            use_random = True
                            logger.debug(f"[OptimizedGenerator] {seed_type} 种子设置为 auto，将随机选择")
                        elif seed_id:
                            # 指定了具体种子ID，查询数据库
                            try:
                                seed_id_int = int(seed_id) if isinstance(seed_id, str) else seed_id
                                seed_result = await db.execute(select(CreativeSeed).where(CreativeSeed.id == seed_id_int))
                                specified_seed = seed_result.scalar_one_or_none()
                            except (ValueError, TypeError):
                                logger.warning(f"[OptimizedGenerator] 无效的种子ID: {seed_id}，将随机选择")
                                use_random = True

                    if specified_seed and specified_seed.status == "enabled":
                        creative_seeds[seed_type] = specified_seed
                        seed_ids.append(str(specified_seed.id))
                    else:
                        use_random = True

                    if use_random:
                        # 随机选择一个
                        category = getattr(template, "category", "通用") if template else "通用"
                        seeds = await get_creative_seeds_for_generation_async(db, seed_type, category, owner_operator_id)
                        if seeds:
                            selected = random.choice(seeds)
                            creative_seeds[seed_type] = selected
                            seed_ids.append(str(selected.id))
                            logger.debug(f"[OptimizedGenerator] {seed_type} 随机选择种子 ID={selected.id}")

        config["creative_seeds"] = creative_seeds
        config["creative_seed_ids"] = seed_ids

        # 参考素材
        config["material"] = material
        config["benchmark_material"] = benchmark_material

        # 创作者画像
        config["sub_user"] = sub_user
        if sub_user:
            config["sub_user_profile"] = {
                "fan_persona": getattr(sub_user, "fan_profile", ""),
                "account_positioning": getattr(sub_user, "user_positioning", ""),
                "content_style": getattr(sub_user, "content_style", ""),
            }

        # 模板指令
        config["prompt_creative"] = template.description if template and hasattr(template, "description") else ""
        config["template_instruction"] = template.prompt_template if template and hasattr(template, "prompt_template") else ""

        # 图片参数
        config["image_count"] = image_count
        config["image_size_ratio"] = template.image_size_ratio if template and hasattr(template, "image_size_ratio") else "3:4"

        # 去重多样性提示
        config["dedup_diversity_hint"] = dedup_diversity_hint

        return config

    @classmethod
    def _build_combined_prompts(cls, config: Dict[str, Any]) -> Tuple[str, str]:
        """
        构建整合版提示词 - 将所有要求整合在一套提示词中

        分配原则：
        - System Prompt: 角色、规则、输出格式（不变的约束）
        - User Prompt: 具体任务、素材、创意配置（每次请求变化的部分）
        """
        # 安全读取字段（兼容 dict 和对象属性两种访问方式）
        def _safe_getattr(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        platform = config.get("platform", "小红书")
        content_type = config.get("content_type", "图文")
        image_count = config.get("image_count", 4)
        image_size_ratio = config.get("image_size_ratio", "3:4")

        # ========== System Prompt（角色 + 规则 + 输出格式）==========
        system_prompt_parts = []

        # 1. 角色定位
        system_prompt_parts.append(f"""你是一位资深的{platform}自媒体创作者，专注于{content_type}内容创作。
你的目标是写出让普通用户看了想点赞、收藏、评论、被种草的真实内容。
""")

        # 2. 平台合规
        system_prompt_parts.append(cls.PLATFORM_COMPLIANCE_RULES)

        # 3. 去 AI 味
        system_prompt_parts.append(cls.HUMANIZE_INSTRUCTIONS)

        # 4. 输出格式要求（放system，因为是固定的格式约束）
        # 获取模板指令和提示词模板，用于在image_prompts中指导LLM
        template_instruction = config.get("template_instruction", "")
        template_prompt = config.get("template_prompt", "")
        
        image_prompt_instruction = ""
        if template_instruction or template_prompt:
            image_prompt_instruction = "\n【重要】生成image_prompts时，必须考虑以下模板指令和提示词模板：\n"
            if template_instruction:
                image_prompt_instruction += f"- 创作方向：{template_instruction}\n"
            if template_prompt:
                image_prompt_instruction += f"- 提示词模板：{template_prompt}\n"
            image_prompt_instruction += "确保生成的图片符合产品外观一致性要求，避免改变产品外观。\n"
        
        system_prompt_parts.append(f"""
【输出格式 - 严格JSON】
请以以下JSON格式输出，不要任何其他内容：
```json
{{
  "title": "吸引人的标题（10-25字，口语化，有钩子，不包含正文内容）",
  "content": "完整正文内容（分段用换行，每段1-3句，自然随意，敢说缺点，像真人写的，200-500字）",
  "topics": ["话题1", "话题2", "话题3", "话题4", "话题5"],
  "image_prompts": [
    "第1张图片提示词（主图，{image_size_ratio}比例）",
    "第2张图片提示词",
    "第3张图片提示词",
    "第4张图片提示词"
  ]
}}{image_prompt_instruction}
```
""")

        system_prompt = "\n".join(system_prompt_parts)

        # ========== User Prompt（具体任务 + 素材 + 创意配置）==========
        # 顺序设计：素材基础 → 具体要求 → 风格约束 → 输出要求
        user_prompt_parts = []
        user_prompt_parts.append("# 创作任务")

        # 1. 参考素材（先给创作基础）
        material = config.get("material")
        if material:
            user_prompt_parts.append("\n## 参考素材（创作基础）")
            _title = _safe_getattr(material, "title")
            _text = _safe_getattr(material, "text_content") or _safe_getattr(material, "content")
            _topic = _safe_getattr(material, "topic")
            if _title:
                user_prompt_parts.append(f"标题：{_title}")
            if _text:
                user_prompt_parts.append(f"内容：{str(_text)[:1500]}")
            if _topic:
                user_prompt_parts.append(f"话题：{_topic}")

        # 2. 对标素材（参考学习，禁止抄袭）
        benchmark_material = config.get("benchmark_material")
        if benchmark_material:
            user_prompt_parts.append("\n## 对标素材（参考学习，禁止抄袭）")
            user_prompt_parts.append("⚠️ 重要：以下是对标素材，用于学习文案风格、结构、表达方式。")
            user_prompt_parts.append("请参考其写作思路，但不要抄袭内容，最终文案要围绕你的产品来写。")
            _title = _safe_getattr(benchmark_material, "title")
            _text = _safe_getattr(benchmark_material, "text_content") or _safe_getattr(benchmark_material, "content")
            if _title:
                user_prompt_parts.append(f"标题：{_title}")
            if _text:
                user_prompt_parts.append(f"内容：{str(_text)[:800]}")

        # 3. 模板创意（创作方向）
        prompt_creative = config.get("prompt_creative")
        if prompt_creative:
            user_prompt_parts.append(f"\n## 创作方向\n{prompt_creative}")

        # 4. 模板指令（具体要求）
        template_instruction = config.get("template_instruction")
        if template_instruction:
            user_prompt_parts.append(f"\n## 具体要求\n{template_instruction}")

        # 5. 创作者账号定位（风格约束）
        sub_user_profile = config.get("sub_user_profile")
        if sub_user_profile:
            persona = sub_user_profile.get("fan_persona", "")
            positioning = sub_user_profile.get("account_positioning", "")
            style = sub_user_profile.get("content_style", "")
            if persona or positioning or style:
                user_prompt_parts.append(f"""
## 创作者账号定位 - 内容要适配
粉丝画像：{persona}
账号定位：{positioning}
内容风格：{style}

💡 关键：你的语气、视角、专业度要完全符合这个账号的人设！
""")

        # 6. 爆款类型配置
        viral_config = config.get("viral_config")
        if viral_config:
            user_prompt_parts.append(f"""
## 爆款类型：{viral_config['name']}
结构要求：{viral_config['structure']}
创作要点：{viral_config['tips']}
""")

        # 7. 创意种子配置
        creative_seeds = config.get("creative_seeds", {})
        if creative_seeds:
            user_prompt_parts.append("\n## 创意种子配置")
            for seed_type, seed in creative_seeds.items():
                if seed and hasattr(seed, "to_prompt"):
                    user_prompt_parts.append(seed.to_prompt())

        # 8. 产品信息（这是你要推广的产品）
        product_name = config.get("product_name", "")
        product_selling_points = config.get("product_selling_points")
        
        if product_name or product_selling_points:
            user_prompt_parts.append(f"""
## 产品信息 - 这是你要推广的产品！""")
            if product_name:
                user_prompt_parts.append(f"产品名称：{product_name}")
            if product_selling_points:
                user_prompt_parts.append(f"""
产品核心卖点（可以随机选择组合多个卖点）：
{product_selling_points}""")
            user_prompt_parts.append("""
⚠️ 关键：
1. 文案内容必须围绕这个产品来写，不要写成对标素材里的产品
2. 不要单独罗列卖点，要把卖点融入具体使用场景和故事中
3. 图片提示词中的产品外观要参考产品图，不要参考对标素材的产品
""")

        # 9. 去重多样性提示
        dedup_hint = config.get("dedup_diversity_hint")
        if dedup_hint:
            user_prompt_parts.append(f"""
## 多样性要求（重要！）
这是重新生成的版本，请务必做到：
{dedup_hint}
⚠️ 不要和之前的版本在结构、用词、视角上重复！
""")

        # 10. 图片生成要求
        benchmark_image_enabled = config.get("benchmark_image_enabled", False)
        image_instruction = f"""
## 图片提示词生成
请同时为这篇内容生成 {image_count} 张图片的提示词：
- 第1张：主图（封面级质量，最吸引人的场景，{image_size_ratio}比例）
- 第2-{image_count}张：副图（多角度展示、细节特写、不同场景）

每张图片提示词需要包含（字数不低于 300 字）：
1. 场景描述（真实生活场景，不要白底/影棚，细致描述））
2. 产品/主体细节
3. 画面氛围（自然光、生活气息）
4. 构图建议
5. 质量要求（真实自然，无AI痕迹）
"""
        
        if benchmark_image_enabled:
            image_instruction += f"""
⚠️ 图片生成特别说明：
- 对标素材图：用于学习构图、风格、光影，但产品外观不要参考它
- 产品图：用于参考产品外观，图片中的产品要保持与产品图一致（轮廓、比例、样式、色彩、纹理、材质、细节等）
- 如果模板指令提到"参考对标素材图"，是指参考其构图和风格，而不是参考其产品外观
"""
        else:
            image_instruction += f"""
⚠️ 图片生成特别说明：
- 产品图：用于参考产品外观，图片中的产品要保持与产品图一致（轮廓、比例、样式、色彩、纹理、材质、细节等）
"""
        
        user_prompt_parts.append(image_instruction)

        user_prompt = "\n".join(user_prompt_parts)

        return system_prompt, user_prompt

    @classmethod
    async def _call_llm_directly(
        cls,
        db: AsyncSession,
        system_prompt: str,
        user_prompt: str,
        model_platform: Optional[str],
        model_id: Optional[str],
        owner_operator_id: Optional[int],
    ) -> GenerationResult:
        """
        直接调用 LLM - 一次性生成所有内容
        """
        model_config_manager = get_model_config_manager()
        await model_config_manager.load_all_configs(db)

        config = None
        platform = None

        # 如果指定了平台和模型ID，查找对应配置
        if model_platform and model_id:
            configs = await model_config_manager.get_configs_by_platform(db, model_platform.lower(), model_type="llm")
            for cfg in configs:
                if cfg.model_id == model_id:
                    config = cfg
                    platform = model_platform.lower()
                    break
            if not config:
                logger.warning(f"[OptimizedGenerator] 未找到指定模型配置，回退默认")

        # 如果没有找到指定配置，使用平台默认配置
        if not config:
            result = await model_config_manager.get_default_config_with_platform(
                db, platform=model_platform.lower() if model_platform else None, model_type="llm"
            )
            if result:
                config, platform = result
            else:
                return GenerationResult(success=False, error_message="No LLM model available")

        logger.info(f"[OptimizedGenerator] 使用模型 | platform={platform} | model_id={config.model_id}")
        adapter = ModelAdapterFactory.create_adapter(platform, config)

        # 构建 TextGenParams，从 config 读取配置
        extra_params = config.extra_params or {}
        text_params = TextGenParams(
            model_id=config.model_id,
            max_tokens=extra_params.get("max_tokens", 32000),
            temperature=extra_params.get("temperature", 0.7),
            top_p=extra_params.get("top_p", 0.8),
            enable_thinking=(platform.lower() == "bailian") and extra_params.get("enable_thinking", True),
        )

        # 在调用之前完成变量替换（OptimizedGenerator 不使用变量，所以传入 None）
        formatted_user = adapter.format_prompt(user_prompt, None)
        formatted_system = adapter.format_prompt(system_prompt, None) if system_prompt else None

        return await adapter.generate_text(
            user_prompt=formatted_user,
            system_prompt=formatted_system,
            params=text_params,
        )

    @classmethod
    def _parse_combined_result(cls, raw_text: str) -> Dict[str, Any]:
        """
        解析整合版生成结果
        """
        # 尝试从 JSON 代码块提取
        json_block_match = None
        if "```json" in raw_text:
            json_block_match = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            parts = raw_text.split("```")
            if len(parts) >= 2:
                json_block_match = parts[1].strip()

        if json_block_match:
            try:
                parsed = json.loads(json_block_match)
                logger.debug(f"[OptimizedGenerator] JSON解析成功 | keys={list(parsed.keys())}")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"[OptimizedGenerator] JSON解析失败: {str(e)[:100]}")
                # 尝试修复JSON
                repaired = cls._repair_json_block(json_block_match)
                if repaired:
                    try:
                        parsed = json.loads(repaired)
                        logger.info(f"[OptimizedGenerator] JSON修复成功 | keys={list(parsed.keys())}")
                        return parsed
                    except json.JSONDecodeError:
                        pass

        # 尝试直接解析
        try:
            parsed = json.loads(raw_text.strip())
            logger.debug(f"[OptimizedGenerator] 直接解析成功 | keys={list(parsed.keys())}")
            return parsed
        except json.JSONDecodeError:
            pass

        # 兜底：尝试修复原始文本
        logger.warning("[OptimizedGenerator] 使用修复解析")
        return cls._repair_and_parse(raw_text)

    @classmethod
    def _repair_json_block(cls, json_text: str) -> Optional[str]:
        """
        尝试修复不完整的JSON字符串

        常见问题：
        1. 被截断的JSON（缺少结尾的}）
        2. 未转义的换行符
        3. 未转义的引号
        """
        # 基本清理
        json_text = json_text.strip()

        # 检查是否缺少结尾
        if not json_text.endswith("}"):
            # 尝试找到最后一个完整的键值对
            # 向前找到最后一个有效的 }
            last_complete = json_text.rfind("]")
            if last_complete == -1:
                last_complete = json_text.rfind("}")

            if last_complete > 0:
                # 从最后一个完整位置截取
                json_text = json_text[:last_complete + 1]
            else:
                # 尝试补全
                open_braces = json_text.count("{") - json_text.count("}")
                open_brackets = json_text.count("[") - json_text.count("]")
                json_text += "]" * open_brackets + "}" * open_braces

        return json_text

    @classmethod
    def _repair_and_parse(cls, raw_text: str) -> Dict[str, Any]:
        """
        修复并解析不完整的 JSON - 使用正则表达式提取内容
        """
        import re

        result = {
            "title": "",
            "content": "",
            "topics": [],
            "image_prompts": []
        }

        # 使用正则提取标题 - 匹配 "title": "..."
        title_pattern = r'"title"\s*:\s*"([^"]+)"'
        title_match = re.search(title_pattern, raw_text)
        if title_match:
            result["title"] = title_match.group(1).strip()

        # 使用正则提取内容 - 匹配 "content": "..." (内容可能很长，包含换行)
        # 使用非贪婪匹配，找到下一个键名作为边界
        content_pattern = r'"content"\s*:\s*"(.+?)"\s*,\s*"topics"'
        content_match = re.search(content_pattern, raw_text, re.DOTALL)
        if content_match:
            # 处理转义字符
            content_text = content_match.group(1)
            # 基本的转义处理
            content_text = content_text.replace('\\n', '\n')
            content_text = content_text.replace('\\r', '')
            content_text = content_text.replace('\\"', '"')
            content_text = content_text.replace('\\\\', '\\')
            result["content"] = content_text.strip()

        # 使用正则提取 topics - 匹配数组
        topics_pattern = r'"topics"\s*:\s*\[([^\]]+)\]'
        topics_match = re.search(topics_pattern, raw_text)
        if topics_match:
            topics_str = topics_match.group(1)
            # 提取每个话题
            topic_items = re.findall(r'"([^"]+)"', topics_str)
            result["topics"] = topic_items

        # 使用正则提取 image_prompts - 匹配数组
        prompts_pattern = r'"image_prompts"\s*:\s*\[(.+?)\]\s*\}'
        prompts_match = re.search(prompts_pattern, raw_text, re.DOTALL)
        if prompts_match:
            prompts_str = prompts_match.group(1)
            # 提取每个提示词
            prompt_items = re.findall(r'"(.+?)"', prompts_str, re.DOTALL)
            result["image_prompts"] = [p.replace('\\n', '\n').strip() for p in prompt_items]

        logger.info(f"[OptimizedGenerator] 修复解析结果 | title_len={len(result['title'])} | text_len={len(result['content'])} | topics={len(result['topics'])} | prompts={len(result['image_prompts'])}")

        return result

    @classmethod
    def build_dedup_diversity_hint(
        cls,
        previous_seed_ids: List[str],
        previous_viral_type: Optional[str] = None,
        similarity_level: float = 0.0,
        failed_segments: Optional[List[Dict]] = None,
    ) -> str:
        """
        构建去重用的多样性提示 - 用于重试时强制差异化
        """
        hints = []

        hints.append(f"本次相似度阈值是 {1 - similarity_level:.2%}，请完全避开以下重复：")

        if previous_seed_ids:
            hints.append(f"- 不要使用创意种子 ID: {', '.join(previous_seed_ids)}")

        if previous_viral_type:
            hints.append(f"- 避免使用 '{previous_viral_type}' 爆款类型结构")

        if failed_segments and len(failed_segments) > 0:
            hints.append(f"- 特别注意这些段落要彻底改写: {', '.join([str(s.get('index', '')) for s in failed_segments])}")

        hints.append("\n请：")
        hints.append("1. 完全换一个写作视角和切入点")
        hints.append("2. 使用不同的故事线和场景")
        hints.append("3. 调整语气和表达方式")
        hints.append("4. 换一种结构组织内容")
        hints.append("5. 重点关注产品不同的卖点侧面")

        return "\n".join(hints)
