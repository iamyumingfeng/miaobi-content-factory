import { Page, Locator, expect } from '@playwright/test';

export class ScheduledTaskCreatePage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly backButton: Locator;
  readonly form: Locator;
  readonly nameInput: Locator;
  readonly taskTypeCustom: Locator;
  readonly taskTypeBenchmark: Locator;
  readonly scheduleTypeDaily: Locator;
  readonly scheduleTypeWeekly: Locator;
  readonly addTimePointButton: Locator;
  readonly weekdayCheckboxes: Locator;
  readonly selectTemplateButton: Locator;
  readonly selectSubUserButton: Locator;
  readonly selectBenchmarkMaterialButton: Locator;
  readonly modelAutoSelect: Locator;
  readonly modelManualSelect: Locator;
  readonly dedupSwitch: Locator;
  readonly imageDedupSwitch: Locator;
  readonly imageCountInput: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: /创建定时任务|编辑定时任务/ });
    this.backButton = page.locator('.el-page-header__back');
    this.form = page.locator('.el-form');
    this.nameInput = page.locator('input[placeholder*="请输入任务名称"]');
    this.taskTypeCustom = page.locator('.el-radio', { hasText: '自定义文案' });
    this.taskTypeBenchmark = page.locator('.el-radio', { hasText: '对标文案' });
    this.scheduleTypeDaily = page.locator('.el-radio', { hasText: '每日' });
    this.scheduleTypeWeekly = page.locator('.el-radio', { hasText: '每周' });
    this.addTimePointButton = page.locator('button', { hasText: '添加时间点' });
    this.weekdayCheckboxes = page.locator('.el-checkbox-group .el-checkbox');
    this.selectTemplateButton = page.locator('button', { hasText: '选择模板' });
    this.selectSubUserButton = page.locator('button', { hasText: '选择创作者' });
    this.selectBenchmarkMaterialButton = page.locator('button', { hasText: '选择对标素材' });
    this.modelAutoSelect = page.locator('.el-radio', { hasText: '自动选择' });
    this.modelManualSelect = page.locator('.el-radio', { hasText: '手动选择' });
    this.dedupSwitch = page.locator('.el-switch').first();
    this.imageDedupSwitch = page.locator('.el-switch').nth(1);
    this.imageCountInput = page.locator('.el-input-number .el-input__inner');
    this.submitButton = page.locator('button', { hasText: /创建|保存/ });
    this.cancelButton = page.locator('button', { hasText: '取消' });
  }

  async goto() {
    await this.page.goto('/scheduled-tasks/create');
    await this.page.waitForLoadState('networkidle');
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectFormVisible() {
    await expect(this.form).toBeVisible();
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async selectTaskType(type: 'custom' | 'benchmark') {
    if (type === 'custom') {
      await this.taskTypeCustom.click();
    } else {
      await this.taskTypeBenchmark.click();
    }
  }

  async selectScheduleType(type: 'daily' | 'weekly') {
    if (type === 'daily') {
      await this.scheduleTypeDaily.click();
    } else {
      await this.scheduleTypeWeekly.click();
    }
  }

  async addTimePoint() {
    await this.addTimePointButton.click();
  }

  async removeTimePoint(index: number) {
    const removeButtons = this.page.locator('.time-point-item .el-button--danger.is-circle');
    if (await removeButtons.count() > index) {
      await removeButtons.nth(index).click();
    }
  }

  async selectWeekday(day: number) {
    const checkbox = this.weekdayCheckboxes.nth(day - 1);
    await checkbox.click();
  }

  async clickSelectTemplate() {
    await this.selectTemplateButton.click();
  }

  async clickSelectSubUser() {
    await this.selectSubUserButton.click();
  }

  async clickSelectBenchmarkMaterial() {
    await this.selectBenchmarkMaterialButton.click();
  }

  async selectModelMode(mode: 'auto' | 'manual') {
    if (mode === 'auto') {
      await this.modelAutoSelect.click();
    } else {
      await this.modelManualSelect.click();
    }
  }

  async toggleDedup(enabled: boolean) {
    const isChecked = await this.dedupSwitch.locator('input').isChecked();
    if (enabled !== isChecked) {
      await this.dedupSwitch.click();
    }
  }

  async toggleImageDedup(enabled: boolean) {
    const isChecked = await this.imageDedupSwitch.locator('input').isChecked();
    if (enabled !== isChecked) {
      await this.imageDedupSwitch.click();
    }
  }

  async setImageCount(count: number) {
    const input = this.page.locator('.el-input-number .el-input__inner');
    await input.clear();
    await input.fill(String(count));
  }

  async submit() {
    await this.submitButton.click();
  }

  async cancel() {
    await this.cancelButton.click();
  }

  async expectValidationErrors() {
    await expect(this.page.locator('.el-form-item__error')).toBeVisible({ timeout: 3000 });
  }

  async expectSubmitSuccess() {
    await expect(this.page.locator('.el-message--success')).toBeVisible({ timeout: 10000 });
  }

  async expectSubmitError() {
    await expect(this.page.locator('.el-message--error')).toBeVisible({ timeout: 10000 });
  }

  async expectRedirectToList() {
    await this.page.waitForURL(/\/scheduled-tasks$/, { timeout: 10000 });
  }

  async expectSectionTitle(title: string) {
    await expect(this.page.locator('.section-title', { hasText: title })).toBeVisible();
  }

  async expectBenchmarkSectionVisible() {
    await expect(this.page.locator('.section-title', { hasText: '对标配置' })).toBeVisible();
  }

  async expectBenchmarkSectionHidden() {
    await expect(this.page.locator('.section-title', { hasText: '对标配置' })).not.toBeVisible();
  }

  async expectBenchmarkMaterialSelectVisible() {
    await expect(this.selectBenchmarkMaterialButton).toBeVisible();
  }

  async expectBenchmarkMaterialSelectHidden() {
    await expect(this.selectBenchmarkMaterialButton).not.toBeVisible();
  }

  async expectModelSelectVisible() {
    await expect(this.page.locator('label', { hasText: '文案模型' })).toBeVisible();
  }

  async expectModelSelectHidden() {
    await expect(this.page.locator('label', { hasText: '文案模型' })).not.toBeVisible();
  }

  async expectDedupThresholdVisible() {
    await expect(this.page.locator('label', { hasText: '文案相似度阈值' })).toBeVisible();
  }

  async expectDedupThresholdHidden() {
    await expect(this.page.locator('label', { hasText: '文案相似度阈值' })).not.toBeVisible();
  }

  async expectImageDedupThresholdVisible() {
    await expect(this.page.locator('label', { hasText: '图片相似度阈值' })).toBeVisible();
  }

  async expectImageDedupThresholdHidden() {
    await expect(this.page.locator('label', { hasText: '图片相似度阈值' })).not.toBeVisible();
  }

  async expectWeeklyFieldsVisible() {
    await expect(this.page.locator('label', { hasText: '执行日期' })).toBeVisible();
  }

  async expectWeeklyFieldsHidden() {
    await expect(this.page.locator('label', { hasText: '执行日期' })).not.toBeVisible();
  }

  async expectDailyTimePickerVisible() {
    await expect(this.page.locator('.time-points-container .el-time-picker').first()).toBeVisible();
  }

  async getTimePointCount(): Promise<number> {
    return await this.page.locator('.time-point-item').count();
  }
}
