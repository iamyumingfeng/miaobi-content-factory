import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { SettingsPage } from '../pages/SettingsPage';

// 测试配置
const TEST_CONFIG = {
  username: 'admin',
  password: 'admin123'
};

test.describe('个人设置页面 - UI展示', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    // 先登录
    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);

    // 导航到设置页面
    await settingsPage.goto();
    await settingsPage.expectOnSettingsPage();
  });

  test('应该能够显示系统设置页面', async () => {
    await settingsPage.expectOnSettingsPage();
  });

  test('应该显示页面标题', async () => {
    await expect(settingsPage.pageTitle).toBeVisible();
    await expect(settingsPage.pageTitle).toContainText('系统设置');
  });

  test('应该显示设置菜单', async () => {
    await expect(settingsPage.settingsMenu).toBeVisible();
    await expect(settingsPage.profileMenuItem).toBeVisible();
  });

  test('应该显示个人设置菜单项', async () => {
    await expect(settingsPage.profileMenuItem).toBeVisible();
    await expect(settingsPage.profileMenuItem).toContainText('个人设置');
  });

  test('应该显示模型平台配置菜单项', async () => {
    await expect(settingsPage.modelMenuItem).toBeVisible();
    await expect(settingsPage.modelMenuItem).toContainText('模型平台配置');
  });

  test('默认应该显示个人设置面板', async () => {
    await expect(settingsPage.profilePanel).toBeVisible();
    await expect(settingsPage.profilePanel).toContainText('个人设置');
  });
});

test.describe('个人设置页面 - 个人信息', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickProfileMenu();
  });

  test('应该显示当前用户名输入框', async () => {
    await expect(settingsPage.usernameInput).toBeVisible();
    // 用户名输入框应该是禁用的
    await expect(settingsPage.usernameInput).toBeDisabled();
  });

  test('应该显示自定义昵称输入框', async () => {
    await expect(settingsPage.nicknameInput).toBeVisible();
    await expect(settingsPage.nicknameInput).toBeEnabled();
  });

  test('应该显示保存昵称按钮', async () => {
    await expect(settingsPage.saveNicknameButton).toBeVisible();
    await expect(settingsPage.saveNicknameButton).toContainText('保存昵称');
  });

  test('自定义昵称输入框应该能够输入内容', async () => {
    const testNickname = '测试昵称' + Date.now();
    await settingsPage.nicknameInput.fill(testNickname);
    await expect(settingsPage.nicknameInput).toHaveValue(testNickname);
  });

  test('应该能够保存昵称', async () => {
    const testNickname = '测试昵称' + Date.now();
    await settingsPage.nicknameInput.fill(testNickname);
    await settingsPage.saveNicknameButton.click();

    // 等待成功消息
    await settingsPage.expectSuccessMessage('昵称保存成功');
  });

  test('清空昵称应该能够保存', async () => {
    await settingsPage.nicknameInput.fill('');
    await settingsPage.saveNicknameButton.click();

    // 应该显示成功消息
    await settingsPage.expectSuccessMessage('昵称保存成功');
  });
});

test.describe('个人设置页面 - 修改密码', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickProfileMenu();
  });

  test('应该显示原密码输入框', async () => {
    await expect(settingsPage.oldPasswordInput).toBeVisible();
    await expect(settingsPage.oldPasswordInput).toBeEnabled();
  });

  test('应该显示新密码输入框', async () => {
    await expect(settingsPage.newPasswordInput).toBeVisible();
    await expect(settingsPage.newPasswordInput).toBeEnabled();
  });

  test('应该显示确认新密码输入框', async () => {
    await expect(settingsPage.confirmPasswordInput).toBeVisible();
    await expect(settingsPage.confirmPasswordInput).toBeEnabled();
  });

  test('应该显示修改密码按钮', async () => {
    await expect(settingsPage.changePasswordButton).toBeVisible();
    await expect(settingsPage.changePasswordButton).toContainText('修改密码');
  });

  test('密码输入框应该能够输入内容', async () => {
    await settingsPage.oldPasswordInput.fill('oldpassword123');
    await settingsPage.newPasswordInput.fill('newpassword123');
    await settingsPage.confirmPasswordInput.fill('newpassword123');

    // 密码输入框的值应该被隐藏（type="password"）
    const inputType = await settingsPage.oldPasswordInput.getAttribute('type');
    expect(inputType).toBe('password');
  });

  test('输入错误原密码应该显示错误', async () => {
    await settingsPage.oldPasswordInput.fill('wrongpassword');
    await settingsPage.newPasswordInput.fill('newpassword123');
    await settingsPage.confirmPasswordInput.fill('newpassword123');
    await settingsPage.changePasswordButton.click();

    // 应该显示错误消息
    await settingsPage.expectErrorMessage('原密码错误');
  });

  test('新密码和确认密码不一致应该显示验证错误', async () => {
    await settingsPage.oldPasswordInput.fill(TEST_CONFIG.password);
    await settingsPage.newPasswordInput.fill('newpassword123');
    await settingsPage.confirmPasswordInput.fill('differentpassword');
    await settingsPage.changePasswordButton.click();

    // 应该显示验证错误
    const errorMessage = settingsPage.page.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });

  test('密码长度少于6位应该显示验证错误', async () => {
    await settingsPage.oldPasswordInput.fill(TEST_CONFIG.password);
    await settingsPage.newPasswordInput.fill('123');
    await settingsPage.confirmPasswordInput.fill('123');
    await settingsPage.changePasswordButton.click();

    // 应该显示验证错误
    const errorMessage = settingsPage.page.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });
});

test.describe('个人设置页面 - 菜单导航', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
  });

  test('点击个人设置菜单应该显示个人设置面板', async () => {
    await settingsPage.clickProfileMenu();
    await expect(settingsPage.profilePanel).toBeVisible();
    await expect(settingsPage.profilePanel).toContainText('个人设置');
  });

  test('点击模型平台配置菜单应该显示模型配置面板', async () => {
    await settingsPage.clickModelMenu();
    await expect(settingsPage.modelPanel).toBeVisible();
    await expect(settingsPage.modelPanel).toContainText('模型平台配置');
  });

  test('菜单项应该有正确的激活状态', async () => {
    // 点击个人设置
    await settingsPage.clickProfileMenu();
    await expect(settingsPage.profileMenuItem).toHaveClass(/is-active/);

    // 点击模型平台配置
    await settingsPage.clickModelMenu();
    await expect(settingsPage.modelMenuItem).toHaveClass(/is-active/);
  });
});

test.describe('个人设置页面 - 异常流程', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);
    await settingsPage.goto();
    await settingsPage.clickProfileMenu();
  });

  test('空昵称应该能够保存', async () => {
    await settingsPage.nicknameInput.fill('');
    await settingsPage.saveNicknameButton.click();
    await settingsPage.expectSuccessMessage('昵称保存成功');
  });

  test('特殊字符昵称应该能够保存', async () => {
    const specialNickname = '测试_昵称-123!@#';
    await settingsPage.nicknameInput.fill(specialNickname);
    await settingsPage.saveNicknameButton.click();
    await settingsPage.expectSuccessMessage('昵称保存成功');
  });

  test('超长昵称应该能够处理', async () => {
    const longNickname = 'a'.repeat(100);
    await settingsPage.nicknameInput.fill(longNickname);
    await settingsPage.saveNicknameButton.click();
    // 应该显示成功或错误消息
    const message = settingsPage.page.locator('.el-message');
    await expect(message).toBeVisible({ timeout: 5000 });
  });
});
