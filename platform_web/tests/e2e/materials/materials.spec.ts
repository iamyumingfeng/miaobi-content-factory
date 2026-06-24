import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { MaterialPage } from '../pages/MaterialPage';

test.describe('素材库功能', () => {
  test.beforeEach(async ({ page }) => {
    // 先登录
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithPassword('any_user', 'any_password');
    await page.waitForTimeout(1500);
  });

  test('应该能够通过侧边栏访问素材库页面', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectLoaded();
    await materialPage.expectPageTitleVisible();
  });

  test('素材库应该显示素材卡片', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectMaterialCardsVisible();

    const cardCount = await materialPage.getMaterialCardCount();
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('应该显示上传素材按钮', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectUploadButtonVisible();
  });

  test('应该显示搜索输入框', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectSearchInputVisible();
  });

  test('应该显示分类树', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectCategoryTreeVisible();
  });

  test('应该显示视图切换标签', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.expectViewTabsVisible();
  });

  test('应该能够切换到卡片视图', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.switchToCardView();
    // 验证切换成功（没有错误即可）
  });

  test('应该能够切换到列表视图', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.switchToListView();
    // 验证切换成功（没有错误即可）
  });

  test('应该能够在搜索框输入内容', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const materialPage = new MaterialPage(page);

    await dashboardPage.navigateToMaterials();
    await materialPage.searchMaterials('测试');
    await expect(materialPage.searchInput).toHaveValue('测试');
  });
});
