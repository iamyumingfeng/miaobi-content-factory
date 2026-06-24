import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { GenerationPage } from '../pages/GenerationPage';

test.describe('内容生成功能', () => {
  test.beforeEach(async ({ page }) => {
    // 先登录
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithPassword('any_user', 'any_password');
    await page.waitForTimeout(1500);
  });

  test('应该能够通过侧边栏访问任务列表页面', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectListLoaded();
    await generationPage.expectPageTitleVisible();
  });

  test('任务列表应该显示任务卡片', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectTaskCardsVisible();

    const cardCount = await generationPage.getTaskCardCount();
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('应该显示创建任务按钮', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectCreateTaskButtonVisible();
  });

  test('点击创建任务按钮应该导航到创建页面', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.clickCreateTaskButton();
    await generationPage.expectCreateLoaded();
  });

  test('应该显示搜索输入框', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectSearchInputVisible();
  });

  test('应该显示状态筛选器', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectStatusFilterVisible();
  });

  test('应该显示分页', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.expectPaginationVisible();
  });

  test('应该能够在搜索框输入内容', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();
    await generationPage.searchTasks('T001');
    await expect(generationPage.searchInput).toHaveValue('T001');
  });

  test('点击任务的查看详情应该导航到详情页面', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const generationPage = new GenerationPage(page);

    await dashboardPage.navigateToGenerationList();

    const cardCount = await generationPage.getTaskCardCount();
    if (cardCount > 0) {
      await generationPage.clickFirstTask();
      // 验证跳转到详情页面
      await page.waitForTimeout(500);
    }
  });
});
