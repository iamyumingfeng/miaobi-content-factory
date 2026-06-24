"""
创意种子库 (creative_seeds.py)

为自媒体文案生成提供强制差异化的创意种子，打破AI趋同性。

核心设计：
- 开头模式种子：强制不同的开头方式
- 情感基调种子：强制不同的情感表达
- 结尾模式种子：强制不同的收尾方式
- 创意种子组合：三者的随机组合，确保每次生成都有明显差异

Author: Claude Code
Date: 2026
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.creative_seed import CreativeSeed as CreativeSeedModel


class OpeningType(Enum):
    """开头模式类型"""

    COUNTER_INTUITIVE = "反常识"  # "没想到xxx居然..."
    SELF_MOCKERY = "自嘲吐槽"  # "我承认我冲动了"
    SUSPENSE = "悬念"  # "用了一个月，说句大实话"
    PAIN_POINT = "痛点场景"  # "凌晨三点还在..."
    CURIOSITY_GAP = "好奇缺口"  # "xxx和xxx的区别，终于搞明白了"
    SCENE_ENTRY = "场景切入"  # "那天朋友来家里..."
    EMOTION_HOOK = "情绪钩子"  # "说实话，一开始我是拒绝的"


class EmotionType(Enum):
    """情感基调类型"""

    CASUAL_ROAST = "轻松吐槽"  # 像朋友吐槽缺点，带点幽默
    SINCERE_SHARE = "真诚分享"  # 认真说体验，不夸张
    HESITANT_WATCH = "犹豫观望"  # 买之前纠结了很久的心态
    SURPRISE_FIND = "惊喜发现"  # 意外发现比预期好
    RATIONAL_COMPARE = "理性对比"  # 和同类产品对比的心态
    REGRET_RELIEF = "后悔释然"  # 后悔没早买/释然没踩坑
    INSIDER_TIP = "内行视角"  # 懂行人的专业视角


class EndingType(Enum):
    """结尾模式类型"""

    ASK_ADVICE = "求建议"  # "你们有啥好用的推荐吗？"
    INVITE_DISCUSS = "被讨论"  # "xx和xx你们选哪个？"
    LEAVE_SUSPENSE = "留悬念"  # "下一步准备试试xxx"
    RESONANCE = "共鸣式"  # "用过的都懂那种感觉"
    SUMMARY_FEELING = "总结感受"  # "总的来说，xxx"
    ACTION_HOOK = "行动钩子"  # "想入的可以冲了"


@dataclass
class OpeningSeed:
    """开头模式种子"""

    type: OpeningType
    template: str  # 模板示例
    forbidden_patterns: List[str]  # 禁止使用的开头模式
    description: str  # 使用说明

    def to_prompt(self) -> str:
        """转换为提示词格式"""
        return f"""【开头模式：{self.type.value}】
示例风格：{self.template}
创作要求：必须用"{self.type.value}"的方式开头，禁止使用以下开头模式：
{chr(10).join(f'- {p}' for p in self.forbidden_patterns)}
说明：{self.description}"""


@dataclass
class EmotionSeed:
    """情感基调种子"""

    type: EmotionType
    tone_description: str  # 基调描述
    example_phrases: List[str]  # 典型表达
    avoid_phrases: List[str]  # 避免的表达

    def to_prompt(self) -> str:
        """转换为提示词格式"""
        return f"""【情感基调：{self.type.value}】
基调要求：{self.tone_description}
典型表达（可参考但不限于）：{', '.join(self.example_phrases[:3])}
避免表达：{', '.join(self.avoid_phrases[:3])}"""


@dataclass
class EndingSeed:
    """结尾模式种子"""

    type: EndingType
    template: str
    description: str
    forbidden_patterns: List[str]

    def to_prompt(self) -> str:
        """转换为提示词格式"""
        return f"""【结尾模式：{self.type.value}】
示例风格：{self.template}
创作要求：必须用"{self.type.value}"的方式结尾，禁止使用以下结尾模式：
{chr(10).join(f'- {p}' for p in self.forbidden_patterns)}
说明：{self.description}"""


@dataclass
class CreativeSeed:
    """完整的创意种子组合"""

    opening: OpeningSeed
    emotion: EmotionSeed
    ending: EndingSeed
    seed_id: str  # 用于追踪和去重

    def to_prompt(self) -> str:
        """转换为完整的创意指导提示词"""
        return f"""
