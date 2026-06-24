"""
分阶段生成事务服务 (generation_phases.py)

实现三阶段事务架构，解决长时间持有数据库连接的问题。

阶段1：读取数据（<1秒）→ 关闭连接
阶段2：AI 生成（30-90秒）→ 无数据库连接
阶段3：保存结果（<1秒）→ 关闭连接

连接持有时间从 100秒 降到 <2秒，连接利用率提升 50倍。

Author: Claude Code
Date: 2026-05-10
"""

import asyncio
import hashlib
import json
import logging
import random
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload

from app.adapters.base import GenerationResult
from app.adapters.params import ImageGenParams, TextGenParams
from app.core.database import async_session_maker
from app.core.retry import NonRetryableError
from app.models import (
    CreativeSeed,
    GenerationItem,
    GenerationItemExecutionLog,
    GenerationTask,
    Material,
    SubUser,
    Template,
)
from app.services.generation_context import GenerationInputData, GenerationOutputData

logger = logging.getLogger(__name__)


# ============================================
# 执行日志记录辅助函数
# ============================================


async def log_execution_node(
    item_id: int,
    node_name: str,
    node_status: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    error_data: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
):
    """
    记录执行日志节点

    Args:
        item_id: 子任务ID
        node_name: 节点名称（prompt_build / llm_call / image_call / save_result）
        node_status: 节点状态（running / success / failed / skipped）
        input_data: 输入数据
        output_data: 输出数据
        error_data: 错误数据
        duration_ms: 耗时毫秒
    """
    try:
        async with async_session_maker() as db:
            log = GenerationItemExecutionLog(
                item_id=item_id,
                node_name=node_name,
                node_status=node_status,
                input_data=input_data,
                output_data=output_data,
                error_data=error_data,
                duration_ms=duration_ms,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            db.add(log)
            await db.commit()
            logger.debug(
                f"[ExecutionLog] 记录节点 | item_id={item_id} | node={node_name} | status={node_status}"
            )
    except Exception as e:
        logger.warning(
            f"[ExecutionLog] 记录失败 | item_id={item_id} | error={str(e)[:100]}"
        )


# ============================================
# 爆款文案创作法则
# ============================================

EXPLOSIVE_COPYWRITING_RULES = """

【爆款文案创作法则 — 必须遵守】

1. 标题制胜
- 制造悬念：让读者产生强烈好奇心
- 提供价值：明确告诉读者能获得什么
- 情感共鸣：触达读者的痛点或欲望
- 标题不超过30字，不含正文内容

2. 开篇抓人
- 前3句话决定读者是否继续阅读
- 用故事、数据或问题开场
- 避免空洞的自我介绍

3. 结构清晰
- 分段明确，每段聚焦一个要点
- 使用小标题或数字标记
- 层层递进，逻辑连贯

4. 结尾有力
- 引导读者行动（点赞、收藏、转发）
- 提供明确的下一步建议
- 留下思考空间或期待感

5. 话题精准
- 选择3-5个高度相关的话题
- 避免堆砌无关热门话题
- 使用平台常见的话题格式"""


# ============================================
# 去 AI 味 — 让文案读起来像真人写的
# ============================================

ANTI_AI_FLAVOR_RULES = """
【去 AI 味要求 — 必须遵守，让文案读起来像真人原创】

1. 拒绝套话模板
- 禁止使用以下 AI 高频用语：
  「在当今社会」「随着...的发展」「众所周知」「让我们一起」
  「值得...的是」「不可否认」「其独特的...」「值得一提的是」
  「不仅...而且...更...」这种三层递进句式不超过全文字数的 5%
- 开头禁止用「在当今...」「随着时代...」等泛泛而谈的废话

2. 句式自然、有呼吸感
- 长短句交替，避免连续 3 句以上结构完全一致
- 适当使用短句、断句，模拟真人思考的停顿
- 允许口语化表达：比如「说实话」「真没想到」「绝了」等
- 段与段之间不要用「首先...其次...最后...」死板串联

3. 观点要有「人味」
- 表达个人真实感受和情绪，哪怕有偏见或主观判断
- 可以说「个人觉得」「说真的」「踩过坑才懂」这类真实语气
- 允许适当的自嘲、幽默、反差
- 不要每句话都「正能量」「完美无缺」，保留争议感

4. 细节要具体、有画面感
- 避免空洞形容词堆砌：「非常好看」「特别好用」「效果显著」
- 用具体场景替代抽象描述：
  错误：「这款产品非常好用」
  正确：「早上挤地铁一只手就能操作，不用手忙脚乱」
- 用数据、对比、故事来代替「很」「非常」「超级」

5. 结尾克制
- 禁止 AI 味结尾：「总的来说」「综上所述」「让我们拭目以待」
  「未来可期」「相信...会越来越好」「值得期待」
- 可以戛然而止、抛出问题、留下悬念，或者自然收束
- 不必每次都呼吁点赞收藏转发"""


# ============================================
# 平台合规要求
# ============================================

# 通用合规要求（所有平台均需遵守）
GENERAL_COMPLIANCE_RULES = """
【内容合规要求 — 所有平台通用，必须遵守】

1. 《广告法》合规
- 严禁使用绝对化用语：最、第一、国家级、顶级、极致、独家、首选等
- 禁止虚假宣传：不得夸大产品功效、效果或性能
- 涉及数据对比必须有明确来源
- 保健品、化妆品、金融产品不得承诺效果

2. 内容真实性
- 描述必须基于事实，避免凭空捏造
- 用户体验分享应接地气，避免浮夸
- 价格、优惠信息需准确

3. 敏感领域
- 医疗健康：不得给出诊疗建议或疗效承诺
- 金融投资：不得承诺收益或诱导投资
- 教育培训：不得承诺考试通过或就业保障"""

# 各平台专属合规要求
PLATFORM_COMPLIANCE_RULES = {
    # 小红书
    "小红书": """
【小红书平台合规要求 — 必须遵守】

1. 内容调性
- 笔记必须是「真实体验分享」视角，拒绝纯广告口吻
- 用第一人称讲述使用感受，真诚自然
- 避免生硬的产品参数堆砌

2. 商业合规
- 商业合作内容需软植入，自然融入场景
- 严禁引流导流：不得出现微信号、二维码、站外链接
- 不得引导用户「私信」「加微信」等

3. 社区规范
- 禁止拉踩、贬低竞品
- 禁止蹭敏感社会热点
- 配图避免过度修图导致失真""",
    # 抖音
    "抖音": """
【抖音平台合规要求 — 必须遵守】

1. 内容规范
- 遵守抖音社区自律公约
- 商品推广需符合抖音电商内容规范
- 避免低俗、猎奇内容表达

2. 互动规范
- 禁止诱导性互动文案（如「双击有惊喜」「评论区扣1送」等）
- 不得引导站外交易或引流

3. 商业合规
- 带货内容需确保商品信息真实
- 功效型产品不得夸大承诺""",
    # 微信公众号
    "微信公众号": """
【微信公众号平台合规要求 — 必须遵守】

1. 内容规范
- 遵守微信公众平台运营规范
- 严禁标题党：标题不得夸大、恐吓、诱导
- 内容需有信息增量，拒绝纯广告推文

2. 商业合规
- 广告需符合《互联网广告管理办法》
- 涉及投资理财需有风险提示

3. 版权要求
- 引用他人内容需注明出处
- 图片素材需确保版权合规""",
    # 微博
    "微博": """
【微博平台合规要求 — 必须遵守】

1. 内容规范
- 遵守微博社区管理规定
- 文案需适配微博短平快的信息流场景
- 避免涉及敏感时政话题

2. 商业合规
- 商业推广需符合微博商业内容管理规范
- 转发抽奖等活动需明确规则""",
    # 快手
    "快手": """
【快手平台合规要求 — 必须遵守】

1. 内容规范
- 遵守快手社区管理规范
- 内容风格适配快手「真实、接地气」的社区氛围
- 避免过度精致化表达

2. 商业合规
- 电商推广需符合快手小店的商品发布规范
- 功效型产品不得虚假宣传""",
    # B站
    "B站": """
【B站平台合规要求 — 必须遵守】

1. 内容规范
- 遵守B站社区规则
- 文案风格适配B站年轻化、圈层化特点
- 可适当使用B站社区梗，但避免低俗

2. 商业合规
- 商业推广需遵守B站商业内容规范
- 合作推广需标注「创作推广」等标签""",
    # 今日头条
    "今日头条": """
【今日头条平台合规要求 — 必须遵守】

1. 内容规范
- 遵守今日头条社区规范
- 内容应注重信息量和可读性
- 避免标题党和虚假信息

2. 商业合规
- 商业内容需符合头条广告规范
- 不得发布违规医疗、金融广告""",
}


def get_platform_compliance_rules(platform_name: str) -> str:
    """
    根据平台名称获取合规要求

    支持模糊匹配：如"小红书"、"小红书平台"、"red"都匹配到小红书规则

    Args:
        platform_name: 平台名称

    Returns:
        合规要求文本，若未匹配到则返回通用合规要求
    """
    if not platform_name:
        return GENERAL_COMPLIANCE_RULES

    name_lower = platform_name.lower().strip()

    # 精确匹配
    if name_lower in PLATFORM_COMPLIANCE_RULES:
        return PLATFORM_COMPLIANCE_RULES[name_lower]

    # 模糊匹配：通过关键词联想
    keyword_map = {
        "小红书": ["小红书", "red", "xhs", "xiaohongshu"],
        "抖音": ["抖音", "douyin", "dy", "tiktok"],
        "微信公众号": ["微信", "公众号", "wechat", "公众平台"],
        "微博": ["微博", "weibo"],
        "快手": ["快手", "kuaishou", "ks"],
        "B站": ["b站", "bilibili", "哔哩哔哩"],
        "今日头条": ["今日头条", "头条", "toutiao"],
    }

    for platform_key, keywords in keyword_map.items():
        for kw in keywords:
            if kw in name_lower:
                return PLATFORM_COMPLIANCE_RULES[platform_key]

    # 未匹配到具体平台，返回通用合规
    return GENERAL_COMPLIANCE_RULES


# ============================================


async def phase1_load_input_data(
    task_id: int,
    item_id: int,
    owner_operator_id: int,
) -> GenerationInputData:
    """
    阶段1：加载生成所需的所有输入数据

    使用独立 session 读取数据后立即关闭，连接持有时间 <1秒。

    Args:
        task_id: 任务ID
        item_id: 子任务ID
        owner_operator_id: 创作管理员ID

    Returns:
        GenerationInputData: 包含所有生成所需数据的容器
    """
    logger.info("[Phase1] 开始加载输入数据 | task_id=%s | item_id=%s", task_id, item_id)
    start_time = datetime.utcnow()

    async with async_session_maker() as db:
        # 查询任务
        task_result = await db.execute(
            select(GenerationTask).where(
                and_(
                    GenerationTask.id == task_id,
                    GenerationTask.owner_operator_id == owner_operator_id,
                )
            )
        )
        task = task_result.scalar_one_or_none()
        if not task:
            # 数据孤儿问题：父任务不存在，不应重试
            raise NonRetryableError(
                f"Orphaned item: Task {task_id} not found for item {item_id}"
            )

        # 查询子任务
        item_result = await db.execute(
            select(GenerationItem).where(
                and_(
                    GenerationItem.id == item_id,
                    GenerationItem.owner_operator_id == owner_operator_id,
                )
            )
        )
        item = item_result.scalar_one_or_none()
        if not item:
            raise ValueError(f"Item {item_id} not found")

        # 创建输入数据容器
        input_data = GenerationInputData(
            task_id=task_id,
            item_id=item_id,
            owner_operator_id=owner_operator_id,
            sub_user_id=item.sub_user_id,
            content_type="text",  # 默认值，后续根据模板更新
            image_count=getattr(task, "image_count", 4),
            model_platform=task.model_platform,
            model_id=task.model_id,
            image_model_platform=getattr(task, "image_model_platform", None),
            image_model_id=getattr(task, "image_model_id", None),
            dedup_enabled=getattr(task, "dedup_enabled", False),
            dedup_threshold=getattr(task, "dedup_threshold", 0.9),
            dedup_retry_count=getattr(task, "dedup_retry_count", 3),
            dedup_scope=task.dedup_scope or ["subuser_history"],
            image_dedup_enabled=getattr(task, "image_dedup_enabled", False),
            image_dedup_threshold=getattr(task, "image_dedup_threshold", 0.9),
            image_dedup_retry_count=getattr(task, "image_dedup_retry_count", 3),
            image_dedup_scope=task.image_dedup_scope or ["subuser_image_history"],
            variable_values=task.variable_values_json or {},
            benchmark_text_enabled=(
                item.input_benchmark_text_enabled
                if item.input_benchmark_text_enabled is not None
                else False
            ),
            benchmark_image_enabled=(
                item.input_benchmark_image_enabled
                if item.input_benchmark_image_enabled is not None
                else False
            ),
            benchmark_image_reference_options=item.input_benchmark_image_reference_options
            or None,
            benchmark_image_roles=item.input_benchmark_image_roles_json or [],
            template_product_mapping=item.input_template_product_mapping_json or {},
        )

        # 加载模板
        template = None  # 初始化模板变量，供后续回退逻辑使用
        if item.template_id:
            # 使用 selectinload 加载 platform 关系
            template_query = (
                select(Template)
                .options(
                    selectinload(Template.platform),
                    selectinload(Template.attachments),
                )
                .where(
                    and_(
                        Template.id == item.template_id,
                        Template.owner_operator_id == owner_operator_id,
                    )
                )
            )
            template_result = await db.execute(template_query)
            template = template_result.scalar_one_or_none()
            if template:
                input_data.template_id = template.id
                input_data.template_name = template.name
                input_data.template_prompt = template.prompt_template
                # 模板的 description 字段 = 提示词创意/灵感
                input_data.template_instruction = template.description
                input_data.template_content_type = template.content_type
                # 平台名称：通过关系获取
                input_data.template_platform = (
                    template.platform.name if template.platform else None
                )
                # 风格参考：使用正确的字段名
                input_data.template_style = template.style_reference
                # 图片比例
                input_data.template_image_size_ratio = template.image_size_ratio
                # 水印设置
                input_data.template_add_watermark = (
                    getattr(template, "add_watermark", False)
                    if getattr(template, "add_watermark", None) is not None
                    else False
                )
                # 爆款类型
                input_data.viral_type = template.viral_type
                # 产品名称（必填字段）
                input_data.template_product_name = template.product_name
                # 产品卖点：解析 Text 字段（可能是 JSON 字符串或普通文本）
                if template.product_selling_points:
                    try:
                        import json

                        points = json.loads(template.product_selling_points)
                        input_data.template_product_selling_points = (
                            points if isinstance(points, list) else [points]
                        )
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是JSON，按行分割
                        input_data.template_product_selling_points = [
                            line.strip()
                            for line in template.product_selling_points.split("\n")
                            if line.strip()
                        ]
                else:
                    input_data.template_product_selling_points = []
                # 创意种子：从关联关系中获取
                input_data.template_seeds = (
                    template.get_creative_seed_config()
                    if hasattr(template, "get_creative_seed_config")
                    else {}
                )
                # 加载创意种子的实际内容（名称+模板示例）
                # 注意：seed_id 可能是 'auto'（随机）或数字字符串
                import random as _random

                # 收集所有需要查询的种子ID（非 auto 的指定种子）和需要随机加载的类型
                seed_ids = []
                auto_seed_types = []
                seed_id_map = {
                    "opening": template.opening_seed_id,
                    "emotion": template.emotion_seed_id,
                    "ending": template.ending_seed_id,
                }
                for seed_type, sid in seed_id_map.items():
                    if sid and sid != "auto":
                        try:
                            seed_ids.append(int(sid))
                        except (ValueError, TypeError):
                            pass
                    elif sid == "auto":
                        auto_seed_types.append(seed_type)

                if seed_ids or auto_seed_types:
                    # 构建查询：指定种子 + 随机种子类型的候选池
                    conditions = [
                        CreativeSeed.status == "enabled",
                        or_(
                            CreativeSeed.owner_operator_id == owner_operator_id,
                            CreativeSeed.is_system,
                        ),
                    ]
                    if seed_ids and auto_seed_types:
                        conditions.append(
                            or_(
                                CreativeSeed.id.in_(seed_ids),
                                CreativeSeed.seed_type.in_(auto_seed_types),
                            )
                        )
                    elif seed_ids:
                        conditions.append(CreativeSeed.id.in_(seed_ids))
                    elif auto_seed_types:
                        conditions.append(CreativeSeed.seed_type.in_(auto_seed_types))

                    seed_query = select(CreativeSeed).where(and_(*conditions))
                    seed_result = await db.execute(seed_query)
                    all_seeds = list(seed_result.scalars().all())
                    seed_records = {s.id: s for s in all_seeds}

                    # 为每个种子类型随机选择一个（当 seed_id 为 'auto' 时），并缓存候选池供重试用
                    seed_candidates_cache: Dict[str, List[Dict[str, str]]] = {}
                    for seed_type in auto_seed_types:
                        candidates = [s for s in all_seeds if s.seed_type == seed_type]
                        if candidates:
                            # 缓存所有候选项（去重重试时重新随机用）
                            # 保存完整信息，包括模板列表、示例列表、描述、避免表达等
                            import json as _json

                            def safe_json_parse(value, default=None):
                                """安全解析 JSON，兼容旧格式（单个字符串）和新格式（数组）"""
                                if not value:
                                    return default or []
                                try:
                                    parsed = _json.loads(value)
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

                            seed_candidates_cache[seed_type] = [
                                {
                                    "name": s.name,
                                    "template": safe_json_parse(s.template, []),
                                    "example_phrases": safe_json_parse(
                                        s.example_phrases, []
                                    ),
                                    "description": s.description or "",
                                    "avoid_phrases": safe_json_parse(
                                        s.avoid_phrases, []
                                    ),
                                }
                                for s in candidates
                            ]
                            chosen = _random.choice(candidates)
                            seed_records[chosen.id] = chosen
                            # 更新 seed_id_map 以正确填充 template_seeds
                            seed_id_map[seed_type] = str(chosen.id)
                    # 存入 input_data 供 Phase2 去重重试时重新随机
                    input_data.seed_candidates_for_auto = (
                        seed_candidates_cache if seed_candidates_cache else None
                    )

                    # 将种子内容填充到 template_seeds 中
                    # 保存完整的种子对象，供 Phase2 使用
                    for seed_type, content_key in [
                        ("opening", "opening_seed_content"),
                        ("emotion", "emotion_seed_content"),
                        ("ending", "ending_seed_content"),
                    ]:
                        sid = seed_id_map.get(seed_type)
                        if sid and sid != "auto":
                            try:
                                sid_int = int(sid)
                                if sid_int in seed_records:
                                    # 直接保存种子对象，Phase2 会调用其 to_prompt 方法
                                    input_data.template_seeds[seed_type] = seed_records[
                                        sid_int
                                    ]
                            except (ValueError, TypeError):
                                pass

                    loaded_keys = [
                        k for k in input_data.template_seeds if k.endswith("_content")
                    ]
                    logger.info(
                        "[Phase1] 创意种子内容已加载 | seeds=%s | auto_types=%s | keys=%s",
                        len(seed_records),
                        auto_seed_types,
                        loaded_keys,
                    )

                # 无论种子是否加载，始终存储原始种子配置
                input_data.raw_seed_config = {
                    "opening": template.opening_seed_id,
                    "emotion": template.emotion_seed_id,
                    "ending": template.ending_seed_id,
                    "viral_type": template.viral_type,
                }

                # 根据模板内容类型更新生成内容类型
                input_data.content_type = template.content_type or "text"
                logger.debug(
                    "[Phase1] 模板已加载 | template_id=%s | name=%s",
                    template.id,
                    template.name,
                )

        # 加载产品图（优先使用子任务快照数据）
        # input_template_images_json 存储了任务创建时的产品图URL列表
        if item.input_template_images_json:
            input_data.template_product_images = item.input_template_images_json
            logger.debug(
                "[Phase1] 产品图快照已加载 | count=%s",
                len(input_data.template_product_images),
            )
        elif item.template_id and template and template.attachments:
            # 回退：从模板附件加载（兼容旧数据）
            input_data.template_product_images = [
                att.file_url for att in template.attachments if att.file_type == "image"
            ]
            logger.debug(
                "[Phase1] 产品图已加载（从模板附件）| count=%s",
                len(input_data.template_product_images),
            )

        # 加载素材
        if task.material_id:
            # 使用 selectinload 加载附件关系
            material_query = (
                select(Material)
                .options(selectinload(Material.attachments))
                .where(
                    and_(
                        Material.id == task.material_id,
                        Material.owner_operator_id == owner_operator_id,
                    )
                )
            )
            material_result = await db.execute(material_query)
            material = material_result.scalar_one_or_none()
            if material:
                input_data.material_id = material.id
                input_data.material_title = material.title
                input_data.material_text_content = material.text_content
                # 素材没有直接关联平台，使用None
                input_data.material_platform = None
                # 从附件中提取图片URL
                input_data.material_images = (
                    [
                        att.file_url
                        for att in material.attachments
                        if att.file_type == "image"
                    ]
                    if material.attachments
                    else []
                )
                logger.debug(
                    "[Phase1] 素材已加载 | material_id=%s | title=%s",
                    material.id,
                    material.title,
                )

        # 加载对标素材（优先使用快照数据，避免素材被修改导致的不一致）
        if item.input_benchmark_title or item.input_benchmark_content:
            # 使用子任务中保存的快照数据
            input_data.benchmark_material_id = task.benchmark_material_id
            input_data.benchmark_material_title = item.input_benchmark_title
            input_data.benchmark_material_text = item.input_benchmark_content
            input_data.benchmark_material_images = (
                item.input_benchmark_images_json or []
            )
            logger.debug(
                "[Phase1] 对标素材快照已加载 | benchmark_id=%s | title=%s | content_len=%s",
                task.benchmark_material_id,
                item.input_benchmark_title,
                (
                    len(item.input_benchmark_content)
                    if item.input_benchmark_content
                    else 0
                ),
            )
        elif task.benchmark_material_id:
            # 如果快照数据不存在，从数据库加载（兼容旧数据）
            benchmark_query = (
                select(Material)
                .options(selectinload(Material.attachments))
                .where(
                    and_(
                        Material.id == task.benchmark_material_id,
                        Material.owner_operator_id == owner_operator_id,
                    )
                )
            )
            benchmark_result = await db.execute(benchmark_query)
            benchmark = benchmark_result.scalar_one_or_none()
            if benchmark:
                input_data.benchmark_material_id = benchmark.id
                input_data.benchmark_material_title = benchmark.title
                input_data.benchmark_material_text = benchmark.content
                input_data.benchmark_material_images = (
                    [
                        att.file_url
                        for att in benchmark.attachments
                        if att.file_type == "image"
                    ]
                    if benchmark.attachments
                    else []
                )
                logger.debug(
                    "[Phase1] 对标素材已加载（从数据库）| benchmark_id=%s | title=%s | content_len=%s",
                    benchmark.id,
                    benchmark.title,
                    len(benchmark.content) if benchmark.content else 0,
                )

        # 加载创作者信息
        if item.sub_user_id:
            sub_user_result = await db.execute(
                select(SubUser).where(SubUser.id == item.sub_user_id)
            )
            sub_user = sub_user_result.scalar_one_or_none()
            if sub_user:
                input_data.sub_user_nickname = sub_user.nickname
                input_data.sub_user_follower_profile = sub_user.fan_profile  # 粉丝画像
                input_data.sub_user_account_positioning = (
                    sub_user.user_positioning
                )  # 账号定位
                input_data.sub_user_content_style = sub_user.content_style
                logger.debug(
                    "[Phase1] 创作者已加载 | sub_user_id=%s | nickname=%s",
                    sub_user.id,
                    sub_user.nickname,
                )

        # 加载历史参考（用于去重提示）
        if input_data.dedup_enabled and "subuser_history" in input_data.dedup_scope:
            try:
                hist_query = (
                    select(GenerationItem)
                    .where(
                        and_(
                            GenerationItem.sub_user_id == item.sub_user_id,
                            GenerationItem.owner_operator_id == owner_operator_id,
                            GenerationItem.distribution_status.in_(
                                ["distributed", "pending_publish", "published"]
                            ),
                            GenerationItem.generated_text.isnot(None),
                        )
                    )
                    .order_by(GenerationItem.created_at.desc())
                    .limit(3)
                )
                hist_result = await db.execute(hist_query)
                hist_items = list(hist_result.scalars().all())

                for hist_item in hist_items:
                    if hist_item.generated_text:
                        preview = (
                            hist_item.generated_text[:300]
                            if len(hist_item.generated_text) > 300
                            else hist_item.generated_text
                        )
                        input_data.historical_texts.append(
                            f"【历史内容】标题：{hist_item.generated_title or '无标题'}\n内容：{preview}"
                        )
                logger.debug("[Phase1] 历史参考已加载 | count=%s", len(hist_items))
            except Exception as e:
                logger.warning("[Phase1] 加载历史参考失败 | error=%s", str(e)[:100])

        # 预加载模型配置（避免 Phase2 重新打开数据库连接）
        # 强制刷新确保拿到最新的配置（特别是 api_key）
        try:
            import random

            from app.adapters.config import ModelConfigManager
            from app.models import UserDefaultModel

            config_manager = ModelConfigManager()
            await config_manager.load_all_configs(db, force_refresh=True)

            # 查询用户的默认模型设置
            user_defaults = {}
            default_query = select(UserDefaultModel).where(
                and_(
                    UserDefaultModel.user_id == owner_operator_id,
                    UserDefaultModel.user_type == "operator",
                )
            )
            default_result = await db.execute(default_query)
            for row in default_result.scalars().all():
                user_defaults[row.model_type] = row

            # 辅助函数：获取所有指定类型的活跃模型
            def _get_all_configs_by_type(model_type: str):
                return [
                    cfg
                    for cfg in config_manager._cache.values()
                    if cfg.platform
                    and cfg.model_id
                    and config_manager._db_configs.get(cfg.id)
                    and config_manager._db_configs[cfg.id].model_type == model_type
                    and config_manager._db_configs[cfg.id].status == "active"
                ]

            # ===== 文本模型选择 =====
            if input_data.model_platform and input_data.model_platform != "auto":
                # 用户指定了具体平台
                text_configs = await config_manager.get_configs_by_platform(
                    db, input_data.model_platform
                )
                if text_configs:
                    if input_data.model_id:
                        for cfg in text_configs:
                            if cfg.model_id == input_data.model_id:
                                input_data.text_model_config = cfg
                                break
                    if not input_data.text_model_config:
                        input_data.text_model_config = text_configs[0]
            else:
                # 自动模式：查用户默认设置
                llm_default = user_defaults.get("llm")
                if llm_default and llm_default.model_config_id:
                    # 用户有指定默认 LLM 模型
                    input_data.text_model_config = config_manager._cache.get(
                        llm_default.model_config_id
                    )
                if not input_data.text_model_config:
                    # 无默认或默认=auto：从所有活跃 LLM 中随机选
                    all_llm = _get_all_configs_by_type("llm")
                    if all_llm:
                        input_data.text_model_config = random.choice(all_llm)

            if input_data.text_model_config:
                input_data.model_platform = input_data.text_model_config.platform
                input_data.model_id = input_data.text_model_config.model_id
                # 调试日志：验证 api_key 是否正确传递
                api_key_status = "有" if input_data.text_model_config.api_key else "无"
                logger.info(
                    "[Phase1] 文本模型已选定 | platform=%s | model_id=%s | mode=%s | api_key=%s",
                    input_data.model_platform,
                    input_data.model_id,
                    (
                        "指定"
                        if (
                            input_data.model_platform
                            and input_data.model_platform != "auto"
                        )
                        else "自动"
                    ),
                    api_key_status,
                )
            else:
                logger.warning("[Phase1] 未找到可用的文本模型")

            # ===== 图片模型选择 =====
            if (
                input_data.image_model_platform
                and input_data.image_model_platform != "auto"
            ):
                # 用户指定了具体图片模型平台
                image_configs = await config_manager.get_configs_by_platform(
                    db, input_data.image_model_platform
                )
                if image_configs:
                    if input_data.image_model_id:
                        for cfg in image_configs:
                            if cfg.model_id == input_data.image_model_id:
                                input_data.image_model_config = cfg
                                break
                    if not input_data.image_model_config:
                        input_data.image_model_config = image_configs[0]
            else:
                # 自动模式：查用户默认图片模型设置
                image_default = user_defaults.get("image")
                if image_default and image_default.model_config_id:
                    input_data.image_model_config = config_manager._cache.get(
                        image_default.model_config_id
                    )
                if not input_data.image_model_config:
                    # 无默认图片模型或默认=auto：从所有活跃 image 模型中随机选
                    all_image = _get_all_configs_by_type("image")
                    if all_image:
                        input_data.image_model_config = random.choice(all_image)

            if input_data.image_model_config:
                input_data.image_model_platform = input_data.image_model_config.platform
                input_data.image_model_id = input_data.image_model_config.model_id
                # 调试日志：验证 api_key 是否正确传递
                api_key_status = "有" if input_data.image_model_config.api_key else "无"
                logger.info(
                    "[Phase1] 图片模型已选定 | platform=%s | model_id=%s | mode=%s | api_key=%s",
                    input_data.image_model_platform,
                    input_data.image_model_id,
                    (
                        "指定"
                        if (
                            input_data.image_model_platform
                            and input_data.image_model_platform != "auto"
                        )
                        else "自动"
                    ),
                    api_key_status,
                )
            else:
                logger.warning("[Phase1] 未找到可用的图片生成模型")

        except Exception as e:
            logger.warning("[Phase1] 预加载模型配置失败 | error=%s", str(e)[:100])

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        "[Phase1] 输入数据加载完成 | elapsed=%.2fs | item_id=%s", elapsed, item_id
    )

    return input_data


