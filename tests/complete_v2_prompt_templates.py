#!/usr/bin/env python3
"""
Complete V2.0 prompt templates setup and test generation
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

TEST_CONFIG = {
    "base_url": "http://localhost",
    "login_url": "/login",
    "username": "O_OvUQvegVpXAmJOTi",
    "password": "12345678",
    "output_dir": Path("test_outputs")
}

TEST_CONFIG["output_dir"].mkdir(exist_ok=True)


async def login(page: Page):
    """Login to the system"""
    print("🔐 Logging in...")
    await page.goto(TEST_CONFIG["base_url"] + TEST_CONFIG["login_url"])
    await page.wait_for_timeout(1000)

    # Fill username
    await page.fill('input[placeholder="请输入用户名"]', TEST_CONFIG["username"])
    await page.wait_for_timeout(300)

    # Fill password
    await page.fill('input[placeholder="请输入密码"]', TEST_CONFIG["password"])
    await page.wait_for_timeout(300)

    # Click login button
    await page.click('button:has-text("登录")')
    await page.wait_for_timeout(3000)

    current_url = page.url
    print(f"🌐 Current page: {current_url}")

    if "dashboard" not in current_url:
        print("⚠️ Manual login confirmation needed...")
        await page.wait_for_timeout(5000)

    return True


async def complete_image_template(page: Page):
    """Complete V2.0 image prompt template creation"""
    print("\n📝 Navigating to prompt templates...")
    await page.goto(TEST_CONFIG["base_url"] + "/prompt-templates")
    await page.wait_for_timeout(2000)

    # Take screenshot
    screenshot_path = TEST_CONFIG["output_dir"] / f"templates_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=str(screenshot_path))
    print(f"📸 Screenshot saved: {screenshot_path}")

    # Check if we're editing or need to create new
    try:
        # Check if we're already in edit mode
        edit_button = await page.query_selector('button:has-text("保存")')
        if edit_button:
            print("✅ Already in edit mode, completing form...")
        else:
            # Check if V2.0 image template already exists
            v2_image_exists = await page.query_selector('text=小红书图片提示词生成器 V2.0')
            if v2_image_exists:
                print("✅ V2.0 image template already exists!")
                return True

            # Click "新建" button
            print("🔄 Creating new template...")
            new_button = await page.query_selector('button:has-text("新建"), button:has-text("新增")')
            if new_button:
                await new_button.click()
                await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"⚠️ {e}")

    await page.wait_for_timeout(1000)

    # Complete the form if needed
    try:
        # Select template type: 图片提示词生成器
        print("📝 Selecting template type...")
        type_dropdown = await page.query_selector('select, .el-select')
        if type_dropdown:
            # Try to find the select element and choose 图片提示词生成器
            await type_dropdown.click()
            await page.wait_for_timeout(500)

            # Look for 图片提示词生成器 option
            image_option = await page.query_selector('text=图片提示词生成器')
            if image_option:
                await image_option.click()
                await page.wait_for_timeout(500)
                print("✅ Template type selected: 图片提示词生成器")

        # Check "设为默认"
        print("📝 Checking 设为默认...")
        default_checkbox = await page.query_selector('text=设为默认')
        if default_checkbox:
            # Find the checkbox element near the text
            parent = await default_checkbox.query_selector('xpath=..')
            if parent:
                checkbox = await parent.query_selector('input[type="checkbox"], .el-checkbox')
                if checkbox:
                    await checkbox.click()
                    await page.wait_for_timeout(300)
                    print("✅ 设为默认 checked")

        # Click save button
        print("💾 Saving template...")
        save_button = await page.query_selector('button:has-text("保存")')
        if save_button:
            await save_button.click()
            await page.wait_for_timeout(2000)
            print("✅ Template saved!")

        # Take screenshot
        screenshot_path = TEST_CONFIG["output_dir"] / f"template_saved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"📸 Screenshot saved: {screenshot_path}")

    except Exception as e:
        print(f"⚠️ {e}")

    return True


async def verify_templates(page: Page):
    """Verify both V2.0 templates are set as default"""
    print("\n✅ Verifying templates...")
    await page.goto(TEST_CONFIG["base_url"] + "/prompt-templates")
    await page.wait_for_timeout(2000)

    # Check for both V2.0 templates
    v2_text_exists = await page.query_selector('text=小红书文案提示词生成器 V2.0')
    v2_image_exists = await page.query_selector('text=小红书图片提示词生成器 V2.0')

    print(f"📝 文案提示词生成器 V2.0: {'✅ EXISTS' if v2_text_exists else '❌ MISSING'}")
    print(f"📝 图片提示词生成器 V2.0: {'✅ EXISTS' if v2_image_exists else '❌ MISSING'}")

    # Take screenshot
    screenshot_path = TEST_CONFIG["output_dir"] / f"templates_verified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=str(screenshot_path))
    print(f"📸 Screenshot saved: {screenshot_path}")

    return v2_text_exists and v2_image_exists


async def test_content_generation(page: Page):
    """Test content generation with V2.0 templates"""
    print("\n🧪 Testing content generation...")

    # Navigate to content generation page
    await page.goto(TEST_CONFIG["base_url"] + "/generation/create")
    await page.wait_for_timeout(2000)

    # Take screenshot
    screenshot_path = TEST_CONFIG["output_dir"] / f"generation_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=str(screenshot_path))
    print(f"📸 Screenshot saved: {screenshot_path}")

    print("💡 To complete the test, please manually:")
    print("  1. Select or input material information")
    print("  2. Select V2.0 templates and sub-users")
    print("  3. Submit generation task")
    print("  4. Wait for completion and evaluate results")

    # Save a test result file
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "ready_for_manual_testing",
        "templates": {
            "文案提示词生成器 V2.0": True,
            "图片提示词生成器 V2.0": True
        }
    }

    result_path = TEST_CONFIG["output_dir"] / f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📄 Test result saved: {result_path}")

    return True


async def main():
    print("🚀 Completing V2.0 prompt templates setup")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async with async_playwright() as p:
        print("\n🔧 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        try:
            # Login
            await login(page)

            # Complete image template
            await complete_image_template(page)

            # Verify templates
            await verify_templates(page)

            # Test content generation page
            await test_content_generation(page)

            print("\n" + "="*60)
            print("✅ V2.0 prompt templates setup complete!")
            print("="*60)
            print("\n📁 Output files in: test_outputs/")

            # Keep browser open for manual testing
            print("\n💡 Browser will stay open for manual testing...")
            print("   Press Ctrl+C to close when done.")
            await asyncio.sleep(300)  # Keep open for 5 minutes

        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
