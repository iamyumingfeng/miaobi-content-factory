import { Page, Locator, expect } from '@playwright/test';

export class ScheduledTaskListPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly statusSelect: Locator;
  readonly taskTypeSelect: Locator;
  readonly searchButton: Locator;
  readonly taskTable: Locator;
  readonly tableRows: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '定时任务管理' });
    this.createButton = page.locator('button', { hasText: '创建任务' });
    this.searchInput = page.locator('input[placeholder*="搜索任务名称"]');
    this.statusSelect = page.locator('.el-select', { has: page.locator('input[placeholder*="任务状态"]') });
    this.taskTypeSelect = page.locator('.el-select', { has: page.locator('input[placeholder*="任务类型"]') });
    this.searchButton = page.locator('button', { hasText: '搜索' });
    this.taskTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__body-wrapper .el-table__row');
    this.pagination = page.locator('.el-pagination');
  }

  async goto() {
    await this.page.goto('/scheduled-tasks');
    await this.page.waitForLoadState('networkidle');
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectCreateButtonVisible() {
    await expect(this.createButton).toBeVisible();
  }

  async clickCreateButton() {
    await this.createButton.click();
    await this.page.waitForURL(/\/scheduled-tasks\/create/);
  }

  async searchByKeyword(keyword: string) {
    await this.searchInput.fill(keyword);
    await this.searchButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  async clearSearch() {
    await this.searchInput.clear();
    await this.searchButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  async selectStatus(status: string) {
    await this.statusSelect.click();
    const option = this.page.locator('.el-select-dropdown__item', { hasText: status });
    await option.click();
    await this.page.waitForLoadState('networkidle');
  }

  async selectTaskType(type: string) {
    await this.taskTypeSelect.click();
    const option = this.page.locator('.el-select-dropdown__item', { hasText: type });
    await option.click();
    await this.page.waitForLoadState('networkidle');
  }

  async expectTableVisible() {
    await expect(this.taskTable).toBeVisible();
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

  async clickViewButton(row: number) {
    const viewBtn = this.tableRows.nth(row).locator('button', { hasText: '查看' });
    await viewBtn.click();
    await this.page.waitForURL(/\/scheduled-tasks\/\d+/);
  }

  async clickEditButton(row: number) {
    const editBtn = this.tableRows.nth(row).locator('button', { hasText: '编辑' });
    await editBtn.click();
    await this.page.waitForURL(/\/scheduled-tasks\/edit\/\d+/);
  }

  async clickDeleteButton(row: number) {
    const deleteBtn = this.tableRows.nth(row).locator('button', { hasText: '删除' });
    await deleteBtn.click();
  }

  async clickToggleButton(row: number) {
    const row_ = this.tableRows.nth(row);
    const toggleBtn = row_.locator('button', { hasText: /禁用|启用/ });
    await toggleBtn.click();
  }

  async clickExecuteButton(row: number) {
    const executeBtn = this.tableRows.nth(row).locator('button', { hasText: '执行' });
    await executeBtn.click();
  }

  async confirmDialog() {
    const confirmBtn = this.page.locator('.el-message-box__btns button', { hasText: '确定' });
    await confirmBtn.click();
    await this.page.waitForLoadState('networkidle');
  }

  async cancelDialog() {
    const cancelBtn = this.page.locator('.el-message-box__btns button', { hasText: '取消' });
    await cancelBtn.click();
  }

  async expectSuccessMessage() {
    await expect(this.page.locator('.el-message--success')).toBeVisible({ timeout: 5000 });
  }

  async expectErrorMessage() {
    await expect(this.page.locator('.el-message--error')).toBeVisible({ timeout: 5000 });
  }

  async expectPaginationVisible() {
    await expect(this.pagination).toBeVisible();
  }

  async getTaskNameByRow(row: number): Promise<string> {
    const nameCell = this.tableRows.nth(row).locator('.name-text');
    return await nameCell.textContent() || '';
  }

  async getTaskTypeByRow(row: number): Promise<string> {
    const typeCell = this.tableRows.nth(row).locator('.el-tag').first();
    return await typeCell.textContent() || '';
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

  async goToPreviousPage() {
    const prevBtn = this.pagination.locator('.btn-prev');
    await prevBtn.click();
    await this.page.waitForLoadState('networkidle');
  }
}
