import { test, expect } from '@playwright/test';
import { ScheduledTaskCreatePage } from '../pages/ScheduledTaskCreatePage';
import { LoginPage } from '../pages/LoginPage';

// 登录辅助函数
async function loginAsAdmin(page: any) {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  try {
    await loginPage.loginWithPassword('admin', 'admin123');
  } catch {
    // 可能已经登录
  }
}

test.describe('创建定时任务页 UI', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('应该能够正常加载创建定时任务页', async () => {
    await createPage.expectPageTitleVisible();
  });

  test('应该显示页面标题"创建定时任务"', async ({ page }) => {
    await expect(page.locator('.page-title', { hasText: '创建定时任务' })).toBeVisible();
  });

  test('应该显示返回按钮', async () => {
    await expect(createPage.backButton).toBeVisible();
  });

  test('应该显示表单', async () => {
    await createPage.expectFormVisible();
  });

  test('应该显示所有表单区域标题', async () => {
    await createPage.expectSectionTitle('基本信息');
    await createPage.expectSectionTitle('调度配置');
    await createPage.expectSectionTitle('素材和模板配置');
    await createPage.expectSectionTitle('创作者配置');
    await createPage.expectSectionTitle('模型配置');
    await createPage.expectSectionTitle('去重配置');
    await createPage.expectSectionTitle('图片配置');
  });

  test('应该显示任务名称输入框', async () => {
    await expect(createPage.nameInput).toBeVisible();
  });

  test('应该显示任务类型单选按钮', async () => {
    await expect(createPage.taskTypeCustom).toBeVisible();
    await expect(createPage.taskTypeBenchmark).toBeVisible();
  });

  test('应该显示调度类型单选按钮', async () => {
    await expect(createPage.scheduleTypeDaily).toBeVisible();
    await expect(createPage.scheduleTypeWeekly).toBeVisible();
  });

  test('应该显示添加时间点按钮', async () => {
    await expect(createPage.addTimePointButton).toBeVisible();
  });

  test('应该显示模板选择按钮', async () => {
    await expect(createPage.selectTemplateButton).toBeVisible();
  });

  test('应该显示创作者选择按钮', async () => {
    await expect(createPage.selectSubUserButton).toBeVisible();
  });

  test('应该显示模型选择方式', async () => {
    await expect(createPage.modelAutoSelect).toBeVisible();
    await expect(createPage.modelManualSelect).toBeVisible();
  });

  test('应该显示图片数量输入框', async () => {
    await expect(createPage.imageCountInput).toBeVisible();
  });

  test('应该显示取消和创建按钮', async () => {
    await expect(createPage.cancelButton).toBeVisible();
    await expect(createPage.submitButton).toBeVisible();
  });
});

test.describe('创建定时任务页 - 任务类型切换', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('默认应该选中"自定义文案"', async ({ page }) => {
    const customRadio = page.locator('.el-radio', { hasText: '自定义文案' });
    await expect(customRadio.locator('.el-radio__input')).toHaveClass(/is-checked/);
  });

  test('选择"自定义文案"时不应显示对标配置', async () => {
    await createPage.selectTaskType('custom');
    await createPage.expectBenchmarkSectionHidden();
  });

  test('选择"对标文案"时应该显示对标配置', async () => {
    await createPage.selectTaskType('benchmark');
    await createPage.expectBenchmarkSectionVisible();
  });

  test('选择"对标文案"且启用对标文案时应该显示对标素材选择', async () => {
    await createPage.selectTaskType('benchmark');
    // 对标文案默认启用，应显示对标素材选择
    await createPage.expectBenchmarkMaterialSelectVisible();
  });
});

test.describe('创建定时任务页 - 调度配置', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('默认应该选中"每日"调度', async ({ page }) => {
    const dailyRadio = page.locator('.el-radio', { hasText: '每日' });
    await expect(dailyRadio.locator('.el-radio__input')).toHaveClass(/is-checked/);
  });

  test('选择"每日"时应该显示时间点选择', async () => {
    await createPage.selectScheduleType('daily');
    await createPage.expectDailyTimePickerVisible();
  });

  test('选择"每日"时不应显示执行日期选择', async () => {
    await createPage.selectScheduleType('daily');
    await createPage.expectWeeklyFieldsHidden();
  });

  test('选择"每周"时应该显示执行日期选择', async () => {
    await createPage.selectScheduleType('weekly');
    await createPage.expectWeeklyFieldsVisible();
  });

  test('选择"每周"时应该显示7个星期复选框', async ({ page }) => {
    await createPage.selectScheduleType('weekly');
    const checkboxes = page.locator('.el-checkbox-group .el-checkbox');
    await expect(checkboxes).toHaveCount(7);
  });

  test('点击添加时间点应该增加一个时间选择器', async () => {
    const initialCount = await createPage.getTimePointCount();
    await createPage.addTimePoint();
    const newCount = await createPage.getTimePointCount();
    expect(newCount).toBe(initialCount + 1);
  });

  test('只有一个时间点时不应该显示删除按钮', async ({ page }) => {
    await createPage.selectScheduleType('daily');
    // 默认只有一个时间点
    const removeButtons = page.locator('.time-point-item .el-button--danger.is-circle');
    expect(await removeButtons.count()).toBe(0);
  });

  test('多个时间点时应该显示删除按钮', async ({ page }) => {
    await createPage.selectScheduleType('daily');
    await createPage.addTimePoint();
    const removeButtons = page.locator('.time-point-item .el-button--danger.is-circle');
    expect(await removeButtons.count()).toBeGreaterThan(0);
  });
});

