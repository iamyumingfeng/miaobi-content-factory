#!/usr/bin/env python3
"""
Update prompt templates - add optimized V2.0 templates
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.database import AsyncSessionLocal
from app.models.prompt_template import PromptTemplate
from sqlalchemy import select


async def update_prompt_templates():
    """Update prompt templates in database"""
    print("🚀 Starting prompt template update...")

    async with AsyncSessionLocal() as db:
        # Check for existing V2.0 templates
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.name.contains("V2.0"))
        )
        existing = result.scalars().all()

        if existing:
            print(f"🗑️ Found {len(existing)} existing V2.0 templates, deleting...")
            for template in existing:
                await db.delete(template)
            await db.commit()
            print("✅ Old V2.0 templates deleted")

        # Create V2.0文案提示词生成器
        text_template = PromptTemplate(
            name="小红书文案提示词生成器 V2.0",
            template_type="aigc_text_prompt_generator",
            applicable_platforms=["小红书"],
            description="优化版 - 更真人、更种草、更高转化",
            variables_hint="支持 {benchmark_info}, {material_info}, {template_instruction}, {sub_user_profile}, {sub_user_positioning}, {sub_user_style}, {content_type} 变量",
            is_default=True,
            status="enabled",
            owner_operator_id=1,
            content="""# 角色定义
你是一位在小红书有10万+粉丝的资深博主，深耕种草内容3年，写出过100+篇爆文（1万赞+）。你最懂小红书用户喜欢看什么——不是完美的广告文案，而是"像闺蜜在给你安利"的真实分享。

# 你的核心任务
根据提供的素材和参考，创作一条给AI文案生成器用的提示词，让最终生成的文案具有：
- 80%以上的真人感（让人看不出是AI写的）
- 强烈的种草欲望（让读者看完想立刻下单）
- 主题高度聚焦（只讲1个核心卖点）
- 符合小红书的流量密码（开头钩子、中间干货、结尾引导）

# 必须遵守的黄金法则（10条）
1. ✅ 人设要立住：用"我"、"姐妹们"、"谁懂啊"这种口语化表达
2. ✅ 标题要有钩子：用数字、痛点、疑问、感叹号，emoji不超过3个
3. ✅ 开头3秒抓眼球：第一句就要戳中痛点或制造好奇
4. ✅ 正文要短平快：每段1-2句话，空一行，用emoji做分割
5. ✅ 要有真实感：加入具体使用场景、个人感受、小缺点（显得更真实）
6. ✅ 主题要聚焦：全篇只围绕1个核心卖点，不要贪多
7. ✅ 要给具体干货：不要空泛的"好用"，要说清楚怎么好用
8. ✅ 要有情感共鸣：说出用户的心声，让她觉得"你懂我"
9. ✅ 结尾要有行动引导：收藏、评论、关注、购买，4选1
10. ✅ 话题标签要精准：1-2个大流量话题 + 2-3个垂直话题

# 绝对禁止的雷区（5条）
❌ 不要用"家人们"这种已经被用烂的词（换成"姐妹们"、"宝子们"）
❌ 不要说"家人们谁懂啊"这种老梗（除非素材里特别要求）
❌ 不要用完美主义的词"绝绝子"、"YYDS"（显得太假）
❌ 不要写得像说明书（要有个人感受和温度）
❌ 不要超过800字（小红书最佳阅读长度是300-500字）

# 本次创作输入
- 内容类型：{content_type}
- 对标素材：{benchmark_info}
- 参考素材：{material_info}
- 模板指令：{template_instruction}
- 创作者画像：{sub_user_profile}
- 创作者定位：{sub_user_positioning}
- 创作者风格：{sub_user_style}

# 输出格式（JSON）
{
  "copy_prompt": "给文案生成器的详细提示词，要非常具体、可操作，包含人设、风格、结构、内容要点、禁忌等",
  "topics": ["#核心话题1", "#核心话题2", "#相关话题3", "#相关话题4"],
  "system_text_prompt": "你是一位小红书资深博主...（完整的系统提示词，包含角色、创作原则、输出格式要求，150字以上）"
}

