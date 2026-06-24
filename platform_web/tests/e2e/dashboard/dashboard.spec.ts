import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('仪表盘功能', () => {
  test.beforeEach(async ({ page }) => {
    // 先登录
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithPassword('any_user', 'any_password');
    await page.waitForTimeout(1500);
  });

  test('登录后应该能够访问仪表盘', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.expectLoaded();
    await dashboardPage.expectPageTitleVisible();
  });

  test('仪表盘应该显示统计卡片', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectStatCardsVisible();

    // 验证有 4 个统计卡片
    const cardCount = await dashboardPage.getStatCardCount();
    expect(cardCount).toBe(4);
  });

  test('仪表盘应该显示趋势图表', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectTrendChartVisible();
  });

  test('仪表盘应该显示最近任务表格', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectRecentTasksTableVisible();
  });

  test('仪表盘应该显示失败任务告警', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectFailedTasksSectionVisible();
  });

  test('应该能够显示侧边栏', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectSidebarVisible();
  });

  test('侧边栏应该有菜单项', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    const itemCount = await dashboardPage.getSidebarItemCount();
    expect(itemCount).toBeGreaterThan(0);
  });

  test('应该能够通过侧边栏导航到模板库', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToTemplates();
    await expect(page).toHaveURL(/\/templates\/list/);
  });

  test('应该能够通过侧边栏导航到素材库', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToMaterials();
    await expect(page).toHaveURL(/\/materials/);
  });

  test('应该能够通过侧边栏导航到创建任务', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToCreateGeneration();
    await expect(page).toHaveURL(/\/generation\/create/);
  });

  test('应该能够通过侧边栏导航到任务列表', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToGenerationList();
    await expect(page).toHaveURL(/\/generation\/list/);
  });

  test('应该能够通过侧边栏导航到站内通知', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToNotifications();
    await expect(page).toHaveURL(/\/notifications/);
  });

  test('应该能够通过侧边栏导航到系统设置', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToSettings();
    await expect(page).toHaveURL(/\/settings/);
  });

  test('应该能够通过侧边栏导航到创作管理员', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToAdminUsers();
    await expect(page).toHaveURL(/\/users\/admin/);
  });

  test('应该能够通过侧边栏导航到创作员管理', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateToSubUsers();
    await expect(page).toHaveURL(/\/users\/sub/);
  });

  test('应该显示用户下拉菜单', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.expectUserDropdown();
  });

  test('点击用户下拉菜单应该显示选项', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.clickUserDropdown();
    await page.waitForTimeout(300);

    // 验证下拉菜单出现
    const personalSettings = page.locator('text=个人设置');
    const logout = page.locator('text=退出登录');

    await expect(personalSettings).toBeVisible();
    await expect(logout).toBeVisible();
  });

  test('应该能够切换侧边栏折叠', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    // 点击折叠按钮
    await dashboardPage.toggleSidebar();
    await page.waitForTimeout(300);

    // 再次点击展开
    await dashboardPage.toggleSidebar();
    await page.waitForTimeout(300);
  });

  test('应该能够点击刷新任务按钮', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.clickRefreshTasks();
    // 只是验证按钮可点击，不验证实际功能
  });

  test('应该能够点击清除所有告警按钮', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    await dashboardPage.clickClearAllAlerts();
    await page.waitForTimeout(300);

    // 验证确认对话框出现
    const confirmDialog = page.locator('.el-message-box');
    await expect(confirmDialog).toBeVisible();

    // 点击取消
    const cancelBtn = page.locator('button', { hasText: '取消' });
    await cancelBtn.click();
  });
});
