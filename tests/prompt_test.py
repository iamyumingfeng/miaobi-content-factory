#!/usr/bin/env python3
"""
提示词优化效果测试脚本
使用 Playwright 模拟用户操作
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("请先安装 playwright: pip install playwright")
    print("然后运行: playwright install chromium")
    exit(1)

# 测试配置
TEST_CONFIG = {
    "base_url": "http://localhost",
    "login_url": "/login",
    "username": "O_OvUQvegVpXAmJOTi",
    "password": "12345678",
    "output_dir": Path("test_outputs")
}

# 测试数据
TEST_MATERIALS = [
    {
        "id": 1,
        "name": "粉底液种草测试",
        "content_type": "图文",
        "benchmark_info": """标题：油皮亲妈！这款粉底液我用空3瓶了
正文：夏天油皮真的太难了，之前用的粉底液到中午就脱妆脱得没法看，T区油光满面，脸颊又拔干……""",
        "material_info": """产品名称：清透持妆粉底液
功效：控油、持妆、遮瑕
适合肤质：油皮、混油皮
特点：12小时不脱妆、不暗沉、不闷痘""",
        "template_instruction": "创作一篇油皮粉底液种草文案，要真实、有细节、有痛点、有解决方案"
    },
    {
        "id": 2,
        "name": "口红推荐测试",
        "content_type": "图文",
        "benchmark_info": """标题：黄皮姐妹真的可以试试这个颜色！
正文：之前一直不敢尝试橘调口红，怕显黑怕土气，直到遇到这支……""",
        "material_info": """产品名称：丝绒雾面唇膏
