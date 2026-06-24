import { Page, Locator, expect } from '@playwright/test';

export class ScheduledTaskExecutionListPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly backButton: Locator;
  readonly executionTable: Locator;
  readonly tableRows: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: /执行历史/ });
    this.backButton = page.locator('.el-page-header__back');
    this.executionTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__body-wrapper .el-table__row');
    this.pagination = page.locator('.el-pagination');
  }

  async goto(taskId: number) {
    await this.page.goto(`/scheduled-tasks/${taskId}/executions`);
    await this.page.waitForLoadState('networkidle');
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectTableVisible() {
    await expect(this.executionTable).toBeVisible();
  }

  async getTableRowCount(): Promise<number> {
    return await this.tableRows.count();
  }

  async expectTableHasData() {
    const count = await this.getTableRowCount();
    expect(count).toBeGreaterThan(0);
  }

  async expectTableEmpty() {
    const emptyBlock = this.page.locator('.el-table__empty-block');
    await expect(emptyBlock).toBeVisible();
  }

  async expectPaginationVisible() {
    await expect(this.pagination).toBeVisible();
  }

  async getExecutionIdByRow(row: number): Promise<string> {
    const idCell = this.tableRows.nth(row).locator('td').first();
    return await idCell.textContent() || '';
  }

  async getExecutionStatusByRow(row: number): Promise<string> {
    const statusTag = this.tableRows.nth(row).locator('.el-tag');
    return await statusTag.textContent() || '';
  }

  async clickViewTaskButton(row: number) {
    const viewBtn = this.tableRows.nth(row).locator('button', { hasText: '查看任务' });
    await viewBtn.click();
  }

  async clickBackButton() {
    await this.backButton.click();
  }

  async changePageSize(size: number) {
    const sizeSelect = this.pagination.locator('.el-pagination__sizes .el-select');
    await sizeSelect.click();
    const option = this.page.locator('.el-select-dropdown__item', { hasText: String(size) });
    await option.click();
    await this.page.waitForLoadState('networkidle');
  }

  async goToNextPage() {
    const nextBtn = this.pagination.locator('.btn-next');
    await nextBtn.click();
    await this.page.waitForLoadState('networkidle');
  }

  async goToPage(pageNum: number) {
    const pageBtn = this.pagination.locator('.el-pager li', { hasText: String(pageNum) });
    await pageBtn.click();
    await this.page.waitForLoadState('networkidle');
  }

  async getTaskNameFromTitle(): Promise<string> {
    const title = await this.pageTitle.textContent() || '';
    // Title format: "执行历史 - {taskName}"
    const parts = title.split(' - ');
    return parts.length > 1 ? parts[1].trim() : '';
  }
}