# ============================================
# 阶段2：AI生成
# ============================================


class _AttrDict:
    """通用属性字典，使 OptimizedContentGenerator 可通过 .text_content 等属性访问字段"""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _SeedPromptWrapper:
    """创意种子提示词包装器，使 OptimizedContentGenerator 可消费纯字符串种子

    强调：参考风格思路，不要直接套用模板
    """

    def __init__(
        self,
        name: str,
        templates: list,
        examples: list,
        description: str = "",
        avoids: list = None,
    ):
        self._name = name
        self._templates = templates if isinstance(templates, list) else [templates]
        self._examples = examples if isinstance(examples, list) else [examples]
        self._description = description
        self._avoids = avoids or []

    def to_prompt(self) -> str:
        """生成提示词，强调参考思路而非照搬"""
        import random

        prompt_parts = [f"【{self._name}】"]
        prompt_parts.append(
            "⚠️ 重要：以下为参考示例，请理解其风格和思路，根据具体场景灵活创作，不要直接套用！"
        )

        if self._description:
            prompt_parts.append(f"创作思路：{self._description}")

        # 随机选择1-2个模板作为参考
        if self._templates:
            selected_templates = random.sample(
                self._templates, min(2, len(self._templates))
            )
            prompt_parts.append("参考风格示例（仅供参考，请灵活变化）：")
            for i, tmpl in enumerate(selected_templates, 1):
                prompt_parts.append(f"  {i}. {tmpl}")

        # 随机选择3-5个示例
        if self._examples:
            selected_examples = random.sample(
                self._examples, min(5, len(self._examples))
            )
            prompt_parts.append("参考表达方式（请学习其风格，不要照搬）：")
            for i, ex in enumerate(selected_examples, 1):
                prompt_parts.append(f"  {i}. {ex}")

        # 需要避免的表达
        if self._avoids:
            prompt_parts.append(f"避免以下表达方式：{', '.join(self._avoids)}")

        prompt_parts.append(
            "\n💡 提示：以上示例仅供参考，请根据具体产品、场景、用户画像灵活调整，创作出符合风格但内容新颖的文案。"
        )

        return "\n".join(prompt_parts)