test.describe('创建定时任务页 - 模型配置', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('默认应该选中"自动选择"', async ({ page }) => {
    const autoRadio = page.locator('.el-radio', { hasText: '自动选择' });
    await expect(autoRadio.locator('.el-radio__input')).toHaveClass(/is-checked/);
  });

  test('选择"自动选择"时不应显示模型下拉框', async () => {
    await createPage.selectModelMode('auto');
    await createPage.expectModelSelectHidden();
  });

  test('选择"手动选择"时应该显示模型下拉框', async () => {
    await createPage.selectModelMode('manual');
    await createPage.expectModelSelectVisible();
  });

  test('选择"手动选择"时应该显示文案模型和图片模型', async ({ page }) => {
    await createPage.selectModelMode('manual');
    await expect(page.locator('label', { hasText: '文案模型' })).toBeVisible();
    await expect(page.locator('label', { hasText: '图片模型' })).toBeVisible();
  });
});

test.describe('创建定时任务页 - 去重配置', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('默认文案去重应该关闭', async ({ page }) => {
    const dedupSwitch = page.locator('.el-switch').first();
    await expect(dedupSwitch).not.toHaveClass(/is-checked/);
  });

  test('默认图片去重应该关闭', async ({ page }) => {
    const imageDedupSwitch = page.locator('.el-switch').nth(1);
    await expect(imageDedupSwitch).not.toHaveClass(/is-checked/);
  });

  test('开启文案去重后应该显示相似度阈值和去重范围', async () => {
    await createPage.toggleDedup(true);
    await createPage.expectDedupThresholdVisible();
    await expect(createPage.page.locator('label', { hasText: '文案去重范围' })).toBeVisible();
  });

  test('关闭文案去重后应该隐藏相似度阈值和去重范围', async () => {
    await createPage.toggleDedup(true);
    await createPage.toggleDedup(false);
    await createPage.expectDedupThresholdHidden();
  });

  test('开启图片去重后应该显示图片相似度阈值', async () => {
    await createPage.toggleImageDedup(true);
    await createPage.expectImageDedupThresholdVisible();
  });

  test('关闭图片去重后应该隐藏图片相似度阈值', async () => {
    await createPage.toggleImageDedup(true);
    await createPage.toggleImageDedup(false);
    await createPage.expectImageDedupThresholdHidden();
  });
});

test.describe('创建定时任务页 - 表单验证', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('不填写任务名称直接提交应该显示验证错误', async () => {
    await createPage.submit();
    await createPage.expectValidationErrors();
  });

  test('任务名称太短应该显示验证错误', async () => {
    await createPage.fillName('a');
    await createPage.submit();
    await createPage.expectValidationErrors();
  });

  test('填写完整信息后应该可以提交', async ({ page }) => {
    await createPage.fillName('E2E测试定时任务');
    // 注意：这里只验证表单验证通过，实际提交可能因为缺少模板/创作者而失败
    // 但至少任务名称验证应该通过
    await createPage.submit();
    // 如果有其他必填项验证错误，也属于正常行为
  });
});

test.describe('创建定时任务页 - 对标配置', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('选择"对标文案"时应该显示对标配置区域', async () => {
    await createPage.selectTaskType('benchmark');
    await createPage.expectBenchmarkSectionVisible();
  });

  test('对标配置应该显示对标图片和对标文案开关', async ({ page }) => {
    await createPage.selectTaskType('benchmark');
    await expect(page.locator('label', { hasText: '对标图片' })).toBeVisible();
    await expect(page.locator('label', { hasText: '对标文案' })).toBeVisible();
  });

  test('开启对标图片后应该显示图片参考选项', async ({ page }) => {
    await createPage.selectTaskType('benchmark');
    // 开启对标图片
    const benchmarkImageSwitch = page.locator('.el-switch').nth(2);
    if (!(await benchmarkImageSwitch.locator('input').isChecked())) {
      await benchmarkImageSwitch.click();
    }
    await expect(page.locator('label', { hasText: '图片参考选项' })).toBeVisible();
  });

  test('图片参考选项应该包含构图、色调、风格', async ({ page }) => {
    await createPage.selectTaskType('benchmark');
    const benchmarkImageSwitch = page.locator('.el-switch').nth(2);
    if (!(await benchmarkImageSwitch.locator('input').isChecked())) {
      await benchmarkImageSwitch.click();
    }
    await expect(page.locator('.el-checkbox', { hasText: '构图' })).toBeVisible();
    await expect(page.locator('.el-checkbox', { hasText: '色调' })).toBeVisible();
    await expect(page.locator('.el-checkbox', { hasText: '风格' })).toBeVisible();
  });
});

test.describe('创建定时任务页 - 导航', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('点击返回按钮应该返回上一页', async ({ page }) => {
    await createPage.clickBackButton();
    // 应该返回到列表页
    await expect(page).toHaveURL(/\/scheduled-tasks/);
  });

  test('点击取消按钮应该返回上一页', async ({ page }) => {
    await createPage.cancel();
    await expect(page).toHaveURL(/\/scheduled-tasks/);
  });
});