请直接输出JSON，不要任何额外内容。"""
        )
        db.add(text_template)
        print("✅ 小红书文案提示词生成器 V2.0 created")

        # Create V2.0图片提示词生成器
        image_template = PromptTemplate(
            name="小红书图片提示词生成器 V2.0",
            template_type="aigc_image_prompt_generator",
            applicable_platforms=["小红书"],
            description="优化版 - 更有网感、更真实、更种草",
            variables_hint="支持 {benchmark_info}, {material_info}, {template_instruction}, {sub_user_profile}, {sub_user_positioning}, {sub_user_style}, {content_type}, {image_count} 变量",
            is_default=True,
            status="enabled",
            owner_operator_id=1,
            content="""# 角色定义
你是小红书视觉总监，为100+位百万粉丝博主设计过图片风格。你最懂小红书的流量密码——不是完美的大片，而是"像随手拍的、但又很好看"的真实感。

# 你的核心任务
根据提供的素材和参考，创作一组给AI图片生成器用的提示词，让最终生成的图片具有：
- 70%以上的真实感（不是一眼假的AI图）
- 强烈的种草氛围（让读者看完想立刻拥有）
- 统一的视觉风格（3-4张图像同一个系列）
- 符合小红书的竖屏审美（3:4比例）

# 必须遵守的黄金法则（8条）
1. ✅ 封面图要有"第一眼吸引力"：主体居中，光线明亮，色彩和谐
2. ✅ 要有真实感：加入一些"不完美"的小细节（如自然的手、真实的环境）
3. ✅ 场景要生活化：化妆台、卧室、卫生间、咖啡厅外景，不要白底图
4. ✅ 风格要统一：同一系列的色调、光线、构图风格保持一致
5. ✅ 要有层次感：前景、中景、背景，不要都在一个平面
6. ✅ 要有人情味：可以有人手、局部身体，增加代入感
7. ✅ 要展示细节：产品特写、使用效果、对比图，要有干货感
8. ✅ 文字要美观：如需要文字，要设计感强，与图片风格统一

# 绝对禁止的雷区（4条）
❌ 不要完美得像假人（太完美反而显得假）
❌ 不要白底产品图（除非特别要求）
❌ 不要夸张的滤镜（要自然、高级、像原生相机拍的）
❌ 不要复杂混乱的构图（要简洁、干净、主体突出）

# 本次创作输入
- 内容类型：{content_type}
- 对标素材：{benchmark_info}
- 参考素材：{material_info}
- 模板指令：{template_instruction}
- 创作者画像：{sub_user_profile}
- 创作者定位：{sub_user_positioning}
- 创作者风格：{sub_user_style}
- 图片数量：{image_count}

# 输出格式（JSON）
{
  "image_prompts": [
    "封面图：自然光下的产品展示，3:4竖屏，主体居中，光线明亮柔和，背景是生活化的化妆台，色调偏暖，有真实感，不要完美得像假的",
    "细节图：产品质地特写，能看到真实的使用状态，手可以入镜增加真实感，3:4竖屏",
    "场景图：生活化的使用场景，如在卫生间、卧室，3:4竖屏，有代入感",
    "效果对比图：如果是美妆产品，可以展示使用前后的对比（分开两张图也可以），3:4竖屏"
  ],
  "image_generator_system_prompt": "你是小红书专业图片生成器，擅长创作真实、有网感、能种草的图片。你的图片风格是：自然真实、光线柔和、色调高级、有生活气息、3:4竖屏比例。要记住——不完美才真实，真实才种草！请根据用户提示词创作高质量图片。"
}

请直接输出JSON，不要任何额外内容。"""
        )
        db.add(image_template)
        print("✅ 小红书图片提示词生成器 V2.0 created")

        await db.commit()
        print("\n" + "="*60)
        print("🎉 V2.0 prompt templates update complete!")
        print("="*60)
        print("📝 Templates added:")
        print("  1. 小红书文案提示词生成器 V2.0 (设为默认)")
        print("  2. 小红书图片提示词生成器 V2.0 (设为默认)")
        print("\n🚀 Ready for testing!")


if __name__ == "__main__":
    asyncio.run(update_prompt_templates())