class Phase2Generator:
    """
    阶段2生成器：在无数据库连接的情况下执行AI生成

    职责：
    1. 提示词构建（使用输入数据）
    2. LLM 文案生成
    3. 图片生成
    4. 去重检测（调用embedding服务，使用独立连接）
    5. 结果封装（写入输出容器）
    """

    async def execute(
        self,
        input_data: GenerationInputData,
    ) -> GenerationOutputData:
        """
        执行阶段2：AI生成

        Args:
            input_data: 输入数据容器

        Returns:
            GenerationOutputData: 输出数据容器

        注意：embedding 在去重检测后直接异步保存
        """
        logger.info(
            "[Phase2] 开始AI生成 | item_id=%s | content_type=%s",
            input_data.item_id,
            input_data.content_type,
        )

        output_data = GenerationOutputData(
            task_id=input_data.task_id,
            item_id=input_data.item_id,
            owner_operator_id=input_data.owner_operator_id,
            execution_started_at=datetime.utcnow(),
        )

        try:
            # ========== 步骤1：使用 OptimizedContentGenerator 构建提示词 ==========
            prompt_build_start = datetime.utcnow()
            config = self._build_optimized_config(input_data)
            from app.services.prompt_generator_optimized import (
                OptimizedContentGenerator,
            )

            system_prompt, text_prompt = (
                OptimizedContentGenerator._build_combined_prompts(config)
            )
            # 追加历史参考（OptimizedContentGenerator 不处理历史）
            if input_data.historical_texts:
                text_prompt += "\n\n## 历史参考（禁止重复和高相似度）\n"
                text_prompt += "\n\n---\n".join(input_data.historical_texts)
                text_prompt += "\n\n⚠️ 以上为已发布的历史内容，请确保新内容在选题角度、表达方式、核心观点上有明显差异"
            image_prompts = []
            if input_data.content_type == "image_text":
                image_prompts = self._construct_image_prompts(input_data)
            output_data.output_system_text_prompt = system_prompt
            output_data.output_user_text_prompt = text_prompt

            # 记录提示词构建日志
            prompt_build_end = datetime.utcnow()
            prompt_build_duration = int(
                (prompt_build_end - prompt_build_start).total_seconds() * 1000
            )
            await log_execution_node(
                item_id=input_data.item_id,
                node_name="prompt_build",
                node_status="success",
                input_data={
                    "content_type": input_data.content_type,
                    "template_id": input_data.template_id,
                    "viral_type": input_data.viral_type,
                },
                output_data={
                    "system_prompt_length": len(system_prompt),
                    "user_prompt_length": len(text_prompt),
                    "image_prompts_count": len(image_prompts),
                },
                duration_ms=prompt_build_duration,
            )

            # ========== 步骤2：生成文案（带去重重试） ==========
            max_dedup_retries = (
                input_data.dedup_retry_count if input_data.dedup_enabled else 1
            )

            for retry_round in range(max_dedup_retries):
                # 步骤2a：LLM 生成文案（去重重试时逐步提高 temperature）
                # temperature 逐步提高：0.7 -> 0.85 -> 0.9 -> 0.95
                retry_temperature = (
                    0.7 + min(retry_round * 0.15, 0.25) if retry_round > 0 else None
                )

                # 记录文案生成开始
                llm_call_start = datetime.utcnow()

                text_result = await self._generate_text_with_retry(
                    text_prompt,
                    input_data,
                    output_data,
                    system_prompt=system_prompt,
                    temperature=retry_temperature,
                )

                llm_call_end = datetime.utcnow()
                llm_call_duration = int(
                    (llm_call_end - llm_call_start).total_seconds() * 1000
                )

                if not text_result.success:
                    output_data.success = False
                    output_data.error_message = (
                        text_result.error_message or "Text generation failed"
                    )
                    # 记录文案生成失败
                    await log_execution_node(
                        item_id=input_data.item_id,
                        node_name="llm_call",
                        node_status="failed",
                        input_data={
                            "model_platform": input_data.model_platform,
                            "model_id": input_data.model_id,
                            "retry_round": retry_round,
                            "temperature": retry_temperature,
                        },
                        error_data={
                            "error_message": text_result.error_message,
                        },
                        duration_ms=llm_call_duration,
                    )
                    return output_data

                # 步骤2b：解析文案结果
                parsed = self._parse_generated_text(text_result.text)
                output_data.generated_title = parsed.get("title")
                output_data.generated_text = parsed.get("content")
                output_data.generated_topics = parsed.get("topics", [])
                output_data.llm_calls_count += 1

                # 记录文案生成成功
                await log_execution_node(
                    item_id=input_data.item_id,
                    node_name="llm_call",
                    node_status="success",
                    input_data={
                        "model_platform": input_data.model_platform,
                        "model_id": input_data.model_id,
                        "retry_round": retry_round,
                        "temperature": retry_temperature,
                    },
                    output_data={
                        "title": (
                            output_data.generated_title[:100]
                            if output_data.generated_title
                            else None
                        ),
                        "content_length": len(output_data.generated_text or ""),
                        "topics_count": len(output_data.generated_topics or []),
                    },
                    duration_ms=llm_call_duration,
                )

                # 步骤2c：对于 image_text，提取 LLM 生成的 image_prompts
                llm_image_prompts_raw = parsed.get("image_prompts", [])
                if input_data.content_type == "image_text" and llm_image_prompts_raw:
                    extracted_prompts = []
                    for p in llm_image_prompts_raw:
                        if isinstance(p, str) and p.strip():
                            extracted_prompts.append(p.strip())
                    if extracted_prompts:
                        image_prompts = extracted_prompts[: input_data.image_count]

                        # 在LLM生成的提示词中加入模板指令和提示词模板
                        template_instruction = input_data.template_instruction or ""
                        template_prompt = input_data.template_prompt or ""
                        if template_instruction.strip() in ("无", "暂无", "无创意", ""):
                            template_instruction = ""
                        if template_prompt.strip() in (
                            "无",
                            "暂无",
                            "",
                            "无提示词模板",
                        ):
                            template_prompt = ""

                        if template_instruction or template_prompt:
                            enhanced_prompts = []
                            for p in image_prompts:
                                parts = [p]
                                if template_instruction:
                                    parts.append(f"创作方向：{template_instruction}")
                                if template_prompt:
                                    parts.append(f"生图要求：{template_prompt}")
                                enhanced_prompts.append("，".join(parts))
                            image_prompts = enhanced_prompts
                            logger.info(
                                "[Phase2] 已为LLM生成的提示词加入模板指令 | count=%s",
                                len(image_prompts),
                            )

                        output_data.aigc_image_prompts = extracted_prompts
                        logger.info(
                            "[Phase2] 使用LLM生成的配图提示词 | count=%s",
                            len(image_prompts),
                        )

                # 步骤2d：去重检测
                dedup_passed = True
                if input_data.dedup_enabled and output_data.generated_text:
                    dedup_passed = await self._check_dedup(input_data, output_data)
                    if not dedup_passed:
                        logger.warning(
                            "[Phase2] 去重检测未通过 | item_id=%s | similarity=%.2f | retry=%s/%s",
                            input_data.item_id,
                            output_data.dedup_similarity,
                            retry_round + 1,
                            max_dedup_retries,
                        )
                        if retry_round < max_dedup_retries - 1:
                            # 去重重试：重新随机爆款类型和创意种子 + 附加相似度高的历史文案 + 去重警告
                            retry_config = self._build_optimized_config(
                                input_data, retry_round=retry_round + 1
                            )
                            text_prompt = (
                                OptimizedContentGenerator._build_combined_prompts(
                                    retry_config
                                )[1]
                            )

                            # 追加相似度高的历史文案（从去重检测结果中提取，而非泛泛的历史记录）
                            if output_data.dedup_references:
                                text_prompt += "\n\n## ⚠️ 高相似度历史文案（必须避免）\n"
                                for idx, ref in enumerate(
                                    output_data.dedup_references[:3], 1
                                ):  # 最多显示前3个
                                    similarity = ref.get("similarity", 0)
                                    content_preview = ref.get("content_preview", "")
                                    source = ref.get("source", "历史内容")
                                    text_prompt += (
                                        f"\n### 相似度 {similarity:.0%} - {source}\n"
                                    )
                                    text_prompt += f"{content_preview}\n"
                                text_prompt += "\n⚠️ 以上为与当前生成内容高度相似的历史文案，请务必创作完全不同的内容"

                            # 追加历史参考（首次生成时的历史文案）
                            if input_data.historical_texts:
                                text_prompt += "\n\n## 历史参考（禁止重复和高相似度）\n"
                                text_prompt += "\n\n---\n".join(
                                    input_data.historical_texts[:2]
                                )  # 限制数量
                                text_prompt += "\n\n⚠️ 以上为已发布的历史内容，请确保新内容在选题角度、表达方式、核心观点上有明显差异"

                            # 追加去重警告
                            dedup_warning = (
                                f"\n\n⚠️ 【去重重试 — 第{retry_round + 1}次生成相似度过高(相似度{output_data.dedup_similarity:.0%})】\n"
                                f"请创作角度、结构、表达方式完全不同的全新内容：\n"
                                f"1. 改变切入角度：从不同场景、不同人群、不同痛点出发\n"
                                f"2. 调整结构顺序：打乱段落顺序，改变论述逻辑\n"
                                f"3. 替换具体案例：使用完全不同的使用场景、数据、细节\n"
                                f"4. 改变表达方式：用不同的比喻、不同的语气、不同的句式\n"
                                f"5. 调整情感基调：从理性分析转为感性分享，或相反"
                            )
                            text_prompt += dedup_warning
                            logger.info(
                                "[Phase2] 去重重试：已重新随机爆款类型和创意种子 | item_id=%s | round=%s/%s | high_sim_refs=%s",
                                input_data.item_id,
                                retry_round + 1,
                                max_dedup_retries,
                                len(output_data.dedup_references),
                            )
                            continue
                        else:
                            logger.warning(
                                "[Phase2] 去重重试耗尽 | item_id=%s | max_retries=%s",
                                input_data.item_id,
                                max_dedup_retries,
                            )
                            output_data.dedup_passed = False

                if dedup_passed:
                    if input_data.dedup_enabled:
                        logger.info(
                            "[Phase2] 去重通过 | item_id=%s | round=%s",
                            input_data.item_id,
                            retry_round + 1,
                        )
                    break

            # ========== 步骤3：生成图片（仅 image_text） ==========
            if input_data.content_type == "image_text" and image_prompts:
                logger.info(
                    "[Phase2] 开始生成图片 | prompt_count=%s", len(image_prompts)
                )

                # 记录图片生成开始
                image_call_start = datetime.utcnow()
                image_result = await self._generate_images(image_prompts, input_data)
                image_call_end = datetime.utcnow()
                image_call_duration = int(
                    (image_call_end - image_call_start).total_seconds() * 1000
                )

                output_data.generated_image_urls = image_result.get("images", [])
                output_data.generated_image_thumbnail_urls = image_result.get(
                    "thumbnails", []
                )
                output_data.image_calls_count = len(image_prompts)

                # 下载图片到本地COS并生成缩略图
                # 模型平台返回的URL可能是临时的，需要保存到本地COS
                if output_data.generated_image_urls:
                    try:
                        from app.services.storage_service import get_storage_service

                        storage_service = get_storage_service()

                        logger.info(
                            "[Phase2] 开始下载URL图片到本地COS | count=%s",
                            len(output_data.generated_image_urls),
                        )
                        original_urls, thumbnail_urls = (
                            await storage_service.save_generated_images_with_thumbnails(
                                output_data.generated_image_urls,
                                input_data.owner_operator_id,
                                input_data.task_id,
                                input_data.item_id,
                            )
                        )
                        output_data.generated_image_urls = original_urls
                        output_data.generated_image_thumbnail_urls = thumbnail_urls
                        logger.info(
                            "[Phase2] URL图片下载完成 | originals=%s | thumbnails=%s",
                            len(original_urls),
                            len([t for t in thumbnail_urls if t]),
                        )
                    except Exception as e:
                        logger.warning(
                            "[Phase2] URL图片下载失败，使用原始URL | error=%s",
                            str(e)[:100],
                        )

                # 保存 base64 图片到本地COS
                base64_images = image_result.get("base64_images", [])
                if base64_images:
                    try:
                        from app.services.storage_service import get_storage_service

                        storage_service = get_storage_service()

                        logger.info(
                            "[Phase2] 开始保存Base64图片到本地COS | count=%s",
                            len(base64_images),
                        )
                        saved_urls, saved_thumbnails = (
                            await storage_service.save_base64_images_with_thumbnails(
                                base64_images,
                                input_data.owner_operator_id,
                                input_data.task_id,
                                input_data.item_id,
                            )
                        )
                        # 合并到最终结果
                        output_data.generated_image_urls.extend(saved_urls)
                        output_data.generated_image_thumbnail_urls.extend(
                            saved_thumbnails
                        )
                        logger.info(
                            "[Phase2] Base64图片保存完成 | saved=%s | thumbnails=%s",
                            len(saved_urls),
                            len([t for t in saved_thumbnails if t]),
                        )
                    except Exception as e:
                        logger.warning(
                            "[Phase2] Base64图片保存失败 | error=%s", str(e)[:100]
                        )

                # 记录图片生成结果
                await log_execution_node(
                    item_id=input_data.item_id,
                    node_name="image_call",
                    node_status="success" if image_result.get("images") else "failed",
                    input_data={
                        "image_model_platform": input_data.image_model_platform,
                        "image_model_id": input_data.image_model_id,
                        "prompt_count": len(image_prompts),
                        "image_size_ratio": input_data.template_image_size_ratio,
                    },
                    output_data={
                        "images_count": len(image_result.get("images", [])),
                        "thumbnails_count": len(image_result.get("thumbnails", [])),
                    },
                    duration_ms=image_call_duration,
                )

                # 图片去重检测（使用独立的图片去重开关）
                if input_data.image_dedup_enabled and output_data.generated_image_urls:
                    await self._check_image_dedup(input_data, output_data)

            # ========== 完成 ==========
            # 如果是图文任务且所有图片生成都失败了，标记为失败（支持重试）
            if (
                input_data.content_type == "image_text"
                and image_prompts
                and not output_data.generated_image_urls
            ):
                output_data.success = False
                output_data.error_message = (
                    f"图片生成全部失败 | prompts={len(image_prompts)} | generated=0"
                )
                logger.error(
                    "[Phase2] 图片生成全部失败 | item_id=%s | prompts=%s",
                    input_data.item_id,
                    len(image_prompts),
                )
            else:
                output_data.success = True
            output_data.execution_completed_at = datetime.utcnow()

            logger.info(
                "[Phase2] AI生成完成 | item_id=%s | success=%s | title_len=%s | text_len=%s | images=%s",
                input_data.item_id,
                output_data.success,
                len(output_data.generated_title or ""),
                len(output_data.generated_text or ""),
                len(output_data.generated_image_urls),
            )

        except Exception as e:
            tb = traceback.format_exc()
            output_data.success = False
            output_data.error_message = f"{str(e)[:400]}\n---\n{tb[-500:]}"
            logger.error(
                "[Phase2] AI生成失败 | item_id=%s | error=%s\n%s",
                input_data.item_id,
                str(e)[:200],
                tb,
            )

        return output_data

    def _build_prompts(self, input_data: GenerationInputData) -> Tuple[str, List[str]]:
        """构建提示词（不访问数据库）

        分配原则：
        - System Prompt: 角色、规则、输出格式（不变的约束，使用 OptimizedContentGenerator 构建）
        - User Prompt: 具体任务、素材、创意配置（使用 OptimizedContentGenerator 构建）
        """
        config = self._build_optimized_config(input_data)
        from app.services.prompt_generator_optimized import OptimizedContentGenerator

        system_prompt, user_prompt = OptimizedContentGenerator._build_combined_prompts(
            config
        )
        return system_prompt, user_prompt

    def _build_optimized_config(
        self, input_data: GenerationInputData, retry_round: int = 0
    ) -> Dict[str, Any]:
        """
        从 GenerationInputData 构建 OptimizedContentGenerator 所需的 config dict

        完全无数据库访问，使用阶段1已加载的数据。
        retry_round > 0 表示去重重试，会重新随机选取爆款类型和创意种子。
        """
        config: Dict[str, Any] = {}

        # 平台
        config["platform"] = input_data.template_platform or "小红书"

        # 内容类型
        ct_map = {"text": "文案", "image_text": "图文", "video_text": "视频"}
        config["content_type"] = ct_map.get(input_data.content_type, "内容")

        # 图片配置
        image_count = getattr(input_data, "image_count", 4) or 4
        image_size_ratio = (
            getattr(input_data, "template_image_size_ratio", None) or "3:4"
        )
        config["image_count"] = image_count
        config["image_size_ratio"] = image_size_ratio

        # 参考素材（创作基础）
        if input_data.material_text_content:
            material_text = input_data.material_text_content
            if not isinstance(material_text, str):
                material_text = str(material_text)
            config["material"] = _AttrDict(
                title=input_data.material_title or "",
                text_content=material_text,
                topic="",
            )

        # 对标素材（参考学习，禁止抄袭）
        if input_data.benchmark_text_enabled and input_data.benchmark_material_text:
            benchmark_text = input_data.benchmark_material_text
            if not isinstance(benchmark_text, str):
                benchmark_text = str(benchmark_text)
            config["benchmark_material"] = _AttrDict(
                title=input_data.benchmark_material_title or "",
                text_content=benchmark_text,
            )

        # 模板创意 / 创作方向
        if (
            input_data.template_instruction
            and input_data.template_instruction.strip() not in ("无", "暂无", "")
        ):
            config["prompt_creative"] = input_data.template_instruction

        # 模板指令 / 具体要求
        if input_data.template_prompt:
            config["template_instruction"] = input_data.template_prompt

        # 产品名称（必填，如果为空则使用默认值）
        product_name = input_data.template_product_name
        if not product_name or not product_name.strip():
            product_name = "产品"
        config["product_name"] = product_name

        # 产品卖点
        if input_data.template_product_selling_points:
            try:
                points_text = "、".join(
                    str(p) for p in input_data.template_product_selling_points
                )
            except Exception:
                points_text = str(input_data.template_product_selling_points)
            if points_text:
                config["product_selling_points"] = points_text

        # 创作者账号定位
        sub_user_profile = {}
        if input_data.sub_user_follower_profile:
            sub_user_profile["fan_persona"] = input_data.sub_user_follower_profile
        if input_data.sub_user_account_positioning:
            sub_user_profile["account_positioning"] = (
                input_data.sub_user_account_positioning
            )
        if input_data.sub_user_content_style:
            sub_user_profile["content_style"] = input_data.sub_user_content_style
        if sub_user_profile:
            config["sub_user_profile"] = sub_user_profile

        # 爆款类型配置
        seeds = input_data.template_seeds or {}
        raw_seed_config = input_data.raw_seed_config or {}
        import random as _random

        from app.services.prompt_generator_optimized import OptimizedContentGenerator

        viral_type = seeds.get("viral_type")
        if not viral_type:
            viral_type = "seeding"
        # 原始配置为 "auto" 时，每次调用都重新随机选取（包括去重重试时）
        raw_viral_type = raw_seed_config.get("viral_type")
        if raw_viral_type == "auto":
            viral_type = _random.choice(
                list(OptimizedContentGenerator.VIRAL_TYPE_CONFIGS.keys())
            )
            if retry_round > 0:
                logger.info(
                    "[Phase2 config] 去重重试第%s轮，重新随机爆款类型: %s",
                    retry_round,
                    viral_type,
                )
            else:
                logger.debug(
                    "[Phase2 config] 爆款类型为 auto，随机选择: %s", viral_type
                )
        viral_config = OptimizedContentGenerator.VIRAL_TYPE_CONFIGS.get(viral_type)
        config["viral_type"] = viral_type
        config["viral_config"] = viral_config

        # 创意种子（创建 wrapper 使 OptimizedContentGenerator 可消费）
        # 去重重试时，对原本是 "auto" 的种子类型从候选池中重新随机选取
        creative_seeds = {}
        seed_type_labels = {
            "opening": "开头模式",
            "emotion": "情感基调",
            "ending": "结尾方式",
        }
        candidates_cache = input_data.seed_candidates_for_auto or {}

        for seed_type in ("opening", "emotion", "ending"):
            raw_sid = raw_seed_config.get(seed_type) if raw_seed_config else None

            if raw_sid == "auto" and seed_type in candidates_cache:
                # 从缓存的候选池中随机选择一个（每次调用可能选到不同的）
                candidates = candidates_cache[seed_type]
                if candidates:
                    chosen = _random.choice(candidates)
                    label = seed_type_labels.get(seed_type, seed_type)

                    # 构建完整的种子信息（包括模板列表、示例列表等）
                    # chosen 包含: name, template (list), example_phrases (list), description, avoid_phrases (list)
                    templates = chosen.get("template", [])
                    if isinstance(templates, str):
                        templates = [templates]

                    examples = chosen.get("example_phrases", [])
                    if isinstance(examples, str):
                        examples = [examples]

                    description = chosen.get("description", "")
                    avoids = chosen.get("avoid_phrases", [])
                    if isinstance(avoids, str):
                        avoids = [avoids]

                    # 创建 wrapper，传递完整信息
                    creative_seeds[seed_type] = _SeedPromptWrapper(
                        name=f"{label}：{chosen['name']}",
                        templates=templates,
                        examples=examples,
                        description=description,
                        avoids=avoids,
                    )

                    if retry_round > 0:
                        logger.info(
                            "[Phase2 config] 去重重试第%s轮，重新随机%s: %s | templates=%s | examples=%s",
                            retry_round,
                            seed_type,
                            chosen["name"],
                            len(templates),
                            len(examples),
                        )
            else:
                # 非 auto 的种子，直接用 Phase1 加载的内容
                # seeds 包含: opening_seed_content, emotion_seed_content, ending_seed_content
                # 这些是数据库查询的种子对象，需要提取完整信息
                seed_obj = seeds.get(seed_type)
                if seed_obj and hasattr(seed_obj, "to_prompt"):
                    # 如果是数据库对象，直接使用
                    creative_seeds[seed_type] = seed_obj
                elif seed_obj:
                    # 如果是字典或其他格式，尝试提取信息
                    label = seed_type_labels.get(seed_type, seed_type)
                    templates = (
                        seed_obj.get("template", [])
                        if isinstance(seed_obj, dict)
                        else []
                    )
                    examples = (
                        seed_obj.get("example_phrases", [])
                        if isinstance(seed_obj, dict)
                        else []
                    )
                    description = (
                        seed_obj.get("description", "")
                        if isinstance(seed_obj, dict)
                        else ""
                    )
                    avoids = (
                        seed_obj.get("avoid_phrases", [])
                        if isinstance(seed_obj, dict)
                        else []
                    )

                    if templates or examples:
                        creative_seeds[seed_type] = _SeedPromptWrapper(
                            name=f"{label}",
                            templates=templates,
                            examples=examples,
                            description=description,
                            avoids=avoids,
                        )

        if creative_seeds:
            config["creative_seeds"] = creative_seeds
            logger.debug(
                "[Phase2 config] 创意种子已注入 | %s", list(creative_seeds.keys())
            )
        else:
            logger.debug(
                "[Phase2 config] 创意种子为空 | seeds_keys=%s",
                list(seeds.keys()) if isinstance(seeds, dict) else type(seeds),
            )

        # 历史参考
        if input_data.historical_texts:
            config["dedup_history"] = input_data.historical_texts

        # 对标图片启用状态（用于图片提示词生成）
        config["benchmark_image_enabled"] = input_data.benchmark_image_enabled

        return config

    @staticmethod
    def _sanitize_image_role_desc(desc) -> str:
        """
        清理对标图角色描述文本

        处理多种格式：
        - Python list: ['style', 'scene']
        - JSON array: ["style", "scene"]
        - Python repr 字符串: "['style']"
        - 普通字符串: "style, scene"
        """
        if isinstance(desc, (list, tuple)):
            return "、".join(str(d) for d in desc)
        if not isinstance(desc, str):
            return str(desc)
        desc = desc.strip()
        # 处理 Python repr 格式的字符串，如 "['style']" 或 "['style', 'scene']"
        if desc.startswith("[") and desc.endswith("]"):
            inner = desc[1:-1]
            try:
                # 尝试 ast 解析
                import ast

                parsed = ast.literal_eval(desc)
                if isinstance(parsed, list):
                    return "、".join(str(p) for p in parsed)
            except (ValueError, SyntaxError):
                pass
            # 简单拆分：去掉引号
            items = [i.strip().strip("'\"") for i in inner.split(",") if i.strip()]
            return "、".join(items)
        return desc

    def _construct_image_prompts(self, input_data: GenerationInputData) -> List[str]:
        """构建图片生成提示词列表（兜底方案，当 LLM 未生成 image_prompts 时使用）"""
        prompts = []

        # 获取模板指令和提示词模板
        template_instruction = input_data.template_instruction or ""
        template_prompt = input_data.template_prompt or ""

        # 过滤掉无效的指令（如"无"、"暂无"等占位符）
        if template_instruction.strip() in ("无", "暂无", "无创意", ""):
            template_instruction = ""
        if template_prompt.strip() in ("无", "暂无", "", "无提示词模板"):
            template_prompt = ""

        # 构建风格前缀
        style_prefix_parts = []
        if input_data.template_style:
            style_prefix_parts.append(input_data.template_style)
        elif input_data.sub_user_content_style:
            style_prefix_parts.append(input_data.sub_user_content_style)

        style_prefix = (
            f"{'，'.join(style_prefix_parts)}，" if style_prefix_parts else ""
        )

        # 根据对标图片参考生成提示词
        if input_data.benchmark_image_enabled and input_data.benchmark_image_roles:
            # 有角色配置时，按角色生成
            roles_list = input_data.benchmark_image_roles
            if isinstance(roles_list, dict):
                # 兼容 dict 格式：{"role1": "desc1", ...} → [{"role": "role1", "description": "desc1"}, ...]
                roles_list = [
                    {"role": k, "description": v if isinstance(v, str) else str(v)}
                    for k, v in roles_list.items()
                ]
            if isinstance(roles_list, list):
                for i, role_info in enumerate(roles_list[: input_data.image_count]):
                    if isinstance(role_info, dict):
                        role = role_info.get("role", f"配图{i+1}")
                        desc = role_info.get("description", "")
                    # 尝试解析 description 中的 JSON 结构
                    subject = desc
                    layout = ""
                    color_style = ""
                    if isinstance(desc, str):
                        try:
                            detail = json.loads(desc)
                            # detail 可能是 dict 或 list
                            if isinstance(detail, dict):
                                subject = detail.get(
                                    "subject", detail.get("description", desc)
                                )
                                layout = detail.get(
                                    "composition", detail.get("layout", "")
                                )
                                color_style = detail.get(
                                    "color_style", detail.get("style", "")
                                )
                            elif isinstance(detail, list):
                                # 如果是列表，取第一个元素或拼接
                                if detail and isinstance(detail[0], dict):
                                    first_item = detail[0]
                                    subject = first_item.get(
                                        "subject", first_item.get("description", desc)
                                    )
                                    layout = first_item.get(
                                        "composition", first_item.get("layout", "")
                                    )
                                    color_style = first_item.get(
                                        "color_style", first_item.get("style", "")
                                    )
                                else:
                                    # 列表元素是字符串，拼接
                                    subject = "、".join(
                                        str(item) for item in detail[:3]
                                    )
                        except (json.JSONDecodeError, TypeError):
                            pass
                    prompt_parts = []
                    if style_prefix:
                        prompt_parts.append(style_prefix)
                    if subject:
                        prompt_parts.append(f"主体：{subject}")
                    if layout:
                        prompt_parts.append(f"构图：{layout}")
                    if color_style:
                        prompt_parts.append(f"风格：{color_style}")
                    prompt_parts.append(f"角色定位：{role}")
                    # 加入模板指令和提示词模板
                    if template_instruction:
                        prompt_parts.append(f"创作方向：{template_instruction}")
                    if template_prompt:
                        prompt_parts.append(f"生图要求：{template_prompt}")
                    prompt_parts.append("高清、精美、适合社交媒体配图")
                    prompts.append("，".join(prompt_parts))
        elif (
            input_data.benchmark_image_enabled and input_data.benchmark_material_images
        ):
            # 有对标图片但没有角色配置
            for i in range(input_data.image_count):
                prompt_parts = [style_prefix] if style_prefix else []
                if input_data.template_product_selling_points:
                    try:
                        pts = [
                            str(p)
                            for p in input_data.template_product_selling_points[:3]
                        ]
                        prompt_parts.append(f"突出卖点：{'、'.join(pts)}")
                    except Exception:
                        prompt_parts.append(
                            f"突出卖点：{input_data.template_product_selling_points}"
                        )
                prompt_parts.append("参考对标素材的构图和风格")
                # 加入模板指令和提示词模板
                if template_instruction:
                    prompt_parts.append(f"创作方向：{template_instruction}")
                if template_prompt:
                    prompt_parts.append(f"生图要求：{template_prompt}")
                prompt_parts.append("高清、精美、适合社交媒体配图")
                prompts.append("，".join(prompt_parts))

        # 填充到所需数量
        while len(prompts) < input_data.image_count:
            prompt_parts = [style_prefix] if style_prefix else []
            if input_data.template_product_selling_points:
                try:
                    pts = [
                        str(p) for p in input_data.template_product_selling_points[:3]
                    ]
                    prompt_parts.append(f"体现卖点：{'、'.join(pts)}")
                except Exception:
                    prompt_parts.append(
                        f"体现卖点：{input_data.template_product_selling_points}"
                    )
            # 加入模板指令和提示词模板
            if template_instruction:
                prompt_parts.append(f"创作方向：{template_instruction}")
            if template_prompt:
                prompt_parts.append(f"生图要求：{template_prompt}")
            prompt_parts.append("精美构图，光线柔和，高清画质，适合社交媒体配图")
            prompt = "，".join(prompt_parts)
            prompts.append(prompt)

        # 记录生成的提示词（用于调试）
        if template_instruction or template_prompt:
            logger.info(
                "[_construct_image_prompts] 已加入模板指令 | count=%s | example=%s",
                len(prompts),
                prompts[0][:200] if prompts else "",
            )

        return prompts[: input_data.image_count]

    async def _generate_text_with_retry(
        self,
        prompt: str,
        input_data: GenerationInputData,
        output_data: GenerationOutputData,
        max_retries: int = 2,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> GenerationResult:
        """生成文案（使用预加载配置 + LLM 调用重试 + 可选预构建 system_prompt）

        Args:
            prompt: 用户提示词
            input_data: 输入数据
            output_data: 输出数据
            max_retries: 最大重试次数
            system_prompt: 系统提示词
            temperature: 温度参数（可选，用于去重重试时提高随机性）
        """
        from app.adapters.factory import ModelAdapterFactory

        logger.info(
            "[Phase2] LLM调用 | prompt_len=%s | platform=%s | model_id=%s | temperature=%s",
            len(prompt),
            input_data.model_platform,
            input_data.model_id,
            temperature,
        )

        # 使用阶段1预加载的模型配置（无需数据库连接）
        model_config = input_data.text_model_config
        if not model_config:
            logger.error("[Phase2] 未预加载文本模型配置")
            return GenerationResult(
                success=False,
                error_message="Text model config not preloaded in phase1",
            )

        platform = input_data.model_platform or "bailian"

        # 调试日志：验证模型配置
        logger.debug(
            "[Phase2] 准备创建文本适配器 | platform=%s | model_id=%s | api_key_len=%s | base_url=%s",
            platform,
            model_config.model_id,
            len(model_config.api_key) if model_config.api_key else 0,
            model_config.base_url,
        )

        try:
            adapter = ModelAdapterFactory.create_adapter(
                platform=platform,
                config=model_config,
                validate=True,
            )
        except Exception as e:
            logger.error("[Phase2] 创建适配器失败 | error=%s", str(e)[:200])
            return GenerationResult(success=False, error_message=str(e)[:500])

        # LLM 调用带重试
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # 构建 TextGenParams，从 model_config 读取配置
                extra_params = model_config.extra_params or {}
                text_params = TextGenParams(
                    model_id=model_config.model_id,
                    max_tokens=extra_params.get("max_tokens", 32000),
                    temperature=extra_params.get(
                        "temperature", temperature if temperature is not None else 0.7
                    ),
                    top_p=extra_params.get("top_p", 0.8),
                    enable_thinking=(platform.lower() == "bailian")
                    and extra_params.get("enable_thinking", True),
                )

                # 在调用之前完成变量替换
                formatted_prompt = adapter.format_prompt(
                    prompt, input_data.variable_values
                )
                formatted_system = (
                    adapter.format_prompt(system_prompt, input_data.variable_values)
                    if system_prompt
                    else None
                )

                result = await adapter.generate_text(
                    user_prompt=formatted_prompt,
                    system_prompt=formatted_system,
                    params=text_params,
                )

                if result.success:
                    if attempt > 0:
                        logger.info(
                            "[Phase2] LLM重试成功 | attempt=%s/%s",
                            attempt + 1,
                            max_retries + 1,
                        )
                    logger.info(
                        "[Phase2] LLM生成成功 | text_len=%s",
                        len(result.text) if result.text else 0,
                    )
                    return result

                # 检查是否需要重试
                if result.error_type in ("server_error", "network_error", "rate_limit"):
                    last_error = result
                    if attempt < max_retries:
                        wait_time = 2**attempt
                        logger.warning(
                            "[Phase2] LLM瞬态错误，准备重试 | attempt=%s/%s | error=%s | wait=%ss",
                            attempt + 1,
                            max_retries + 1,
                            (
                                result.error_message[:100]
                                if result.error_message
                                else "unknown"
                            ),
                            wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    # 客户端错误不重试
                    logger.error(
                        "[Phase2] LLM生成失败(不可重试) | error=%s",
                        result.error_message,
                    )
                    return result

            except Exception as e:
                last_error = GenerationResult(
                    success=False,
                    error_message=str(e)[:500],
                    error_type="network_error",
                )
                if attempt < max_retries:
                    wait_time = 2**attempt
                    logger.warning(
                        "[Phase2] LLM调用异常，准备重试 | attempt=%s/%s | error=%s | wait=%ss",
                        attempt + 1,
                        max_retries + 1,
                        str(e)[:100],
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("[Phase2] LLM重试耗尽 | error=%s", str(e)[:200])

        # 所有重试失败
        return last_error or GenerationResult(
            success=False,
            error_message="LLM generation failed after all retries",
            error_type="server_error",
        )

    async def _generate_images(
        self,
        prompts: List[str],
        input_data: GenerationInputData,
    ) -> Dict[str, List[str]]:
        """生成图片（Base64 参考图 + 对标图/产品图区分 + 角色要求注入 + 并行生成）"""
        from app.adapters.factory import ModelAdapterFactory
        from app.services.storage_service import get_storage_service

        # 优先使用独立的图片模型配置
        model_config = input_data.image_model_config
        platform = input_data.image_model_platform

        if not model_config or not platform:
            logger.warning(
                "[Phase2] 未配置独立图片模型，跳过图片生成 | item_id=%s",
                input_data.item_id,
            )
            return {"images": [], "thumbnails": []}

        # ===== 步骤A：收集并转换所有参考图 =====
        storage_service = get_storage_service()

        # 根据图片模型平台决定 prefer_url 参数
        # 即梦（jimeng）等火山引擎系平台不支持 data URL（base64），需要公网 URL
        # 百炼（bailian）、可灵（kling）等平台支持 base64 参考图
        image_platform = input_data.image_model_platform or ""
        prefer_url_for_platform = image_platform in ("jimeng", "volcengine")

        # 对标图（用于构图/场景/风格参考）
        benchmark_ref_list: List[str] = []
        if input_data.benchmark_image_enabled and input_data.benchmark_material_images:
            for url in input_data.benchmark_material_images:
                ref_url, ref_b64 = await storage_service.process_reference_image(
                    url,
                    prefer_url=prefer_url_for_platform,
                    max_size_bytes=4 * 1024 * 1024,
                )
                if prefer_url_for_platform and ref_url:
                    benchmark_ref_list.append(ref_url)
                elif ref_b64:
                    benchmark_ref_list.append(ref_b64)
            logger.info(
                "[Phase2] 对标图转换 | total=%s | success=%s | use_url=%s | platform=%s",
                len(input_data.benchmark_material_images),
                len(benchmark_ref_list),
                prefer_url_for_platform,
                image_platform,
            )

        # 产品图（用于主体外观参考）
        # 优先使用模板附件中的产品图，回退到素材附件
        product_urls = input_data.template_product_images or input_data.material_images
        product_ref_list: List[str] = []
        if product_urls:
            for url in product_urls:
                ref_url, ref_b64 = await storage_service.process_reference_image(
                    url,
                    prefer_url=prefer_url_for_platform,
                    max_size_bytes=4 * 1024 * 1024,
                )
                if prefer_url_for_platform and ref_url:
                    product_ref_list.append(ref_url)
                elif ref_b64:
                    product_ref_list.append(ref_b64)
            logger.info(
                "[Phase2] 产品图转换 | total=%s | success=%s | use_url=%s | platform=%s",
                len(product_urls),
                len(product_ref_list),
                prefer_url_for_platform,
                image_platform,
            )

        # 解析对标图角色配置（list 格式，按索引对应每张对标图）
        bench_roles_list = self._parse_benchmark_roles(input_data)

        logger.info(
            "[Phase2] 图片生成 | prompts=%s | platform=%s | model_id=%s | benchmark_refs=%s | product_refs=%s",
            len(prompts),
            platform,
            model_config.model_id,
            len(benchmark_ref_list),
            len(product_ref_list),
        )

        # 调试日志：验证图片模型配置
        logger.debug(
            "[Phase2] 准备创建图片适配器 | platform=%s | model_id=%s | api_key_len=%s | base_url=%s",
            platform,
            model_config.model_id,
            len(model_config.api_key) if model_config.api_key else 0,
            model_config.base_url,
        )

        # ===== 步骤B：创建适配器 =====
        try:
            adapter = ModelAdapterFactory.create_adapter(
                platform=platform,
                config=model_config,
                validate=True,
            )
        except Exception as e:
            logger.error("[Phase2] 创建图片适配器失败 | error=%s", str(e)[:200])
            return {"images": [], "thumbnails": []}

        # ===== 步骤C：并行生成所有图片 =====
        image_size_ratio = (
            getattr(input_data, "template_image_size_ratio", None) or "3:4"
        )
        add_watermark = getattr(input_data, "template_add_watermark", False)

        async def _generate_single(
            i: int, prompt: str
        ) -> Tuple[int, Optional[str], Optional[str]]:
            """生成单张图片，返回 (index, image_url, thumbnail_url)

            参考图传入规则（每张生成图独立选图）：
            - 第1张（图1）：对标图按顺序循环取 — benchmark[i % len(benchmarks)]
            - 第2张、第3张（图2、图3）：从产品图随机选 2 张
            """
            selected_refs: List[str] = []
            n_benchmark = 0
            n_product = 0
            benchmark_role_text = ""

            # 对标图：按索引顺序循环取，每张生成图用一张不同的对标图
            if benchmark_ref_list:
                bench_idx = i % len(benchmark_ref_list)
                selected_refs.append(benchmark_ref_list[bench_idx])
                n_benchmark = 1
                # 取对应对标图的角色要求（用模型视角：它收到的数组里这就是第1张）
                if bench_idx < len(bench_roles_list):
                    role_info = bench_roles_list[bench_idx]
                    roledesc = self._sanitize_image_role_desc(
                        role_info.get("description", "")
                    )
                    if roledesc:
                        benchmark_role_text = f"第1张（对标图）：请重点参考其{roledesc}，该图片主体产品不作为生成对象"

            # 产品图：随机取 2 张
            if product_ref_list:
                n_product = min(2, len(product_ref_list))
                sampled = (
                    random.sample(product_ref_list, n_product)
                    if n_product > 1
                    else [random.choice(product_ref_list)]
                )
                selected_refs.extend(sampled)

            # 构建增强 prompt（从生图模型视角描述参考图用途）
            enhanced_prompt = prompt
            extra_parts = []
            if benchmark_role_text:
                extra_parts.append(f"【参考图说明】\n{benchmark_role_text}")
            if n_benchmark > 0 and n_product > 0:
                extra_parts.append(
                    "第2张、第3张为产品参考图，参考其主体外观，保持主体的轮廓、比例、样式、色彩、纹理、材质、细节等"
                )
            if extra_parts:
                enhanced_prompt = f"{prompt}\n\n" + "\n".join(extra_parts)

            logger.info(
                "[Phase2] 生成图片 %d/%d | 对标图=原始索引%s | 产品参考图=%s张",
                i + 1,
                len(prompts),
                (i % len(benchmark_ref_list)) + 1 if benchmark_ref_list else 0,
                n_product,
            )

            try:
                # 构建 ImageGenParams，从 model_config 读取配置
                extra_params = model_config.extra_params or {}
                image_params = ImageGenParams(
                    model_id=model_config.model_id,
                    count=1,
                    ratio=image_size_ratio,
                    quality=extra_params.get("quality", "high"),
                    watermark=add_watermark,
                    reference_images=selected_refs or None,
                    benchmark_image_count=n_benchmark,  # 前N张为对标图
                )

                # 在调用之前完成变量替换
                formatted_prompt = adapter.format_prompt(
                    enhanced_prompt, input_data.variable_values
                )

                result = await adapter.generate_image(
                    prompt=formatted_prompt,
                    params=image_params,
                )

                if result.success:
                    # 优先使用 URL，如果没有则使用 base64
                    if result.image_urls:
                        thumb = (
                            result.thumbnail_urls[0]
                            if hasattr(result, "thumbnail_urls")
                            and result.thumbnail_urls
                            else None
                        )
                        return i, {
                            "type": "url",
                            "data": result.image_urls[0],
                            "thumbnail": thumb,
                        }
                    elif result.image_base64_list:
                        # 返回 base64 数据，稍后由调用方保存
                        return i, {
                            "type": "base64",
                            "data": result.image_base64_list[0],
                        }
                    else:
                        logger.warning(
                            "[Phase2] 图片生成成功但无返回数据 | prompt=%s", prompt[:50]
                        )
                        return i, None, None
                else:
                    logger.warning(
                        "[Phase2] 图片生成失败 | prompt=%s | error=%s",
                        prompt[:50],
                        result.error_message,
                    )
                    return i, None, None
            except Exception as e:
                logger.warning(
                    "[Phase2] 单张图片生成异常 | prompt=%s | error=%s",
                    prompt[:50],
                    str(e)[:100],
                )
                return i, None, None

        tasks = [_generate_single(i, prompt) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sorted_results = sorted(
            [r for r in results if isinstance(r, tuple) and r[1] is not None],
            key=lambda x: x[0],
        )

        # 分离 URL 和 base64 数据
        images = []
        base64_images = []
        thumbnails = []

        for r in sorted_results:
            img_data = r[1]
            if isinstance(img_data, dict):
                if img_data["type"] == "url":
                    images.append(img_data["data"])
                    if img_data.get("thumbnail"):
                        thumbnails.append(img_data["thumbnail"])
                elif img_data["type"] == "base64":
                    base64_images.append(img_data["data"])
            else:
                # 兼容旧格式（直接是 URL 字符串）
                images.append(img_data)

        logger.info(
            "[Phase2] 图片生成完成 | urls=%s | base64=%s | total=%s",
            len(images),
            len(base64_images),
            len(prompts),
        )
        return {
            "images": images,
            "base64_images": base64_images,
            "thumbnails": thumbnails,
        }

    def _parse_benchmark_roles(
        self, input_data: GenerationInputData
    ) -> List[Dict[str, Any]]:
        """
        解析对标图角色配置为有序列表

        对标图角色配置（benchmark_image_roles）定义了每张对标图的使用方式：
        如构图、场景、色彩风格、光影等。

        Returns:
            有序列表 [{"role": "benchmark_1", "description": "style, scene"}, ...]
            按索引对应每张对标图
        """
        roles = input_data.benchmark_image_roles
        if not roles:
            return []

        if isinstance(roles, dict):
            # dict 格式：按 key 排序保证顺序稳定
            sorted_items = sorted(roles.items(), key=lambda x: str(x[0]))
            return [
                {"role": k, "description": v if isinstance(v, str) else str(v)}
                for k, v in sorted_items
            ]

        if isinstance(roles, list):
            return [r for r in roles if isinstance(r, dict)]

        return []

    async def _check_dedup(
        self,
        input_data: GenerationInputData,
        output_data: GenerationOutputData,
    ) -> bool:
        """
        去重检测（使用独立数据库连接）

        embedding 在检测完成后直接异步保存。
        """
        try:
            from app.models import GenerationItem
            from app.services.async_embedding_service import (
                AsyncEmbeddingService,
                EmbeddingSaveRequest,
            )
            from app.services.dedup_service import DedupService

            # 创建临时的 GenerationItem 对象用于去重检测
            temp_item = GenerationItem(
                id=input_data.item_id,
                task_id=input_data.task_id,
                owner_operator_id=input_data.owner_operator_id,
                sub_user_id=input_data.sub_user_id,
            )

            # 使用独立 session 进行去重检测
            async with async_session_maker() as db:
                dedup_result = await DedupService.check_text_duplication_with_scope(
                    db=db,
                    item=temp_item,
                    text=output_data.generated_text,
                    scope=input_data.dedup_scope,
                    task_id=input_data.task_id,
                    threshold=input_data.dedup_threshold,
                    save_embedding=True,
                )

            output_data.dedup_passed = dedup_result.passed
            output_data.dedup_similarity = dedup_result.max_similarity
            output_data.dedup_references = dedup_result.references
            output_data.text_embedding = dedup_result.embedding

            # 直接异步保存 embedding（不阻塞主流程）
            if dedup_result.embedding:
                request = EmbeddingSaveRequest(
                    item_id=input_data.item_id,
                    owner_operator_id=input_data.owner_operator_id,
                    task_id=input_data.task_id,
                    content_type="text",
                    content=output_data.generated_text,
                    content_hash=hashlib.sha256(
                        output_data.generated_text.encode("utf-8")
                    ).hexdigest(),
                    embedding=dedup_result.embedding,
                    content_index=0,
                )
                asyncio.create_task(AsyncEmbeddingService.save_embedding_async(request))
                logger.debug(
                    "[Phase2] embedding 已提交异步保存 | item_id=%s", input_data.item_id
                )

            return dedup_result.passed

        except Exception as e:
            logger.error("[Phase2] 去重检测失败 | error=%s", str(e)[:100])
            return True

    async def _check_image_dedup(
        self,
        input_data: GenerationInputData,
        output_data: GenerationOutputData,
    ) -> None:
        """
        图片去重检测：检查生成的图片是否与历史素材高度相似

        对每张生成的图片检查与对标素材和历史图片的相似度。
        去重结果记录到 output_data 中，不阻断流程。
        """
        try:
            from app.models import GenerationItem
            from app.services.dedup_service import DedupService

            temp_item = GenerationItem(
                id=input_data.item_id,
                task_id=input_data.task_id,
                owner_operator_id=input_data.owner_operator_id,
                sub_user_id=input_data.sub_user_id,
            )

            image_dedup_results = []
            async with async_session_maker() as db:
                for i, img_url in enumerate(output_data.generated_image_urls):
                    try:
                        dedup_result = (
                            await DedupService.check_image_duplication_with_scope(
                                db=db,
                                generated_image_url=img_url,
                                item=temp_item,
                                scope=input_data.dedup_scope,
                                task_id=input_data.task_id,
                                threshold=input_data.dedup_threshold,
                            )
                        )
                        image_dedup_results.append(
                            {
                                "index": i,
                                "passed": dedup_result.passed,
                                "similarity": dedup_result.max_similarity,
                            }
                        )
                        if not dedup_result.passed:
                            logger.warning(
                                "[Phase2] 图片去重检测未通过 | item_id=%s | image_index=%s | similarity=%.2f",
                                input_data.item_id,
                                i,
                                dedup_result.max_similarity,
                            )
                    except Exception as img_e:
                        logger.warning(
                            "[Phase2] 单张图片去重检测失败 | item_id=%s | image_index=%s | error=%s",
                            input_data.item_id,
                            i,
                            str(img_e)[:100],
                        )
                        image_dedup_results.append(
                            {
                                "index": i,
                                "passed": True,
                                "similarity": 0.0,
                                "error": str(img_e)[:100],
                            }
                        )

            output_data.dedup_references = image_dedup_results
            logger.info(
                "[Phase2] 图片去重完成 | item_id=%s | total_images=%s | passed=%s/%s",
                input_data.item_id,
                len(image_dedup_results),
                sum(1 for r in image_dedup_results if r.get("passed", True)),
                len(image_dedup_results),
            )

        except Exception as e:
            logger.error("[Phase2] 图片去重检测失败 | error=%s", str(e)[:100])
            # 图片去重异常不阻断流程

    def _parse_generated_text(self, text: Optional[str]) -> Dict[str, Any]:
        """解析生成的文本"""
        result = {
            "title": None,
            "content": None,
            "topics": [],
            "image_prompts": [],
        }

        if not text:
            return result

        import re

        text_to_parse = text.strip()

        # 统一换行符，避免 \r\n 问题
        text_to_parse = text_to_parse.replace("\r\n", "\n").replace("\r", "\n")

        # 方法1：使用 re.search 查找代码块（不要求整个字符串匹配）
        json_block_pattern = r"```(?:json)?\s*\n(.*?)\n\s*```"
        match = re.search(json_block_pattern, text_to_parse, re.DOTALL)
        if match:
            text_to_parse = match.group(1).strip()
            logger.debug("[Phase2] 从代码块中提取 JSON | length=%s", len(text_to_parse))
        else:
            # 方法2：尝试直接解析（可能没有代码块包裹）
            # 如果以 { 开头，直接尝试解析
            if text_to_parse.startswith("{"):
                pass  # 保持原样
            else:
                # 尝试查找第一个 { 和最后一个 }
                first_brace = text_to_parse.find("{")
                last_brace = text_to_parse.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    text_to_parse = text_to_parse[first_brace:last_brace + 1]
                    logger.debug(
                        "[Phase2] 提取 {} 之间的内容 | length=%s", len(text_to_parse)
                    )

        try:
            data = json.loads(text_to_parse)
            result["title"] = data.get("title")
            result["content"] = data.get("content")
            result["topics"] = data.get("topics", [])
            result["image_prompts"] = data.get("image_prompts", [])
            logger.info(
                "[Phase2] JSON解析成功 | title=%s | content_len=%s | topics=%s | image_prompts=%s",
                result["title"][:30] if result["title"] else None,
                len(result["content"]) if result["content"] else 0,
                len(result["topics"]),
                len(result["image_prompts"]),
            )
        except json.JSONDecodeError as e:
            logger.warning(
                "[Phase2] JSON解析失败，使用原始文本 | error=%s | text_len=%s | first_100=%s",
                str(e)[:50],
                len(text_to_parse),
                text_to_parse[:100],
            )
            result["content"] = text

        return result


async def execute_phase2_generation(
    input_data: GenerationInputData,
) -> GenerationOutputData:
    """执行阶段2生成"""
    generator = Phase2Generator()
    return await generator.execute(input_data)


# ============================================
# 阶段3：结果保存
# ============================================


async def phase3_save_result(
    output_data: GenerationOutputData,
    owner_operator_id: int,
) -> bool:
    """
    阶段3：保存生成结果到数据库（带死锁重试）

    使用独立 session 保存数据后立即关闭，连接持有时间 <1秒。
    多 worker 并发更新同一 task 的计数器时可能死锁，自动重试最多 3 次。

    Args:
        output_data: 生成结果数据容器
        owner_operator_id: 创作管理员ID

    Returns:
        是否保存成功
    """
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            return await _phase3_save_once(output_data, owner_operator_id, attempt)
        except Exception as e:
            is_deadlock = "Deadlock" in str(e) or "1213" in str(e)
            if is_deadlock and attempt < MAX_RETRIES - 1:
                wait = (2**attempt) * 0.1  # 0.1s, 0.2s, 0.4s
                logger.warning(
                    "[Phase3] 死锁重试 | item_id=%s | attempt=%s/%s | wait=%.1fs",
                    output_data.item_id,
                    attempt + 1,
                    MAX_RETRIES,
                    wait,
                )
                await asyncio.sleep(wait)
                continue
            logger.error("[Phase3] 保存结果失败 | error=%s", str(e)[:200])
            return False
    return False


async def _phase3_save_once(
    output_data: GenerationOutputData,
    owner_operator_id: int,
    attempt: int = 0,
) -> bool:
    """阶段3单次保存（独立 session）"""
    start_time = datetime.utcnow()
    if attempt == 0:
        logger.info(
            "[Phase3] 开始保存结果 | item_id=%s | success=%s",
            output_data.item_id,
            output_data.success,
        )

    async with async_session_maker() as db:
        # 查询子任务
        item_result = await db.execute(
            select(GenerationItem).where(
                and_(
                    GenerationItem.id == output_data.item_id,
                    GenerationItem.owner_operator_id == owner_operator_id,
                )
            )
        )
        item = item_result.scalar_one_or_none()
        if not item:
            logger.error("[Phase3] 子任务不存在 | item_id=%s", output_data.item_id)
            return False

        # 更新子任务字段（生成内容相关）
        if output_data.success:
            item.generated_title = output_data.generated_title
            item.generated_text = output_data.generated_text
            item.output_topics = output_data.generated_topics
            item.generated_image_urls_json = output_data.generated_image_urls
            item.generated_image_thumbnails_json = (
                output_data.generated_image_thumbnail_urls
            )
            item.aigc_user_text_generator_user_prompt = (
                output_data.aigc_user_text_prompt
            )
            item.aigc_user_image_prompts_json = output_data.aigc_image_prompts
            item.output_user_text_prompt = output_data.output_user_text_prompt
            item.output_user_image_prompt = output_data.output_user_image_prompt
            item.output_system_text_prompt = output_data.output_system_text_prompt
            # 注意：status/completed_at/distribution_status 由 update_generation_item_status 统一管理，
            # 此处不设置，以确保 generating→completed 的计数器原子转换正确触发
        else:
            item.error_message = output_data.error_message

        item.execution_started_at = output_data.execution_started_at
        item.execution_completed_at = (
            output_data.execution_completed_at or datetime.utcnow()
        )
        item.updated_at = datetime.utcnow()

        # 更新任务状态和计数器
        from app.services.generation_service import GenerationService

        await GenerationService.update_generation_item_status(
            db,
            output_data.item_id,
            owner_operator_id,
            status="completed" if output_data.success else "failed",
            error_message=(
                output_data.error_message if not output_data.success else None
            ),
        )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "[Phase3] 结果保存完成 | elapsed=%.2fs | item_id=%s | success=%s",
            elapsed,
            output_data.item_id,
            output_data.success,
        )

        # 记录结果保存日志（在数据库事务内）
        save_log = GenerationItemExecutionLog(
            item_id=output_data.item_id,
            node_name="save_result",
            node_status="success" if output_data.success else "failed",
            input_data={
                "success": output_data.success,
                "attempt": attempt,
            },
            output_data={
                "title_saved": bool(output_data.generated_title),
                "text_saved": bool(output_data.generated_text),
                "images_saved": len(output_data.generated_image_urls or []),
                "status": "completed" if output_data.success else "failed",
            },
            error_data=(
                {"error_message": output_data.error_message}
                if not output_data.success
                else None
            ),
            duration_ms=int(elapsed * 1000),
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )
        db.add(save_log)
        await db.commit()

        return True
