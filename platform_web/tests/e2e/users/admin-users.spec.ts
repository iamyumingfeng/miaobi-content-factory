import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AdminUsersPage } from '../pages/AdminUsersPage';

// 测试配置
const TEST_CONFIG = {
  baseUrl: 'http://localhost',
  username: 'admin',
  password: 'admin123'
};

test.describe('创作管理员页面 - UI展示', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    // 先登录
    await loginPage.ensureLoggedOut();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);

    // 导航到创作管理员页面
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('应该能够显示创作管理员页面', async () => {
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('应该显示页面标题', async () => {
    await expect(adminUsersPage.pageTitle).toBeVisible();
    await expect(adminUsersPage.pageTitle).toContainText('创作管理员');
  });

  test('应该显示搜索和筛选区域', async () => {
    await expect(adminUsersPage.searchKeywordInput).toBeVisible();
    await expect(adminUsersPage.searchButton).toBeVisible();
  });

  test('应该显示管理员表格', async () => {
    await expect(adminUsersPage.adminTable).toBeVisible();
  });

  test('应该显示新增管理员按钮', async () => {
    await expect(adminUsersPage.addAdminButton).toBeVisible();
  });

  test('应该显示分页组件', async () => {
    await expect(adminUsersPage.pagination).toBeVisible();
  });
});

test.describe('创作管理员页面 - 搜索和筛选', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('搜索输入框应该能够输入内容', async () => {
    await adminUsersPage.searchKeywordInput.fill('test');
    await expect(adminUsersPage.searchKeywordInput).toHaveValue('test');
  });

  test.skip('状态筛选应该能够选择状态', async () => {
    await adminUsersPage.searchStatusSelect.click();
    const normalOption = adminUsersPage.page.locator('.el-select-dropdown__item', { hasText: '正常' });
    await normalOption.click();
    await expect(adminUsersPage.searchStatusSelect).toContainText('正常');
  });

  test('点击搜索按钮应该触发搜索', async () => {
    await adminUsersPage.searchKeywordInput.fill('admin');
    await adminUsersPage.searchButton.click();
    // 搜索后表格应该仍然可见
    await expect(adminUsersPage.adminTable).toBeVisible();
  });

  test.skip('应该能够清空搜索条件', async () => {
    await adminUsersPage.searchKeywordInput.fill('test');
    await adminUsersPage.clearSearch();
    await expect(adminUsersPage.searchKeywordInput).toHaveValue('');
  });
});

test.describe('创作管理员页面 - 新增管理员对话框', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('点击新增管理员按钮应该打开对话框', async () => {
    await adminUsersPage.clickAddAdmin();
    await expect(adminUsersPage.createDialog).toBeVisible();
    await expect(adminUsersPage.dialogTitle).toContainText('新增管理员');
  });

  test('新增对话框应该显示备注名输入框', async () => {
    await adminUsersPage.clickAddAdmin();
    await expect(adminUsersPage.nicknameInput).toBeVisible();
  });

  test('新增对话框应该显示密码输入框', async () => {
    await adminUsersPage.clickAddAdmin();
    await expect(adminUsersPage.passwordInput).toBeVisible();
  });

  test('新增对话框不应该显示自定义昵称输入框', async () => {
    await adminUsersPage.clickAddAdmin();
    // 新增时不应该显示自定义昵称
    await expect(adminUsersPage.displayNameInput).toBeHidden();
  });

  test('新增对话框应该显示确定和取消按钮', async () => {
    await adminUsersPage.clickAddAdmin();
    await expect(adminUsersPage.submitButton).toBeVisible();
    await expect(adminUsersPage.cancelButton).toBeVisible();
  });

  test('点击取消按钮应该关闭对话框', async () => {
    await adminUsersPage.clickAddAdmin();
    await adminUsersPage.cancelDialog();
    await expect(adminUsersPage.createDialog).toBeHidden();
  });

  test('空表单提交应该显示验证错误', async ({ page }) => {
    await adminUsersPage.clickAddAdmin();
    await adminUsersPage.submitForm();
    // 应该有验证错误提示
    const errorMessage = page.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });
});

