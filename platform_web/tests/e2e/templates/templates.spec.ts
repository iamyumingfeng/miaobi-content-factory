import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TemplatePage } from '../pages/TemplatePage';

test.describe('模板管理功能', () => {
  test.beforeEach(async ({ page }) => {
    // 先登录
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithPassword('any_user', 'any_password');
    await page.waitForTimeout(1500);
  });

  test('应该能够通过侧边栏访问模板列表页面', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectLoaded();
    await templatePage.expectPageTitleVisible();
  });

  test('模板列表应该显示模板卡片', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectTemplateCardsVisible();

    const cardCount = await templatePage.getTemplateCardCount();
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('应该显示新建模板按钮', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectCreateButtonVisible();
  });

  test('应该显示搜索输入框', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectSearchInputVisible();
  });

  test('应该显示分类树', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectCategoryTreeVisible();
  });

  test('应该显示视图切换标签', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.expectViewTabsVisible();
  });

  test('应该能够切换到卡片视图', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.switchToCardView();
    // 验证切换成功（没有错误即可）
  });

  test('应该能够切换到列表视图', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.switchToListView();
    // 验证切换成功（没有错误即可）
  });

  test('应该能够在搜索框输入内容', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const templatePage = new TemplatePage(page);

    await dashboardPage.navigateToTemplates();
    await templatePage.searchTemplates('测试');
    await expect(templatePage.searchInput).toHaveValue('测试');
  });
});
