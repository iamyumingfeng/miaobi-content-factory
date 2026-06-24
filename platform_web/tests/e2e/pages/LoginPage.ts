import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly wechatTab: Locator;
  readonly passwordTab: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('input[placeholder*="用户名"]');
    this.passwordInput = page.locator('input[placeholder*="密码"]');
    this.loginButton = page.locator('button', { hasText: '登录' });
    this.wechatTab = page.locator('.el-tabs__item', { hasText: '微信扫码' });
    this.passwordTab = page.locator('.el-tabs__item', { hasText: '账号登录' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async loginWithPassword(username: string, password: string) {
    await this.passwordTab.click();
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    // 等待跳转到 dashboard
    await this.page.waitForURL(/\/dashboard/, { timeout: 10000 });
  }

  /**
   * 确保登出状态 - 清除所有 cookies 和本地存储
   */
  async ensureLoggedOut() {
    await this.page.context().clearCookies();
    await this.page.context().clearPermissions();
    await this.page.goto('/login');
    // 等待登录页面加载
    await this.expectOnLoginPage();
  }

  async switchToWechatLogin() {
    await this.wechatTab.click();
  }

  async expectLoginSuccess() {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }

  async expectSuccessMessage(message: string) {
    await expect(this.page.locator('.el-message')).toContainText(message);
  }

  async expectOnLoginPage() {
    await expect(this.page).toHaveURL(/\/login/);
  }

  async expectBrandTitleVisible() {
    await expect(this.page.locator('text=妙笔内容工场')).toBeVisible();
  }

  async expectTabsVisible() {
    await expect(this.passwordTab).toBeVisible();
    await expect(this.wechatTab).toBeVisible();
  }
}
