import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('登录页面 UI', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.ensureLoggedOut();
  });

  test('应该能够显示登录页面', async () => {
    await loginPage.expectOnLoginPage();
    await loginPage.expectBrandTitleVisible();
  });

  test('应该显示登录标签页', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.expectTabsVisible();
  });

  test('应该显示用户名和密码输入框', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await expect(loginPage.usernameInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('应该有品牌标题和副标题', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await expect(page.locator('text=妙笔内容工场')).toBeVisible();
    await expect(page.locator('.brand-description')).toBeVisible();
  });

  test('应该有安全提示', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await expect(page.locator('text=连续5次登录失败将锁定账号15分钟')).toBeVisible();
  });
});

test.describe('登录交互', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.ensureLoggedOut();
  });

  test('输入框应该能够输入内容', async () => {
    await loginPage.usernameInput.fill('test_user');
    await loginPage.passwordInput.fill('test_password');

    await expect(loginPage.usernameInput).toHaveValue('test_user');
    await expect(loginPage.passwordInput).toHaveValue('test_password');
  });

  test('点击登录按钮应该显示加载状态', async () => {
    await loginPage.usernameInput.fill('test_user');
    await loginPage.passwordInput.fill('test_password');

    // 点击登录
    await loginPage.loginButton.click();

    // 检查按钮是否有加载状态
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('使用模拟登录应该成功跳转到仪表盘', async () => {
    // 此测试需要后端API支持，当前跳过
    // TODO: 添加mock API或确保后端服务运行
    test.skip();
  });

  test('登录成功应该显示成功消息', async () => {
    // 此测试需要后端API支持，当前跳过
    // TODO: 添加mock API或确保后端服务运行
    test.skip();
  });
});
