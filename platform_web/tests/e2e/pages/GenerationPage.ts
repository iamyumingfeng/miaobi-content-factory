import { Page, Locator, expect } from '@playwright/test';

export class GenerationPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createTaskButton: Locator;
  readonly taskCards: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '生成任务列表' });
    this.createTaskButton = page.locator('button', { hasText: '创建任务' });
    this.taskCards = page.locator('.task-card');
    this.searchInput = page.locator('input[placeholder*="搜索任务ID/名称"]');
    this.statusFilter = page.locator('.el-select').first();
    this.pagination = page.locator('.pagination');
  }

  async gotoList() {
    await this.page.goto('/generation/list');
  }

  async gotoCreate() {
    await this.page.goto('/generation/create');
  }

  async expectListLoaded() {
    await expect(this.page).toHaveURL(/\/generation\/list/);
  }

  async expectCreateLoaded() {
    await expect(this.page).toHaveURL(/\/generation\/create/);
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectTaskCardsVisible() {
    await expect(this.taskCards.first()).toBeVisible();
  }

  async getTaskCardCount() {
    return await this.taskCards.count();
  }

  async expectCreateTaskButtonVisible() {
    await expect(this.createTaskButton).toBeVisible();
  }

  async clickCreateTaskButton() {
    await this.createTaskButton.click();
  }

  async expectSearchInputVisible() {
    await expect(this.searchInput).toBeVisible();
  }

  async searchTasks(keyword: string) {
    await this.searchInput.fill(keyword);
  }

  async expectStatusFilterVisible() {
    await expect(this.statusFilter).toBeVisible();
  }

  async expectPaginationVisible() {
    await expect(this.pagination).toBeVisible();
  }

  async clickFirstTask() {
    const firstTask = this.taskCards.first();
    const viewDetailBtn = firstTask.locator('button', { hasText: '查看详情' });
    await viewDetailBtn.click();
  }

  async expectTaskDetailVisible() {
    await expect(this.page).toHaveURL(/\/generation\/detail\//);
  }

  async filterByStatus(status: string) {
    await this.statusFilter.click();
    await this.page.waitForTimeout(300);
    const label = status === 'completed' ? '已完成' : status === 'failed' ? '失败' : status === 'generating' ? '生成中' : status === 'queued' ? '排队中' : status === 'paused' ? '已暂停' : status;
    await this.page.locator(`.el-select-dropdown__item span:has-text("${label}")`).first().click();
  }

  async clickFirstTaskDetail() {
    // 在列表页（表格视图）点击第一行的"详情"按钮
    const detailBtn = this.page.locator('.el-table__body tr').first()
      .locator('text=详情');
    await detailBtn.click();
  }
}
