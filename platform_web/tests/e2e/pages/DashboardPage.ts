import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly statCards: Locator;
  readonly recentTasksTable: Locator;
  readonly sidebar: Locator;
  readonly sidebarItems: Locator;
  readonly trendChart: Locator;
  readonly failedTasksSection: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '仪表盘' });
    this.statCards = page.locator('.stat-card');
    this.recentTasksTable = page.locator('.el-table').first();
    this.sidebar = page.locator('.sidebar-menu');
    this.sidebarItems = page.locator('.el-menu-item');
    this.trendChart = page.locator('.chart-container');
    this.failedTasksSection = page.locator('text=失败任务告警');
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectStatCardsVisible() {
    await expect(this.statCards.first()).toBeVisible();
  }

  async getStatCardCount() {
    return await this.statCards.count();
  }

  async expectSidebarVisible() {
    await expect(this.sidebar).toBeVisible();
  }

  async getSidebarItemCount() {
    return await this.sidebarItems.count();
  }

  async clickSidebarItem(text: string) {
    const item = this.sidebarItems.filter({ hasText: text }).first();
    await item.click();
  }

  async expandSubMenu(text: string) {
    const subMenu = this.page.locator('.el-sub-menu__title', { hasText: text });
    await subMenu.click();
  }

  async navigateToAdminUsers() {
    await this.expandSubMenu('用户管理');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('创作管理员');
  }

  async navigateToSubUsers() {
    await this.expandSubMenu('用户管理');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('创作员管理');
  }

  async navigateToTemplates() {
    await this.expandSubMenu('模板素材管理');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('模板库');
  }

  async navigateToMaterials() {
    await this.expandSubMenu('模板素材管理');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('素材库');
  }

  async navigateToCreateGeneration() {
    await this.expandSubMenu('内容生成');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('创建任务');
  }

  async navigateToGenerationList() {
    await this.expandSubMenu('内容生成');
    await this.page.waitForTimeout(300);
    await this.clickSidebarItem('任务列表');
  }

  async navigateToNotifications() {
    await this.clickSidebarItem('站内通知');
  }

  async navigateToSettings() {
    await this.clickSidebarItem('系统设置');
  }

  async expectTrendChartVisible() {
    await expect(this.trendChart).toBeVisible();
  }

  async expectRecentTasksTableVisible() {
    await expect(this.recentTasksTable).toBeVisible();
  }

  async expectFailedTasksSectionVisible() {
    await expect(this.failedTasksSection).toBeVisible();
  }

  async clickRefreshTasks() {
    const refreshBtn = this.page.locator('button', { hasText: '刷新' });
    await refreshBtn.click();
  }

  async clickClearAllAlerts() {
    const clearBtn = this.page.locator('button', { hasText: '清除告警' });
    await clearBtn.click();
  }

  async expectUserDropdown() {
    const userInfo = this.page.locator('.user-info');
    await expect(userInfo).toBeVisible();
  }

  async clickUserDropdown() {
    const userInfo = this.page.locator('.user-info');
    await userInfo.click();
  }

  async toggleSidebar() {
    const collapseIcon = this.page.locator('.collapse-icon');
    await collapseIcon.click();
  }
}