══════════════════════════════════════════════════════════════
【创意种子 - 强制差异化框架】种子ID: {self.seed_id}
══════════════════════════════════════════════════════════════

{self.opening.to_prompt()}

{self.emotion.to_prompt()}

{self.ending.to_prompt()}

══════════════════════════════════════════════════════════════
⚠️ 重要：以上三个维度是本次创作的强制框架，必须严格遵守！
这是确保文案差异化的关键，不要偏离这个框架。
══════════════════════════════════════════════════════════════
"""


class CreativeSeedBank:
    """创意种子库"""

    # 开头模式种子库
    OPENING_SEEDS: List[OpeningSeed] = [
        OpeningSeed(
            type=OpeningType.COUNTER_INTUITIVE,
            template="没想到这个xxx居然...",
            forbidden_patterns=["最近买了", "上周入手", "大家好", "hello", "作为一个"],
            description="用反常识或意外的角度开头，打破读者预期",
        ),
        OpeningSeed(
            type=OpeningType.SELF_MOCKERY,
            template="我承认我冲动了/说实话我一开始是拒绝的",
            forbidden_patterns=["大家好", "hello", "首先", "作为一个"],
            description="用自嘲或吐槽的方式开头，显得真实不做作",
        ),
        OpeningSeed(
            type=OpeningType.SUSPENSE,
            template="用了一个月，说句大实话/憋了很久想说",
            forbidden_patterns=["最近", "上周", "首先", "第一"],
            description="用悬念或时间积累开头，制造期待感",
        ),
        OpeningSeed(
            type=OpeningType.PAIN_POINT,
            template="凌晨三点还在xxx/每天xxx真的太xxx了",
            forbidden_patterns=["作为一个", "大家好", "最近"],
            description="用具体痛点场景开头，引发共鸣",
        ),
        OpeningSeed(
            type=OpeningType.CURIOSITY_GAP,
            template="xxx和xxx的区别，终于搞明白了/原来xxx和xxx差这么多",
            forbidden_patterns=["众所周知", "大家都知道", "首先"],
            description="用好奇缺口开头，让读者想知道答案",
        ),
        OpeningSeed(
            type=OpeningType.SCENE_ENTRY,
            template="那天朋友来家里xxx/周末在家xxx的时候",
            forbidden_patterns=["作为一个", "最近", "大家好"],
            description="用具体场景切入，画面感强",
        ),
        OpeningSeed(
            type=OpeningType.EMOTION_HOOK,
            template="说实话，一开始我是拒绝的/买之前纠结了很久",
            forbidden_patterns=["首先", "作为一个", "大家好"],
            description="用情绪状态开头，显得真实",
        ),
    ]

    # 情感基调种子库
    EMOTION_SEEDS: List[EmotionSeed] = [
        EmotionSeed(
            type=EmotionType.CASUAL_ROAST,
            tone_description="像朋友吐槽缺点，带点幽默，不严肃",
            example_phrases=["说实话", "其实吧", "反正", "可能就是"],
            avoid_phrases=["不仅而且", "由此可见", "综上所述", "值得一提的是"],
        ),
        EmotionSeed(
            type=EmotionType.SINCERE_SHARE,
            tone_description="认真说体验，不夸张，像真心推荐给朋友",
            example_phrases=["真的挺", "确实", "个人感觉", "我觉得"],
            avoid_phrases=["绝绝子", "YYDS", "闭眼入", "冲就完事"],
        ),
        EmotionSeed(
            type=EmotionType.HESITANT_WATCH,
            tone_description="买之前纠结了很久的心态，显得理性",
            example_phrases=[
                "犹豫了很久",
                "纠结了好久",
                "看了好多评价",
                "对比了好几款",
            ],
            avoid_phrases=["直接冲", "毫不犹豫", "一眼就"],
        ),
        EmotionSeed(
            type=EmotionType.SURPRISE_FIND,
            tone_description="意外发现比预期好，有惊喜感",
            example_phrases=["没想到", "超出预期", "比想象中", "意外的"],
            avoid_phrases=["果然", "不出所料", "和预期一样"],
        ),
        EmotionSeed(
            type=EmotionType.RATIONAL_COMPARE,
            tone_description="和同类产品对比的心态，显得专业",
            example_phrases=["对比了", "和xxx比", "之前用过", "相比之下"],
            avoid_phrases=["闭眼入", "无脑冲", "不用犹豫"],
        ),
        EmotionSeed(
            type=EmotionType.REGRET_RELIEF,
            tone_description="后悔没早买或释然没踩坑的心态",
            example_phrases=["早知道", "后悔没", "幸好没", "还好没"],
            avoid_phrases=["果断", "毫不犹豫", "直接"],
        ),
        EmotionSeed(
            type=EmotionType.INSIDER_TIP,
            tone_description="懂行人的专业视角，显得有经验",
            example_phrases=["作为用过", "玩过不少", "这个圈子里", "内行人都知道"],
            avoid_phrases=["小白也能", "新手友好", "零基础"],
        ),
    ]

    # 结尾模式种子库
    ENDING_SEEDS: List[EndingSeed] = [
        EndingSeed(
            type=EndingType.ASK_ADVICE,
            template="你们有啥好用的xxx推荐吗？",
            description="求建议式结尾，引发评论互动",
            forbidden_patterns=["记得点赞", "关注我", "评论区告诉我"],
        ),
        EndingSeed(
            type=EndingType.INVITE_DISCUSS,
            template="xxx和xxx你们选哪个？",
            description="邀请讨论式结尾，制造话题",
            forbidden_patterns=["记得点赞", "关注我", "求关注"],
        ),
        EndingSeed(
            type=EndingType.LEAVE_SUSPENSE,
            template="下一步准备试试xxx/下次试试xxx",
            description="留悬念式结尾，让人期待后续",
            forbidden_patterns=["记得点赞", "关注我", "评论区"],
        ),
        EndingSeed(
            type=EndingType.RESONANCE,
            template="用过的都懂那种感觉/懂的都懂",
            description="共鸣式结尾，建立认同感",
            forbidden_patterns=["记得点赞", "关注我", "求关注"],
        ),
        EndingSeed(
            type=EndingType.SUMMARY_FEELING,
            template="总的来说，xxx/反正我觉得xxx",
            description="总结感受式结尾，自然收尾",
            forbidden_patterns=["综上所述", "总而言之", "最后总结"],
        ),
        EndingSeed(
            type=EndingType.ACTION_HOOK,
            template="想入的可以冲了/趁着xxx赶紧",
            description="行动钩子式结尾，促成转化",
            forbidden_patterns=["记得点赞收藏", "关注我不迷路", "评论区扣"],
        ),
    ]

    @classmethod
    def get_random_seed(cls, exclude_ids: Optional[List[str]] = None) -> CreativeSeed:
        """
        获取随机创意种子组合

        Args:
            exclude_ids: 需要排除的种子ID列表（避免重复）

        Returns:
            CreativeSeed: 完整的创意种子组合
        """
        exclude_ids = exclude_ids or []

        # 随机选择三个维度
        opening = random.choice(cls.OPENING_SEEDS)
        emotion = random.choice(cls.EMOTION_SEEDS)
        ending = random.choice(cls.ENDING_SEEDS)

        # 生成种子ID
        seed_id = f"{opening.type.value[:2]}{emotion.type.value[:2]}{ending.type.value[:2]}_{random.randint(100, 999)}"

        # 如果在排除列表中，重新选择
        max_attempts = 10
        attempts = 0
        while seed_id in exclude_ids and attempts < max_attempts:
            opening = random.choice(cls.OPENING_SEEDS)
            emotion = random.choice(cls.EMOTION_SEEDS)
            ending = random.choice(cls.ENDING_SEEDS)
            seed_id = f"{opening.type.value[:2]}{emotion.type.value[:2]}{ending.type.value[:2]}_{random.randint(100, 999)}"
            attempts += 1

        return CreativeSeed(
            opening=opening, emotion=emotion, ending=ending, seed_id=seed_id
        )

    @classmethod
    def get_multiple_seeds(
        cls, count: int = 3, exclude_ids: Optional[List[str]] = None
    ) -> List[CreativeSeed]:
        """
        获取多个不同的创意种子组合

        Args:
            count: 需要的数量
            exclude_ids: 需要排除的种子ID列表

        Returns:
            List[CreativeSeed]: 多个不同的创意种子组合
        """
        exclude_ids = exclude_ids or []
        seeds = []
        used_ids = list(exclude_ids)

        for _ in range(count):
            seed = cls.get_random_seed(exclude_ids=used_ids)
            seeds.append(seed)
            used_ids.append(seed.seed_id)

        return seeds

    @classmethod
    def get_seed_by_id(cls, seed_id: str) -> Optional[CreativeSeed]:
        """
        根据种子ID获取创意种子（用于重试时切换）

        Args:
            seed_id: 种子ID

        Returns:
            CreativeSeed: 找到的种子，或None
        """
        # 解析种子ID格式："{opening[:2]}{emotion[:2]}{ending[:2]}_{random}"
        try:
            prefix = seed_id.split("_")[0]
            opening_prefix = prefix[:2]
            emotion_prefix = prefix[2:4]
            ending_prefix = prefix[4:6]

            # 匹配开头
            opening = next(
                (o for o in cls.OPENING_SEEDS if o.type.value[:2] == opening_prefix),
                None,
            )
            emotion = next(
                (e for e in cls.EMOTION_SEEDS if e.type.value[:2] == emotion_prefix),
                None,
            )
            ending = next(
                (en for en in cls.ENDING_SEEDS if en.type.value[:2] == ending_prefix),
                None,
            )

            if opening and emotion and ending:
                return CreativeSeed(
                    opening=opening, emotion=emotion, ending=ending, seed_id=seed_id
                )
        except Exception:
            pass

        return None

    @classmethod
    def get_different_seed(cls, current_seed_id: str) -> CreativeSeed:
        """
        获取与当前种子完全不同的新种子（用于重试）

        Args:
            current_seed_id: 当前种子ID

        Returns:
            CreativeSeed: 新的创意种子
        """
        current_seed = cls.get_seed_by_id(current_seed_id)
        if current_seed:
            # 排除当前种子的所有三个维度
            exclude_openings = [current_seed.opening.type]
            exclude_emotions = [current_seed.emotion.type]
            exclude_endings = [current_seed.ending.type]

            # 选择不同的开头
            available_openings = [
                o for o in cls.OPENING_SEEDS if o.type not in exclude_openings
            ]
            if not available_openings:
                available_openings = cls.OPENING_SEEDS

            # 选择不同的情感
            available_emotions = [
                e for e in cls.EMOTION_SEEDS if e.type not in exclude_emotions
            ]
            if not available_emotions:
                available_emotions = cls.EMOTION_SEEDS

            # 选择不同的结尾
            available_endings = [
                en for en in cls.ENDING_SEEDS if en.type not in exclude_endings
            ]
            if not available_endings:
                available_endings = cls.ENDING_SEEDS

            opening = random.choice(available_openings)
            emotion = random.choice(available_emotions)
            ending = random.choice(available_endings)

            seed_id = f"{opening.type.value[:2]}{emotion.type.value[:2]}{ending.type.value[:2]}_{random.randint(100, 999)}"

            return CreativeSeed(
                opening=opening, emotion=emotion, ending=ending, seed_id=seed_id
            )

        # 如果无法解析当前种子，返回随机新种子
        return cls.get_random_seed(exclude_ids=[current_seed_id])


# 便捷函数
def get_creative_seeds_for_generation(
    count: int = 3, used_seed_ids: Optional[List[str]] = None
) -> List[CreativeSeed]:
    """
    为文案生成获取创意种子

    Args:
        count: 需要的种子数量（默认3个用于并行生成）
        used_seed_ids: 已使用过的种子ID列表

    Returns:
        List[CreativeSeed]: 创意种子列表
    """
    return CreativeSeedBank.get_multiple_seeds(count=count, exclude_ids=used_seed_ids)


def get_next_creative_seed_for_retry(
    current_seed_id: str, used_seed_ids: Optional[List[str]] = None
) -> CreativeSeed:
    """
    为重试获取新的创意种子

    Args:
        current_seed_id: 当前失败的种子ID
        used_seed_ids: 已使用过的种子ID列表

    Returns:
        CreativeSeed: 新的创意种子
    """
    used_seed_ids = used_seed_ids or []
    all_exclude = list(set(used_seed_ids + [current_seed_id]))

    # 首先尝试获取完全不同的种子
    new_seed = CreativeSeedBank.get_different_seed(current_seed_id)

    # 如果新种子也在排除列表中，重新获取
    if new_seed.seed_id in all_exclude:
        new_seed = CreativeSeedBank.get_random_seed(exclude_ids=all_exclude)

    return new_seed


async def get_creative_seeds_for_generation_async(
    db,
    seed_type: str,
    category: Optional[str] = None,
    owner_operator_id: Optional[int] = None,
    count: int = 3,
    exclude_ids: Optional[List[int]] = None,
) -> List["CreativeSeedModel"]:
    """
    从数据库获取指定类型的创意种子列表

    Args:
        db: 数据库会话
        seed_type: 种子类型 (opening/emotion/ending)
        category: 品类过滤
        owner_operator_id: 创作管理员ID
        count: 需要的数量
        exclude_ids: 需要排除的种子ID列表

    Returns:
        List[CreativeSeedModel]: 创意种子模型列表
    """
    from sqlalchemy import and_, or_, select

    from app.models import CreativeSeed as CreativeSeedModel

    exclude_ids = exclude_ids or []

    conditions = [
        CreativeSeedModel.seed_type == seed_type,
        CreativeSeedModel.status == "enabled",
    ]

    # 权限过滤：用户自己的种子 + 系统种子
    if owner_operator_id:
        conditions.append(
            or_(
                CreativeSeedModel.owner_operator_id == owner_operator_id,
                CreativeSeedModel.is_system == True,
            )
        )

    # 品类过滤
    if category and category != "通用":
        conditions.append(
            or_(
                CreativeSeedModel.category == category,
                CreativeSeedModel.category == "通用",
                CreativeSeedModel.category == None,
            )
        )

    # 排除已使用的
    if exclude_ids:
        conditions.append(CreativeSeedModel.id.notin_(exclude_ids))

    query = select(CreativeSeedModel).where(and_(*conditions))
    result = await db.execute(query)
    seeds = list(result.scalars().all())

    # 如果数量不足，返回所有可用的
    if len(seeds) <= count:
        return seeds

    # 随机选择指定数量
    return random.sample(seeds, count)


async def get_creative_seeds_from_db(
    db,
    owner_operator_id: int,
    opening_seed_id: Optional[str] = None,
    emotion_seed_id: Optional[str] = None,
    ending_seed_id: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[CreativeSeed]:
    """
    从数据库获取创意种子组合

    Args:
        db: 数据库会话
        owner_operator_id: 创作管理员ID
        opening_seed_id: 指定的开头种子ID（'auto'或None表示随机）
        emotion_seed_id: 指定的情感种子ID（'auto'或None表示随机）
        ending_seed_id: 指定的结尾种子ID（'auto'或None表示随机）
        category: 品类过滤

    Returns:
        CreativeSeed: 完整的创意种子组合
    """
    import json

    from sqlalchemy import and_, or_, select

    from app.models import CreativeSeed as CreativeSeedModel

    def parse_seed_id(seed_id: Optional[str]) -> Optional[int]:
        """解析种子ID：'auto'或None返回None（随机），否则转为int"""
        if seed_id is None or seed_id == "auto":
            return None
        try:
            return int(seed_id)
        except (ValueError, TypeError):
            return None

    async def get_seed(seed_id: Optional[str], seed_type: str) -> Optional[Dict]:
        """获取单个种子"""
        # 解析seed_id：'auto'或None表示随机
        parsed_id = parse_seed_id(seed_id)
        if parsed_id:
            # 使用指定的种子ID查询
            result = await db.execute(
                select(CreativeSeedModel).where(CreativeSeedModel.id == parsed_id)
            )
            seed = result.scalar_one_or_none()
            if seed:
                return {
                    "id": seed.id,
                    "name": seed.name,
                    "template": seed.template,
                    "description": seed.description,
                    "forbidden_patterns": (
                        json.loads(seed.forbidden_patterns)
                        if seed.forbidden_patterns
                        else []
                    ),
                    "example_phrases": (
                        json.loads(seed.example_phrases) if seed.example_phrases else []
                    ),
                    "avoid_phrases": (
                        json.loads(seed.avoid_phrases) if seed.avoid_phrases else []
                    ),
                }
        else:
            # 随机选择
            conditions = [
                CreativeSeedModel.seed_type == seed_type,
                CreativeSeedModel.status == "enabled",
                or_(
                    CreativeSeedModel.owner_operator_id == owner_operator_id,
                    CreativeSeedModel.is_system == True,
                ),
            ]
            if category and category != "通用":
                conditions.append(
                    or_(
                        CreativeSeedModel.category == category,
                        CreativeSeedModel.category == "通用",
                    )
                )

            query = select(CreativeSeedModel).where(and_(*conditions))
            result = await db.execute(query)
            seeds = list(result.scalars().all())

            if seeds:
                seed = random.choice(seeds)
                return {
                    "id": seed.id,
                    "name": seed.name,
                    "template": seed.template,
                    "description": seed.description,
                    "forbidden_patterns": (
                        json.loads(seed.forbidden_patterns)
                        if seed.forbidden_patterns
                        else []
                    ),
                    "example_phrases": (
                        json.loads(seed.example_phrases) if seed.example_phrases else []
                    ),
                    "avoid_phrases": (
                        json.loads(seed.avoid_phrases) if seed.avoid_phrases else []
                    ),
                }
        return None

    # 获取三个维度的种子
    opening_data = await get_seed(opening_seed_id, "opening")
    emotion_data = await get_seed(emotion_seed_id, "emotion")
    ending_data = await get_seed(ending_seed_id, "ending")

    # 如果数据库中没有种子，使用硬编码的种子
    if not opening_data or not emotion_data or not ending_data:
        return CreativeSeedBank.get_random_seed()

    # 转换为CreativeSeed对象
    opening = OpeningSeed(
        type=OpeningType.COUNTER_INTUITIVE,  # 类型从名称推断
        template=opening_data["template"],
        forbidden_patterns=opening_data.get("forbidden_patterns", []),
        description=opening_data.get("description", ""),
    )

    emotion = EmotionSeed(
        type=EmotionType.CASUAL_ROAST,
        tone_description=emotion_data.get("description", ""),
        example_phrases=emotion_data.get("example_phrases", []),
        avoid_phrases=emotion_data.get("avoid_phrases", []),
    )

    ending = EndingSeed(
        type=EndingType.ASK_ADVICE,
        template=ending_data["template"],
        description=ending_data.get("description", ""),
        forbidden_patterns=ending_data.get("forbidden_patterns", []),
    )

    seed_id = f"db_{opening_data['id']}_{emotion_data['id']}_{ending_data['id']}"

    return CreativeSeed(
        opening=opening,
        emotion=emotion,
        ending=ending,
        seed_id=seed_id,
    )


def build_creative_seed_prompt(
    opening_template: str,
    opening_description: str,
    emotion_description: str,
    emotion_examples: List[str],
    ending_template: str,
    ending_description: str,
    product_selling_points: Optional[str] = None,
) -> str:
    """
    构建创意种子提示词

    Args:
        opening_template: 开头模板
        opening_description: 开头说明
        emotion_description: 情感描述
        emotion_examples: 情感示例
        ending_template: 结尾模板
        ending_description: 结尾说明
        product_selling_points: 产品卖点

    Returns:
        str: 创意种子提示词
    """
    prompt_parts = [
        "══════════════════════════════════════════════════════════════",
        "【创意种子 - 差异化框架】",
        "══════════════════════════════════════════════════════════════",
        "",
        "【开头模式】",
        f"示例风格：{opening_template}",
        f"创作要求：{opening_description}",
        "",
        "【情感基调】",
        f"基调要求：{emotion_description}",
        f"典型表达：{', '.join(emotion_examples[:3]) if emotion_examples else '自然真实'}",
        "",
        "【结尾模式】",
        f"示例风格：{ending_template}",
        f"创作要求：{ending_description}",
    ]

    if product_selling_points:
        prompt_parts.extend(
            [
                "",
                "【产品卖点】",
                product_selling_points,
            ]
        )

    prompt_parts.extend(
        [
            "",
            "══════════════════════════════════════════════════════════════",
            "⚠️ 重要：以上维度是本次创作的强制框架，必须严格遵守！",
            "══════════════════════════════════════════════════════════════",
        ]
    )

    return "\n".join(prompt_parts)
