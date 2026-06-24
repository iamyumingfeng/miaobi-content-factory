import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { SettingsPage } from '../pages/SettingsPage';

// 测试配置
const TEST_CONFIG = {
  superAdminUsername: 'admin',
  superAdminPassword: 'admin123',
  operatorUsername: 'O_OvUQvegVpXAmJOTi',
  operatorPassword: '12345678'
};

// 获取最后打开的下拉框中的选项
function getDropdownOptions(page: any) {
  return page.locator('.el-select-dropdown').last().locator('.el-select-dropdown__item');
}

test.describe('用户默认模型设置 - 超级管理员', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    // 先登录
    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.superAdminUsername, TEST_CONFIG.superAdminPassword);

    // 导航到设置页面并点击模型平台配置
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('应该能够显示用户默认模型选择器', async () => {
    await settingsPage.expectModelPanelVisible();
    await expect(settingsPage.defaultTextModelSelect).toBeVisible();
    await expect(settingsPage.defaultImageModelSelect).toBeVisible();
    await expect(settingsPage.defaultVideoModelSelect).toBeVisible();
  });

  test('默认应该显示"自动选择"选项', async () => {
    await settingsPage.defaultTextModelSelect.click();
    const options = getDropdownOptions(settingsPage.page);
    const autoOption = options.filter({ hasText: '自动选择' }).first();
    await autoOption.waitFor({ state: 'attached' });
    await expect(autoOption).toHaveCount(1);
  });

  test('应该能够选择文本模型作为默认', async () => {
    await settingsPage.defaultTextModelSelect.click();
    const options = getDropdownOptions(settingsPage.page);
    const count = await options.count();
    if (count > 1) {
      await options.nth(1).click();
      await settingsPage.page.waitForTimeout(500);
      await expect(settingsPage.page.locator('.el-message--success')).toBeVisible();
    }
  });

  test('应该能够选择"自动选择"作为默认', async () => {
    await settingsPage.defaultTextModelSelect.click();
    const options = getDropdownOptions(settingsPage.page);
    const count = await options.count();
    if (count > 1) {
      await options.nth(1).click();
      await settingsPage.page.waitForTimeout(500);

      await settingsPage.defaultTextModelSelect.click();
      const autoOption = getDropdownOptions(settingsPage.page).filter({ hasText: '自动选择' }).first();
      await autoOption.click();
      await settingsPage.page.waitForTimeout(500);
      await expect(settingsPage.page.locator('.el-message--success')).toBeVisible();
    }
  });
});

test.describe('用户默认模型设置 - 创作管理员', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.operatorUsername, TEST_CONFIG.operatorPassword);

    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('创作管理员应该能够看到默认模型设置', async () => {
    await settingsPage.expectModelPanelVisible();
    await expect(settingsPage.defaultTextModelSelect).toBeVisible();
    await expect(settingsPage.defaultImageModelSelect).toBeVisible();
    await expect(settingsPage.defaultVideoModelSelect).toBeVisible();
  });

  test('创作管理员不应该看到平台标签页（因为只有超级管理员可以管理模型）', async () => {
    await settingsPage.expectModelPanelVisible();
    const platformTabs = settingsPage.page.locator('.platform-tabs');
    try {
      await expect(platformTabs).not.toBeVisible({ timeout: 3000 });
    } catch {
      const isHidden = await platformTabs.count() === 0 || await platformTabs.isHidden();
      expect(isHidden).toBeTruthy();
    }
  });

  test('创作管理员应该能够选择自己的默认模型', async () => {
    await settingsPage.defaultImageModelSelect.click();
    const options = getDropdownOptions(settingsPage.page);
    const count = await options.count();
    if (count > 1) {
      await options.nth(1).click();
      await settingsPage.page.waitForTimeout(500);
      await expect(settingsPage.page.locator('.el-message--success')).toBeVisible();
    }
  });
});

test.describe('用户默认模型设置 - 隔离性测试', () => {
  test('两个不同的管理员应该有各自独立的默认模型设置', async ({ browser }) => {
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    const loginPage1 = new LoginPage(page1);
    const settingsPage1 = new SettingsPage(page1);

    await loginPage1.goto();
    await loginPage1.loginWithPassword(TEST_CONFIG.superAdminUsername, TEST_CONFIG.superAdminPassword);
    await settingsPage1.goto();
    await settingsPage1.clickModelMenu();

    await settingsPage1.defaultTextModelSelect.click();
    const options1 = getDropdownOptions(page1);
    const count1 = await options1.count();
    let superAdminSelection = 'auto';

    if (count1 > 1) {
      await options1.nth(1).click();
      await page1.waitForTimeout(500);
      const selectedText = await settingsPage1.defaultTextModelSelect.textContent();
      superAdminSelection = selectedText || 'auto';
    }

    await context1.close();

    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    const loginPage2 = new LoginPage(page2);
    const settingsPage2 = new SettingsPage(page2);

    await loginPage2.goto();
    await loginPage2.loginWithPassword(TEST_CONFIG.operatorUsername, TEST_CONFIG.operatorPassword);
    await settingsPage2.goto();
    await settingsPage2.clickModelMenu();

    const operatorSelection = await settingsPage2.defaultTextModelSelect.textContent();
    expect(operatorSelection?.includes('自动选择') || operatorSelection !== superAdminSelection).toBeTruthy();

    await context2.close();
  });
});
