import { test, expect } from '@playwright/test';
import { ScheduledTaskListPage } from '../pages/ScheduledTaskListPage';
import { LoginPage } from '../pages/LoginPage';

// 登录辅助函数
async function loginAsAdmin(page: any) {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  // 尝试登录，如果已经登录会自动跳转
  try {
    await loginPage.loginWithPassword('admin', 'admin123');
  } catch {
    // 可能已经登录
  }
}

test.describe('定时任务列表页 UI', () => {
  let taskListPage: ScheduledTaskListPage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    taskListPage = new ScheduledTaskListPage(page);
    await taskListPage.goto();
  });

  test('应该能够正常加载定时任务列表页', async () => {
    await taskListPage.expectPageTitleVisible();
    await taskListPage.expectCreateButtonVisible();
  });

  test('应该显示页面标题"定时任务管理"', async ({ page }) => {
    await expect(page.locator('.page-title', { hasText: '定时任务管理' })).toBeVisible();
  });

  test('应该显示创建任务按钮', async () => {
    await taskListPage.expectCreateButtonVisible();
  });

  test('应该显示搜索栏', async ({ page }) => {
    await expect(page.locator('input[placeholder*="搜索任务名称"]')).toBeVisible();
  });

  test('应该显示状态筛选下拉框', async ({ page }) => {
    await expect(page.locator('input[placeholder*="任务状态"]')).toBeVisible();
  });

  test('应该显示任务类型筛选下拉框', async ({ page }) => {
    await expect(page.locator('input[placeholder*="任务类型"]')).toBeVisible();
  });

  test('应该显示搜索按钮', async ({ page }) => {
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();
  });

  test('应该显示任务列表表格', async () => {
    await taskListPage.expectTableVisible();
  });

  test('表格应该包含正确的列标题', async ({ page }) => {
    const expectedHeaders = ['任务名称', '任务类型', '调度配置', '下次执行时间', '执行统计', '创建时间', '操作'];
    for (const header of expectedHeaders) {
      await expect(page.locator('.el-table__header th', { hasText: header })).toBeVisible();
    }
  });

  test('应该显示分页组件', async () => {
    await taskListPage.expectPaginationVisible();
  });
});

test.describe('定时任务列表页 - 搜索和筛选', () => {
  let taskListPage: ScheduledTaskListPage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    taskListPage = new ScheduledTaskListPage(page);
    await taskListPage.goto();
  });

  test('搜索输入框应该能够输入内容', async ({ page }) => {
    await taskListPage.searchInput.fill('测试任务');
    await expect(taskListPage.searchInput).toHaveValue('测试任务');
  });

  test('搜索输入框应该支持清空', async ({ page }) => {
    await taskListPage.searchInput.fill('测试任务');
    const clearBtn = page.locator('.el-input__clear');
    if (await clearBtn.isVisible()) {
      await clearBtn.click();
      await expect(taskListPage.searchInput).toHaveValue('');
    }
  });

  test('按回车应该触发搜索', async ({ page }) => {
    await taskListPage.searchInput.fill('测试');
    await taskListPage.searchInput.press('Enter');
    await page.waitForLoadState('networkidle');
  });

  test('点击搜索按钮应该触发搜索', async () => {
    await taskListPage.searchByKeyword('测试');
  });

  test('状态筛选下拉框应该显示选项', async ({ page }) => {
    await taskListPage.statusSelect.click();
    const options = ['全部', '已启用', '已暂停', '已禁用'];
    for (const option of options) {
      await expect(page.locator('.el-select-dropdown__item', { hasText: option })).toBeVisible();
    }
  });

  test('任务类型筛选下拉框应该显示选项', async ({ page }) => {
    await taskListPage.taskTypeSelect.click();
    const options = ['全部', '自定义文案', '对标文案'];
    for (const option of options) {
      await expect(page.locator('.el-select-dropdown__item', { hasText: option })).toBeVisible();
    }
  });
});