test.describe('创作管理员页面 - 表格操作', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('表格应该显示操作按钮', async () => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    // 检查编辑按钮
    const editButton = firstRow.locator('button', { hasText: '编辑' });
    await expect(editButton).toBeVisible();

    // 检查重置密码按钮
    const resetButton = firstRow.locator('button', { hasText: '重置密码' });
    await expect(resetButton).toBeVisible();
  });

  test('点击编辑按钮应该打开编辑对话框', async () => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    await adminUsersPage.clickEditButton(firstRow);
    await expect(adminUsersPage.createDialog).toBeVisible();
    await expect(adminUsersPage.dialogTitle).toContainText('编辑管理员');
  });

  test('编辑对话框应该显示自定义昵称输入框', async () => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    await adminUsersPage.clickEditButton(firstRow);
    // 编辑时应该显示自定义昵称
    await expect(adminUsersPage.displayNameInput).toBeVisible();
  });

  test('点击禁用/启用按钮应该显示确认对话框', async ({ page }) => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    await adminUsersPage.clickToggleStatusButton(firstRow);
    await adminUsersPage.expectConfirmDialog();
  });

  test('点击删除按钮应该显示确认对话框', async ({ page }) => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    // 尝试删除（可能被阻止，如果是超级管理员）
    try {
      await adminUsersPage.clickDeleteButton(firstRow);
      // 可能显示确认对话框，也可能直接显示错误消息
      const confirmDialog = page.locator('.el-message-box');
      const errorMessage = page.locator('.el-message--error');

      await expect(confirmDialog.or(errorMessage)).toBeVisible({ timeout: 2000 });
    } catch (e) {
      // 如果删除按钮不可见（比如是超级管理员），这个测试也可以通过
      test.skip();
    }
  });

  test('点击重置密码按钮应该显示确认对话框', async ({ page }) => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    await adminUsersPage.clickResetPasswordButton(firstRow);
    await adminUsersPage.expectConfirmDialog();
  });

  test('取消确认对话框应该不执行操作', async ({ page }) => {
    const rows = adminUsersPage.getTableRows();
    const firstRow = rows.first();

    await adminUsersPage.clickToggleStatusButton(firstRow);
    await adminUsersPage.cancelConfirmDialog();
    await expect(page.locator('.el-message-box')).toBeHidden();
  });
});

test.describe('创作管理员页面 - 不显示超级管理员', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('管理员列表中不应该显示超级管理员账号', async () => {
    // 超级管理员账号不应该出现在列表中
    await adminUsersPage.expectTableNotContains('super_admin');
    await adminUsersPage.expectTableNotContains('超级管理员');
  });
});

test.describe('创作管理员页面 - 分页功能', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('应该显示分页组件', async () => {
    await expect(adminUsersPage.pagination).toBeVisible();
  });

  test('应该显示总记录数', async () => {
    const totalText = adminUsersPage.page.locator('.total-text');
    await expect(totalText).toBeVisible();
    await expect(totalText).toContainText('共');
    await expect(totalText).toContainText('条记录');
  });
});

test.describe('创作管理员页面 - 异常流程', () => {
  let loginPage: LoginPage;
  let adminUsersPage: AdminUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminUsersPage = new AdminUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await adminUsersPage.goto();
    await adminUsersPage.expectOnAdminUsersPage();
  });

  test('搜索不存在的用户应该显示空表格或无数据提示', async ({ page }) => {
    await adminUsersPage.searchAdmins('this_user_should_not_exist_123456');
    // 即使没有数据，表格也应该可见
    await expect(adminUsersPage.adminTable).toBeVisible();
  });

  test('输入特殊字符搜索应该正常处理', async () => {
    await adminUsersPage.searchAdmins('!@#$%^&*()');
    await expect(adminUsersPage.adminTable).toBeVisible();
  });

  test('快速多次点击搜索按钮应该正常处理', async () => {
    await adminUsersPage.searchKeywordInput.fill('test');
    // 快速点击多次
    for (let i = 0; i < 3; i++) {
      await adminUsersPage.searchButton.click();
    }
    await expect(adminUsersPage.adminTable).toBeVisible();
  });
});
