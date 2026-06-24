import { Page, Locator, expect } from '@playwright/test';

export class ScheduledTaskDetailPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly backButton: Locator;
  readonly editButton: Locator;
  readonly toggleButton: Locator;
  readonly executeButton: Locator;
  readonly basicInfoCard: Locator;
  readonly executionStatsCard: Locator;
  readonly configDetailCard: Locator;
  readonly executionHistoryCard: Locator;
  readonly viewExecutionsButton: Locator;
  readonly executionTable: Locator;
  readonly executionPagination: Locator;
  readonly logDialog: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '任务详情' });
    this.backButton = page.locator('.el-page-header__back');
    this.editButton = page.locator('button', { hasText: '编辑任务' });
    this.toggleButton = page.locator('button', { hasText: /禁用|启用/ });
    this.executeButton = page.locator('button', { hasText: '立即执行' });
    this.basicInfoCard = page.locator('.card', { has: page.locator('.card-title', { hasText: '基本信息' }) });
    this.executionStatsCard = page.locator('.card', { has: page.locator('.card-title', { hasText: '执行统计' }) });
    this.configDetailCard = page.locator('.card', { has: page.locator('.card-title', { hasText: '配置详情' }) });
    this.executionHistoryCard = page.locator('.card', { has: page.locator('.card-title', { hasText: '执行历史' }) });
    this.viewExecutionsButton = page.locator('button', { hasText: '查看执行历史' });
    this.executionTable = page.locator('.card', { has: page.locator('.card-title', { hasText: '执行历史' }) }).locator('.el-table');
    this.executionPagination = page.locator('.card', { has: page.locator('.card-title', { hasText: '执行历史' }) }).locator('.el-pagination');
    this.logDialog = page.locator('.el-dialog', { hasText: '执行日志' });
  }

  async goto(taskId: number) {
    await this.page.goto(`/scheduled-tasks/${taskId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectBasicInfoCardVisible() {
    await expect(this.basicInfoCard).toBeVisible();
  }

  async expectExecutionStatsCardVisible() {
    await expect(this.executionStatsCard).toBeVisible();
  }

  async expectConfigDetailCardVisible() {
    await expect(this.configDetailCard).toBeVisible();
  }

  async expectExecutionHistoryCardVisible() {
    await expect(this.executionHistoryCard).toBeVisible();
  }

  async expectEditButtonVisible() {
    await expect(this.editButton).toBeVisible();
  }

  async expectToggleButtonVisible() {
    await expect(this.toggleButton).toBeVisible();
  }

  async expectExecuteButtonVisible() {
    await expect(this.executeButton).toBeVisible();
  }

  async clickEditButton() {
    await this.editButton.click();
    await this.page.waitForURL(/\/scheduled-tasks\/edit\/\d+/);
  }

  async clickToggleButton() {
    await this.toggleButton.click();
  }

  async clickExecuteButton() {
    await this.executeButton.click();
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

  async clickViewExecutions() {
    await this.viewExecutionsButton.click();
    await this.page.waitForURL(/\/scheduled-tasks\/\d+\/executions/);
  }

  async clickTab(tabName: string) {
    const tab = this.page.locator('.el-tabs__item', { hasText: tabName });
    await tab.click();
  }

  async expectTabVisible(tabName: string) {
    const tab = this.page.locator('.el-tabs__item', { hasText: tabName });
    await expect(tab).toBeVisible();
  }

  async expectTabHidden(tabName: string) {
    const tab = this.page.locator('.el-tabs__item', { hasText: tabName });
    await expect(tab).not.toBeVisible();
  }

  async getTaskName(): Promise<string> {
    const descriptions = this.page.locator('.el-descriptions__body .el-descriptions__cell');
    for (let i = 0; i < await descriptions.count(); i++) {
      const text = await descriptions.nth(i).textContent();
      if (text && text.trim() && !text.includes('任务名称') && !text.includes('任务类型') && !text.includes('调度类型') && !text.includes('执行时间') && !text.includes('下次执行') && !text.includes('创建时间')) {
        return text.trim();
      }
    }
    return '';
  }

  async getExecutionStats(): Promise<{ total: number; success: number; failed: number }> {
    const statValues = this.executionStatsCard.locator('.stat-value');
    const total = parseInt(await statValues.nth(0).textContent() || '0');
    const success = parseInt(await statValues.nth(1).textContent() || '0');
    const failed = parseInt(await statValues.nth(2).textContent() || '0');
    return { total, success, failed };
  }

  async expectExecutionTableVisible() {
    await expect(this.executionTable).toBeVisible();
  }

  async getExecutionRowCount(): Promise<number> {
    return await this.executionTable.locator('.el-table__row').count();
  }

  async clickViewLogButton(row: number) {
    const viewLogBtn = this.executionTable.locator('.el-table__row').nth(row).locator('button', { hasText: '查看日志' });
    await viewLogBtn.click();
  }

  async expectLogDialogVisible() {
    await expect(this.logDialog).toBeVisible();
  }

  async closeLogDialog() {
    const closeBtn = this.logDialog.locator('button', { hasText: '关闭' });
    await closeBtn.click();
  }

  async clickBackButton() {
    await this.backButton.click();
  }

  async expectExecuteButtonDisabled() {
    await expect(this.executeButton).toBeDisabled();
  }

  async expectExecuteButtonEnabled() {
    await expect(this.executeButton).toBeEnabled();
  }
}