色号：暖棕橘
质地：丝绒雾面，不拔干
适合肤色：黄皮显白、不挑皮""",
        "template_instruction": "创作一篇黄皮口红推荐文案，强调显白、不挑皮、日常可用"
    }
]


class PromptTester:
    """提示词测试器"""

    def __init__(self):
        self.output_dir = TEST_CONFIG["output_dir"]
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    async def login(self, page: Page):
        """登录系统"""
        print("🔐 正在登录...")
        await page.goto(TEST_CONFIG["base_url"] + TEST_CONFIG["login_url"])
        await page.wait_for_timeout(1000)

        # 输入用户名
        await page.fill('input[placeholder="请输入用户名"]', TEST_CONFIG["username"])
        await page.wait_for_timeout(300)

        # 输入密码
        await page.fill('input[placeholder="请输入密码"]', TEST_CONFIG["password"])
        await page.wait_for_timeout(300)

        # 点击登录按钮
        await page.click('button:has-text("登录")')
        print("✅ 登录请求已发送")

        # 等待跳转或停留
        await page.wait_for_timeout(3000)

        current_url = page.url
        print(f"🌐 当前页面: {current_url}")

        if "dashboard" in current_url:
            print("✅ 登录成功！")
            return True
        else:
            print("⚠️  可能需要手动完成登录")
            print("💡 提示：如果看到登录页面，请手动登录后按回车继续...")
            input()
            return True

    async def check_prompt_templates(self, page: Page):
        """检查提示词模板"""
        print("\n📝 检查提示词模板...")

        # 尝试导航到提示词模板页面
        await page.goto(TEST_CONFIG["base_url"] + "/prompt-templates")
        await page.wait_for_timeout(2000)

        current_url = page.url
        print(f"🌐 当前页面: {current_url}")

        if "prompt-templates" not in current_url:
            print("💡 提示：请手动导航到提示词模板管理页面")
            print("💡 查看V2.0模板是否已设置为默认，然后按回车继续...")
            input()

        await page.wait_for_timeout(1000)

        # 截图保存
        screenshot_path = self.output_dir / f"prompt_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"📸 模板页面截图已保存: {screenshot_path}")

    async def test_generation_flow(self, page: Page, material: Dict):
        """测试生成流程"""
        print(f"\n{'='*60}")
        print(f"🧪 测试: {material['name']}")
        print('='*60)

        # 导航到内容生成页面
        await page.goto(TEST_CONFIG["base_url"] + "/generation/create")
        await page.wait_for_timeout(2000)

        print("💡 提示：现在请在浏览器中手动完成以下操作:")
        print(f"  1. 选择或输入素材信息")
        print(f"  2. 选择模板和创作者")
        print(f"  3. 提交生成任务")
        print(f"  4. 等待生成完成")
        print(f"  5. 查看生成的文案和图片质量")
        print("\n完成后按回车继续...")
        input()

        # 截图保存
        screenshot_path = self.output_dir / f"result_{material['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"📸 结果截图已保存: {screenshot_path}")

        # 记录评分
        result = {
            "material_id": material["id"],
            "material_name": material["name"],
            "screenshot": str(screenshot_path),
            "timestamp": datetime.now().isoformat(),
            "scores": {}
        }

        print("\n📊 现在请进行评分:")
        print("="*40)
        print("真人感 (0-30): ", end="")
        result["scores"]["realness"] = int(input() or "0")

        print("种草力 (0-25): ", end="")
        result["scores"]["desirability"] = int(input() or "0")

        print("主题聚焦度 (0-20): ", end="")
        result["scores"]["focus"] = int(input() or "0")

        print("通顺度 (0-15): ", end="")
        result["scores"]["readability"] = int(input() or "0")

        print("平台适配度 (0-10): ", end="")
        result["scores"]["platform_fit"] = int(input() or "0")

        total = sum(result["scores"].values())
        print(f"✅ 总分: {total}")
        result["scores"]["total"] = total

        print("\n💬 其他评价/建议 (可选): ", end="")
        result["notes"] = input()

        self.results.append(result)
        return result

    async def run(self):
        """运行完整测试"""
        print("🚀 AIGC 提示词优化效果测试")
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 目标: {TEST_CONFIG['base_url']}")

        async with async_playwright() as p:
            print("\n🔧 启动浏览器...")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1440, 'height': 900})
            page = await context.new_page()

            try:
                # 登录
                await self.login(page)

                # 检查模板
                await self.check_prompt_templates(page)

                # 逐个测试
                for material in TEST_MATERIALS:
                    await self.test_generation_flow(page, material)

                    if material != TEST_MATERIALS[-1]:
                        print("\n继续下一个测试？(回车继续, n退出): ", end="")
                        choice = input().strip().lower()
                        if choice == 'n':
                            break

                # 生成报告
                self.generate_report()

            finally:
                await browser.close()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 生成测试报告...")
        print("="*60)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_json = self.output_dir / f"report_{timestamp}.json"
        report_md = self.output_dir / f"report_{timestamp}.md"

        with open(report_json, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "config": TEST_CONFIG,
                "materials": TEST_MATERIALS,
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON报告: {report_json}")

        md_content = f"# AIGC 提示词优化效果测试报告\n\n"
        md_content += f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        md_content += "## 测试概览\n\n"
        md_content += f"- 测试素材数量: {len(TEST_MATERIALS)}\n"
        md_content += f"- 完成测试数量: {len(self.results)}\n\n"

        if self.results:
            md_content += "## 评分详情\n\n"
            md_content += "| 测试项 | 真人感 | 种草力 | 主题聚焦度 | 通顺度 | 平台适配度 | 总分 |\n"
            md_content += "|--------|--------|--------|------------|--------|------------|------|\n"

            avg_total = 0
            for r in self.results:
                s = r["scores"]
                avg_total += s["total"]
                md_content += f"| {r['material_name']} | {s['realness']} | {s['desirability']} | {s['focus']} | {s['readability']} | {s['platform_fit']} | {s['total']} |\n"

            avg_total = avg_total / len(self.results) if self.results else 0
            md_content += f"\n**平均总分**: {avg_total:.1f}/100\n\n"

            md_content += "## 详细评价\n\n"
            for r in self.results:
                md_content += f"### {r['material_name']}\n\n"
                md_content += f"- 时间: {r['timestamp']}\n"
                md_content += f"- 截图: {r['screenshot']}\n"
                if r.get("notes"):
                    md_content += f"- 评价: {r['notes']}\n"
                md_content += "\n"

        md_content += "\n## 总结\n\n"
        md_content += "请在此处添加测试总结和后续优化建议...\n"

        with open(report_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"📄 Markdown报告: {report_md}")

        print("\n✅ 测试完成！")


def print_intro():
    """打印介绍信息"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    AIGC 提示词优化测试工具                      ║
╠═══════════════════════════════════════════════════════════════╣
║  这个工具会帮助你测试V2.0提示词模板的效果，包含以下功能：       ║
║                                                               ║
║  1. 自动登录系统（如果失败会让你手动操作）                     ║
║  2. 检查提示词模板页面                                        ║
║  3. 引导你完成内容生成和评分过程                               ║
║  4. 自动保存截图和测试报告                                    ║
║                                                               ║
║  评分标准：                                                  ║
║  - 真人感：0-30分 (越接近真人越好)                           ║
║  - 种草力：0-25分 (越让人想买越好)                           ║
║  - 主题聚焦度：0-20分 (不跑题、讲清楚核心卖点)               ║
║  - 通顺度：0-15分 (读起来自然、流畅)                         ║
║  - 平台适配度：0-10分 (符合小红书风格和规范)                  ║
║                                                               ║
║  准备好了吗？按回车开始！                                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    input()


async def main():
    print_intro()

    tester = PromptTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
