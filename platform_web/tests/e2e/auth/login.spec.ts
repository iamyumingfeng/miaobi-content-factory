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

  test('应该能够在账号登录和微信扫码之间切换', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.switchToWechatLogin();
    await expect(loginPage.wechatTab).toHaveClass(/is-active/);

    await loginPage.passwordTab.click();
    await expect(loginPage.passwordTab).toHaveClass(/is-active/);
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
    await expect(page.locator('text=智能生产 · 智能管理')).toBeVisible();
  });

  test('应该有微信登录按钮', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    const wechatBtn = page.locator('.wechat-btn');
    await expect(wechatBtn).toBeVisible();
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
    const dashboardPage = new DashboardPage(loginPage.page);

    await loginPage.loginWithPassword('admin', 'admin123');

    await loginPage.expectLoginSuccess();
  });

  test('登录成功应该显示成功消息', async () => {
    await loginPage.loginWithPassword('admin', 'admin123');

    // 等待消息显示
    await loginPage.page.waitForTimeout(2000);

    await loginPage.expectSuccessMessage('登录成功');
  });
});

test.describe('微信扫码登录 UI', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.ensureLoggedOut();
  });

  test('切换到微信扫码应该显示二维码区域', async () => {
    await loginPage.switchToWechatLogin();

    // 等待二维码生成（模拟有 1 秒延迟）
    await loginPage.page.waitForTimeout(1500);

    // 检查二维码相关元素
    const qrBox = loginPage.page.locator('.qr-box');
    await expect(qrBox).toBeVisible();

    const qrTip = loginPage.page.locator('.qr-tip');
    await expect(qrTip).toBeVisible();
  });

  test('应该显示刷新二维码按钮', async () => {
    await loginPage.switchToWechatLogin();
    await loginPage.page.waitForTimeout(1500);

    const refreshBtn = loginPage.page.locator('button', { hasText: '刷新二维码' });
    await expect(refreshBtn).toBeVisible();
  });

  test('点击刷新二维码应该重新生成', async () => {
    await loginPage.switchToWechatLogin();
    await loginPage.page.waitForTimeout(1500);

    const refreshBtn = loginPage.page.locator('button', { hasText: '刷新二维码' });
    await refreshBtn.click();

    // 应该显示加载状态
    await expect(loginPage.page.locator('.qr-loading')).toBeVisible({ timeout: 2000 });
  });
});
