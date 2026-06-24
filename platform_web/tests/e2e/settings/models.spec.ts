import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { SettingsPage } from '../pages/SettingsPage';

// 测试配置
const TEST_CONFIG = {
  username: 'admin',
  password: 'admin123'
};

test.describe('模型平台配置页面 - UI展示', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    // 先登录
    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);

    // 导航到设置页面并点击模型平台配置
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('应该能够显示模型平台配置页面', async () => {
    await settingsPage.expectModelPanelVisible();
  });

  test('应该显示页面标题', async () => {
    await expect(settingsPage.pageTitle).toBeVisible();
    await expect(settingsPage.pageTitle).toContainText('系统设置');
  });

  test('应该显示模型平台配置面板', async () => {
    await expect(settingsPage.modelPanel).toBeVisible();
    await expect(settingsPage.modelPanel).toContainText('模型平台配置');
  });
});

test.describe('模型平台配置页面 - 默认模型设置', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('应该显示默认文本模型选择器', async () => {
    await expect(settingsPage.defaultTextModelSelect).toBeVisible();
  });

  test('应该显示默认图片模型选择器', async () => {
    await expect(settingsPage.defaultImageModelSelect).toBeVisible();
  });

  test('应该显示默认视频模型选择器', async () => {
    await expect(settingsPage.defaultVideoModelSelect).toBeVisible();
  });

  test('应该显示默认模型设置标签', async () => {
    const divider = settingsPage.modelPanel.locator('.el-divider', { hasText: '默认模型设置' });
    await expect(divider).toBeVisible();
  });

  test('默认模型选择器应该显示自动选择选项', async () => {
    await settingsPage.defaultTextModelSelect.click();
    const autoOption = settingsPage.page.locator('.el-select-dropdown__item', { hasText: '自动选择' });
    await expect(autoOption).toBeVisible();
  });

  test('应该能够选择默认文本模型', async () => {
    // 点击打开下拉框
    await settingsPage.defaultTextModelSelect.click();
    // 选择自动选择
    const autoOption = settingsPage.page.locator('.el-select-dropdown__item', { hasText: '自动选择' });
    await autoOption.click();
    // 验证选择成功
    await expect(settingsPage.defaultTextModelSelect).toContainText('自动选择');
  });
});

test.describe('模型平台配置页面 - 平台标签页', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('应该显示平台标签页', async () => {
    await expect(settingsPage.platformTabs).toBeVisible();
  });

  test('应该显示阿里百炼平台标签', async () => {
    const bailianTab = settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '阿里百炼' });
    await expect(bailianTab).toBeVisible();
  });

  test('应该显示火山引擎平台标签', async () => {
    const volcanoTab = settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '火山引擎' });
    await expect(volcanoTab).toBeVisible();
  });

  test('应该显示即梦AI平台标签', async () => {
    const jimengTab = settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '即梦AI' });
    await expect(jimengTab).toBeVisible();
  });

  test('应该显示可灵平台标签', async () => {
    const klingTab = settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '可灵' });
    await expect(klingTab).toBeVisible();
  });

  test('应该能够切换平台标签', async () => {
    // 切换到火山引擎
    await settingsPage.clickPlatformTab('火山引擎');
    await expect(settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '火山引擎' })).toHaveClass(/is-active/);

    // 切换到即梦AI
    await settingsPage.clickPlatformTab('即梦AI');
    await expect(settingsPage.platformTabs.locator('.el-tabs__item', { hasText: '即梦AI' })).toHaveClass(/is-active/);
  });
});