test.describe('定时任务列表页 - 操作按钮', () => {
  let taskListPage: ScheduledTaskListPage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    taskListPage = new ScheduledTaskListPage(page);
    await taskListPage.goto();
  });

  test('点击创建任务按钮应该跳转到创建页面', async ({ page }) => {
    await taskListPage.clickCreateButton();
    await expect(page).toHaveURL(/\/scheduled-tasks\/create/);
  });

  test('如果列表有数据，每行应该显示操作按钮', async () => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      await expect(firstRow.locator('button', { hasText: '查看' })).toBeVisible();
      await expect(firstRow.locator('button', { hasText: '编辑' })).toBeVisible();
      await expect(firstRow.locator('button', { hasText: /禁用|启用/ })).toBeVisible();
      await expect(firstRow.locator('button', { hasText: '执行' })).toBeVisible();
      await expect(firstRow.locator('button', { hasText: '删除' })).toBeVisible();
    }
  });

  test('点击查看按钮应该跳转到详情页', async ({ page }) => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      await taskListPage.clickViewButton(0);
      await expect(page).toHaveURL(/\/scheduled-tasks\/\d+/);
    }
  });

  test('点击编辑按钮应该跳转到编辑页', async ({ page }) => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      await taskListPage.clickEditButton(0);
      await expect(page).toHaveURL(/\/scheduled-tasks\/edit\/\d+/);
    }
  });

  test('点击删除按钮应该弹出确认对话框', async ({ page }) => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      await taskListPage.clickDeleteButton(0);
      await expect(page.locator('.el-message-box')).toBeVisible();
      await taskListPage.cancelDialog();
    }
  });

  test('点击禁用/启用按钮应该弹出确认对话框', async ({ page }) => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      await taskListPage.clickToggleButton(0);
      await expect(page.locator('.el-message-box')).toBeVisible();
      await taskListPage.cancelDialog();
    }
  });

  test('点击执行按钮应该弹出确认对话框', async ({ page }) => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      const executeBtn = firstRow.locator('button', { hasText: '执行' });
      if (await executeBtn.isEnabled()) {
        await taskListPage.clickExecuteButton(0);
        await expect(page.locator('.el-message-box')).toBeVisible();
        await taskListPage.cancelDialog();
      }
    }
  });
});

test.describe('定时任务列表页 - 分页', () => {
  let taskListPage: ScheduledTaskListPage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    taskListPage = new ScheduledTaskListPage(page);
    await taskListPage.goto();
  });

  test('分页组件应该显示总数', async ({ page }) => {
    const totalText = page.locator('.el-pagination__total');
    await expect(totalText).toBeVisible();
  });

  test('分页组件应该显示页码选择器', async ({ page }) => {
    await expect(page.locator('.el-pager')).toBeVisible();
  });

  test('分页组件应该显示每页条数选择器', async ({ page }) => {
    await expect(page.locator('.el-pagination__sizes')).toBeVisible();
  });
});

test.describe('定时任务列表页 - 数据展示', () => {
  let taskListPage: ScheduledTaskListPage;

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    taskListPage = new ScheduledTaskListPage(page);
    await taskListPage.goto();
  });

  test('任务名称列应该显示名称和状态标签', async () => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      await expect(firstRow.locator('.name-text')).toBeVisible();
      await expect(firstRow.locator('.el-tag').first()).toBeVisible();
    }
  });

  test('任务类型列应该显示类型标签', async () => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      const typeTag = firstRow.locator('.el-table__cell').nth(1).locator('.el-tag');
      await expect(typeTag).toBeVisible();
    }
  });

  test('调度配置列应该显示调度信息', async () => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      await expect(firstRow.locator('.schedule-info')).toBeVisible();
    }
  });

  test('执行统计列应该显示统计数据', async () => {
    const rowCount = await taskListPage.getTableRowCount();
    if (rowCount > 0) {
      const firstRow = taskListPage.tableRows.first();
      await expect(firstRow.locator('.execution-stats')).toBeVisible();
    }
  });
});
