#!/usr/bin/env python3
"""
提示词优化效果自动化测试
使用 Playwright 模拟用户操作，测试生成的内容质量
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请先安装 playwright: pip install playwright")
    print("然后运行: playwright install chromium")
    exit(1)

# 测试配置
TEST_CONFIG = {
    "base_url": "http://localhost:3000",  # 前端地址
    "login_url": "/login",
    "username": "O_OvUQvegVpXAmJOTi",
    "password": "12345678",
    "output_dir": Path("test_outputs")
}

# 测试数据 - 模拟素材
TEST_MATERIALS = [
    {
        "name": "粉底液测试",
        "content_type": "图文",
        "benchmark_info": "标题：油皮亲妈！这款粉底液我用空3瓶了\n正文：夏天油皮真的太难了，之前用的粉底液到中午就脱妆脱得没法看...",
        "material_info": "产品名称：清透持妆粉底液\n功效：控油、持妆、遮瑕\n适合肤质：油皮、混油皮",
        "template_instruction": "创作一篇油皮粉底液种草文案，要真实、有细节"
    },
    {
        "name": "口红测试",
        "content_type": "图文",
        "benchmark_info": "标题：黄皮姐妹真的可以试试这个颜色！\n正文：之前一直不敢尝试橘调口红，怕显黑...",
        "material_info": "产品名称：丝绒雾面唇膏\n色号：暖棕橘\n质地：雾面不拔干",
        "template_instruction": "创作一篇黄皮口红推荐文案"
    }
]


class PromptTester:
    """提示词测试器"""

    def __init__(self):
        self.output_dir = TEST_CONFIG["output_dir"]
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = []

    async def run_test(self):
        """运行完整测试"""
        print("🚀 开始提示词优化效果测试...")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # 有头模式，方便观察
            page = await browser.new_page()

            try:
                # 1. 登录
                await self.login(page)

                # 2. 测试每一个素材
                for i, material in enumerate(TEST_MATERIALS, 1):
                    print(f"\n{'='*60}")
                    print(f"测试 {i}/{len(TEST_MATERIALS)}: {material['name']}")
                    print('='*60)

                    result = await self.test_single_material(page, material)
                    self.test_results.append(result)

                # 3. 生成报告
                self.generate_report()

            finally:
                await browser.close()

    async def login(self, page):
        """登录系统"""
        print("📱 正在登录...")
        await page.goto(TEST_CONFIG["base_url"] + TEST_CONFIG["login_url"])

        # 等待页面加载
        await page.wait_for_timeout(1000)

        # 填写用户名密码 (这里根据实际前端调整)
        # 实际使用时需要根据你的前端页面选择器调整
        print("⚠️  请手动完成登录，按回车继续...")
        input()

        print("✅ 登录完成！")

    async def test_single_material(self, page, material: Dict) -> Dict:
        """测试单个素材"""
        result = {
            "name": material["name"],
            "generated_contents": [],
            "scores": []
        }

        print(f"📝 测试素材: {material['name']}")

        # 这里需要根据实际的前端页面流程进行调整
        # 简单演示：保存测试数据到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"test_{timestamp}_{material['name']}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "material": material,
                "test_time": datetime.now().isoformat(),
                "status": "manual_test_required"
            }, f, ensure_ascii=False, indent=2)

        print(f"💾 测试数据已保存: {output_file}")
        print("📋 请手动进行测试，然后填写评分...")

        # 等待用户手动测试和评分
        print("\n请完成以下步骤:")
        print("1. 使用系统生成内容")
        print("2. 观察生成质量")
        print("3. 使用评分表进行评分")
        print()
        input("按回车继续下一个测试...")

        return result

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"test_report_{timestamp}.md"

        report_content = f"""# 提示词优化效果测试报告

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试概览

- 测试素材数量: {len(TEST_MATERIALS)}
- 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试素材列表

"""

        for i, material in enumerate(TEST_MATERIALS, 1):
            report_content += f"\n### {i}. {material['name']}\n"
            report_content += f"- 内容类型: {material['content_type']}\n"
            report_content += f"- 状态: ⏳ 需要人工评分\n"

        report_content += f"""
## 评分记录

（此处粘贴人工评分结果）

## 总结与建议

（此处填写测试总结和优化建议）

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"📄 测试报告已生成: {report_file}")
        print("\n请继续完成人工评分，并填写到报告中！")


def print_scoring_guide():
    """打印评分指南"""
    print("""
📋 评分指南
==========

真人感 (0-30分):
- 25-30: 完全像真人写的
- 18-24: 比较像真人
- 10-17: 一半像AI
- 0-9: 明显是AI

种草力 (0-25分):
- 20-25: 看完立刻想下单
- 13-19: 有点兴趣
- 6-12: 一般般
- 0-5: 完全不想买

主题聚焦度 (0-20分):
- 16-20: 完全聚焦
- 11-15: 基本聚焦
- 6-10: 有点散
- 0-5: 完全不知道在讲什么

通顺度 (0-15分):
- 12-15: 非常通顺
- 8-11: 基本通顺
- 4-7: 不太通顺
- 0-3: 不通顺

平台适配度 (0-10分):
- 8-10: 完美符合
- 5-7: 基本符合
- 2-4: 不太符合
- 0-1: 完全不符合
""")


async def main():
    """主函数"""
    print_scoring_guide()

    tester = PromptTester()
    await tester.run_test()


if __name__ == "__main__":
    asyncio.run(main())