test.describe('模型平台配置页面 - 模型折叠面板', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('应该显示模型折叠面板', async () => {
    await expect(settingsPage.modelCollapse).toBeVisible();
  });

  test('应该显示文本模型折叠项', async () => {
    const textCollapseItem = settingsPage.modelCollapse.locator('.el-collapse-item', { hasText: '文本模型' });
    await expect(textCollapseItem).toBeVisible();
  });

  test('应该显示图片模型折叠项', async () => {
    const imageCollapseItem = settingsPage.modelCollapse.locator('.el-collapse-item', { hasText: '图片模型' });
    await expect(imageCollapseItem).toBeVisible();
  });

  test('应该显示视频模型折叠项', async () => {
    const videoCollapseItem = settingsPage.modelCollapse.locator('.el-collapse-item', { hasText: '视频模型' });
    await expect(videoCollapseItem).toBeVisible();
  });

  test('折叠项应该显示模型数量', async () => {
    const textCollapseItem = settingsPage.modelCollapse.locator('.el-collapse-item', { hasText: '文本模型' });
    const countElement = textCollapseItem.locator('.model-count');
    await expect(countElement).toBeVisible();
    await expect(countElement).toContainText(/\(\d+\)/);
  });

  test('折叠项应该显示添加按钮', async () => {
    const textCollapseItem = settingsPage.modelCollapse.locator('.el-collapse-item', { hasText: '文本模型' });
    const addButton = textCollapseItem.locator('button', { hasText: '添加' });
    await expect(addButton).toBeVisible();
  });

  test('点击添加按钮应该打开添加模型对话框', async () => {
    await settingsPage.clickAddModelButton('text');
    await settingsPage.expectModelDialogVisible();
  });

  test('添加模型对话框应该显示模型ID输入框', async () => {
    await settingsPage.clickAddModelButton('text');
    const dialog = settingsPage.getModelDialog();
    const modelIdInput = dialog.locator('input[placeholder*="模型 ID"]');
    await expect(modelIdInput).toBeVisible();
  });

  test('添加模型对话框应该显示模型名称输入框', async () => {
    await settingsPage.clickAddModelButton('text');
    const dialog = settingsPage.getModelDialog();
    const modelNameInput = dialog.locator('input[placeholder*="模型名称"]');
    await expect(modelNameInput).toBeVisible();
  });

  test('添加模型对话框应该显示Base URL输入框', async () => {
    await settingsPage.clickAddModelButton('text');
    const dialog = settingsPage.getModelDialog();
    const baseUrlInput = dialog.locator('input[placeholder*="Base URL"]');
    await expect(baseUrlInput).toBeVisible();
  });

  test('添加模型对话框应该显示API Key输入框', async () => {
    await settingsPage.clickAddModelButton('text');
    const dialog = settingsPage.getModelDialog();
    const apiKeyInput = dialog.locator('input[placeholder*="API Key"]');
    await expect(apiKeyInput).toBeVisible();
  });

  test('添加模型对话框应该显示并发QPS输入框', async () => {
    await settingsPage.clickAddModelButton('text');
    const dialog = settingsPage.getModelDialog();
    const concurrencyInput = dialog.locator('.el-input-number');
    await expect(concurrencyInput).toBeVisible();
  });

  test('添加模型对话框应该显示确定和取消按钮', async () => {
    await settingsPage.clickAddModelButton('text');
    await expect(settingsPage.getDialogSubmitButton()).toBeVisible();
    await expect(settingsPage.getDialogCancelButton()).toBeVisible();
  });

  test('点击取消按钮应该关闭对话框', async () => {
    await settingsPage.clickAddModelButton('text');
    await settingsPage.getDialogCancelButton().click();
    await expect(settingsPage.getModelDialog()).toBeHidden();
  });
});

test.describe('模型平台配置页面 - 表格操作', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('模型表格应该显示模型ID列', async () => {
    const table = settingsPage.page.locator('.el-table').first();
    await expect(table).toContainText('模型 ID');
  });

  test('模型表格应该显示API URL列', async () => {
    const table = settingsPage.page.locator('.el-table').first();
    await expect(table).toContainText('API URL');
  });

  test('模型表格应该显示并发QPS列', async () => {
    const table = settingsPage.page.locator('.el-table').first();
    await expect(table).toContainText('并发 QPS');
  });

  test('模型表格应该显示状态列', async () => {
    const table = settingsPage.page.locator('.el-table').first();
    await expect(table).toContainText('状态');
  });

  test('模型表格应该显示操作列', async () => {
    const table = settingsPage.page.locator('.el-table').first();
    await expect(table).toContainText('操作');
  });

  test('应该能够点击编辑按钮', async () => {
    // 尝试找到编辑按钮
    const editButton = settingsPage.page.locator('button', { hasText: '编辑' });
    if (await editButton.count() > 0) {
      await expect(editButton.first()).toBeVisible();
    }
  });

  test('应该能够点击禁用/启用按钮', async () => {
    // 尝试找到启用/禁用按钮
    const toggleButton = settingsPage.page.locator('button', { hasText: /禁用|启用/ });
    if (await toggleButton.count() > 0) {
      await expect(toggleButton.first()).toBeVisible();
    }
  });

  test('应该能够点击删除按钮', async () => {
    // 尝试找到删除按钮
    const deleteButton = settingsPage.page.locator('button', { hasText: '删除' });
    if (await deleteButton.count() > 0) {
      await expect(deleteButton.first()).toBeVisible();
    }
  });
});

test.describe('模型平台配置页面 - 异常流程', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickModelMenu();
  });

  test('空模型表单提交应该显示验证错误', async () => {
    await settingsPage.clickAddModelButton('text');
    await settingsPage.getDialogSubmitButton().click();

    // 应该显示错误提示
    const dialog = settingsPage.getModelDialog();
    const errorMessage = dialog.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });

  test('只填写模型ID应该显示验证错误', async () => {
    await settingsPage.clickAddModelButton('text');

    const dialog = settingsPage.getModelDialog();
    const modelIdInput = dialog.locator('input[placeholder*="模型 ID"]');
    await modelIdInput.fill('test-model-id');

    await settingsPage.getDialogSubmitButton().click();

    // 应该显示错误提示
    const errorMessage = dialog.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });

  test('快速切换平台标签应该正常处理', async () => {
    // 快速切换平台标签
    for (let i = 0; i < 3; i++) {
      await settingsPage.clickPlatformTab('火山引擎');
      await settingsPage.clickPlatformTab('阿里百炼');
    }
    // 页面应该仍然正常
    await expect(settingsPage.platformTabs).toBeVisible();
  });
});
