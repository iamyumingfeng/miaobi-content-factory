import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { SubUsersPage } from '../pages/SubUsersPage';

// 测试配置
const TEST_CONFIG = {
  baseUrl: 'http://localhost',
  username: 'admin',
  password: 'admin123'
};

test.describe('创作员管理页面 - UI展示', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    // 先登录
    await loginPage.goto();
    await loginPage.loginWithPassword(TEST_CONFIG.username, TEST_CONFIG.password);

    // 导航到创作员管理页面
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('应该能够显示创作员管理页面', async () => {
    await subUsersPage.expectOnSubUsersPage();
  });

  test('应该显示页面标题', async () => {
    await expect(subUsersPage.pageTitle).toBeVisible();
    await expect(subUsersPage.pageTitle).toContainText('创作员管理');
  });

  test('应该显示左侧标签面板', async () => {
    await expect(subUsersPage.categoryPanel).toBeVisible();
  });

  test('应该显示"全部"标签项', async () => {
    await expect(subUsersPage.allTagItem).toBeVisible();
    await expect(subUsersPage.allTagItem).toContainText('全部');
  });

  test('应该显示新增标签按钮', async () => {
    await expect(subUsersPage.addTagButton).toBeVisible();
    await expect(subUsersPage.addTagButton).toContainText('新增标签');
  });

  test('应该显示搜索和筛选区域', async () => {
    await expect(subUsersPage.searchKeywordInput).toBeVisible();
    await expect(subUsersPage.searchStatusSelect).toBeVisible();
    await expect(subUsersPage.searchButton).toBeVisible();
  });

  test('应该显示创建用户按钮', async () => {
    await expect(subUsersPage.createUserButton).toBeVisible();
    await expect(subUsersPage.createUserButton).toContainText('创建用户');
  });

  test('应该显示批量删除按钮', async () => {
    await expect(subUsersPage.batchDeleteButton).toBeVisible();
    await expect(subUsersPage.batchDeleteButton).toContainText('批量删除');
  });

  test('应该显示创作者表格', async () => {
    await expect(subUsersPage.userTable).toBeVisible();
  });

  test('应该显示分页组件', async () => {
    await expect(subUsersPage.pagination).toBeVisible();
  });
});

test.describe('创作员管理页面 - 标签功能', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('点击"全部"标签应该显示所有用户', async () => {
    await subUsersPage.clickTag(null);
    await expect(subUsersPage.allTagItem).toHaveClass(/active/);
  });

  test('每个标签应该显示对应的用户数量', async () => {
    // 检查"全部"标签有数量显示
    const allTagCount = subUsersPage.allTagItem.locator('.category-count');
    await expect(allTagCount).toBeVisible();
    await expect(allTagCount).toContainText(/\(\d+\)/);
  });

  test('点击新增标签按钮应该打开标签对话框', async () => {
    await subUsersPage.clickAddTag();
    await expect(subUsersPage.tagDialog).toBeVisible();
  });

  test('标签对话框应该显示标签名称输入框', async () => {
    await subUsersPage.clickAddTag();
    await expect(subUsersPage.tagNameInput).toBeVisible();
  });
});

test.describe('创作员管理页面 - 搜索和筛选', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('搜索输入框应该能够输入内容', async () => {
    await subUsersPage.searchKeywordInput.fill('test');
    await expect(subUsersPage.searchKeywordInput).toHaveValue('test');
  });

  test.skip('状态筛选应该能够选择状态', async () => {
    await subUsersPage.searchStatusSelect.click();
    const normalOption = subUsersPage.page.locator('.el-select-dropdown__item', { hasText: '正常' });
    await normalOption.click();
    await expect(subUsersPage.searchStatusSelect).toContainText('正常');
  });

  test('点击搜索按钮应该触发搜索', async () => {
    await subUsersPage.searchKeywordInput.fill('user');
    await subUsersPage.searchButton.click();
    await expect(subUsersPage.userTable).toBeVisible();
  });

  test.skip('应该能够清空搜索条件', async () => {
    await subUsersPage.searchKeywordInput.fill('test');
    await subUsersPage.clearSearch();
    await expect(subUsersPage.searchKeywordInput).toHaveValue('');
  });
});

test.describe('创作员管理页面 - 创建用户对话框', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('点击创建用户按钮应该打开对话框', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.createDialog).toBeVisible();
  });

  test('创建对话框应该显示备注名输入框', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.nicknameInput).toBeVisible();
  });

  test('创建对话框应该显示密码输入框', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.passwordInput).toBeVisible();
  });

  test('创建对话框应该显示账号定位输入框', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.userPositioningInput).toBeVisible();
  });

  test('创建对话框应该显示内容风格输入框', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.contentStyleInput).toBeVisible();
  });

  test('创建对话框应该显示用户标签选择', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.tagSelect).toBeVisible();
  });

  test('创建对话框不应该显示自定义昵称输入框', async () => {
    await subUsersPage.clickCreateUser();
    await subUsersPage.expectCreateDialogNoDisplayName();
  });

  test('创建对话框应该显示确定和取消按钮', async () => {
    await subUsersPage.clickCreateUser();
    await expect(subUsersPage.submitButton).toBeVisible();
    await expect(subUsersPage.cancelButton).toBeVisible();
  });

  test('点击取消按钮应该关闭对话框', async () => {
    await subUsersPage.clickCreateUser();
    await subUsersPage.cancelUserForm();
    await expect(subUsersPage.createDialog).toBeHidden();
  });

  test('空表单提交应该显示验证错误', async ({ page }) => {
    await subUsersPage.clickCreateUser();
    await subUsersPage.submitUserForm();
    const errorMessage = page.locator('.el-form-item__error');
    await expect(errorMessage.first()).toBeVisible({ timeout: 2000 });
  });
});

test.describe('创作员管理页面 - 表格操作', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test.skip('表格应该显示复选框列', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();
    const checkbox = firstRow.locator('.el-checkbox');
    await expect(checkbox).toBeVisible();
  });

  test.skip('应该能够选择表格行', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();
    await subUsersPage.selectRow(firstRow);
    const checkbox = firstRow.locator('.el-checkbox');
    await expect(checkbox).toHaveClass(/is-checked/);
  });

  test.skip('表格应该显示操作按钮', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    const editButton = firstRow.locator('button', { hasText: '编辑' });
    await expect(editButton).toBeVisible();

    const resetButton = firstRow.locator('button', { hasText: '重置密码' });
    await expect(resetButton).toBeVisible();

    const toggleButton = firstRow.locator('button', { hasText: /禁用|启用/ });
    await expect(toggleButton).toBeVisible();

    const deleteButton = firstRow.locator('button', { hasText: '删除' });
    await expect(deleteButton).toBeVisible();
  });

  test.skip('点击编辑按钮应该打开编辑对话框', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickEditButton(firstRow);
    await expect(subUsersPage.createDialog).toBeVisible();
  });

  test.skip('编辑对话框应该显示自定义昵称输入框', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickEditButton(firstRow);
    await subUsersPage.expectEditDialogHasDisplayName();
  });

  test.skip('点击禁用/启用按钮应该显示确认对话框', async ({ page }) => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickToggleStatusButton(firstRow);
    await subUsersPage.expectConfirmDialog();
  });

  test.skip('点击删除按钮应该显示确认对话框', async ({ page }) => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickDeleteButton(firstRow);
    await subUsersPage.expectConfirmDialog();
  });

  test.skip('点击重置密码按钮应该显示确认对话框', async ({ page }) => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickResetPasswordButton(firstRow);
    await subUsersPage.expectConfirmDialog();
  });

  test.skip('取消确认对话框应该不执行操作', async ({ page }) => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.clickToggleStatusButton(firstRow);
    await subUsersPage.cancelConfirmDialog();
    await expect(page.locator('.el-message-box')).toBeHidden();
  });

  test.skip('选中用户后批量删除按钮应该可用', async () => {
    const rows = subUsersPage.getTableRows();
    const firstRow = rows.first();

    await subUsersPage.selectRow(firstRow);
    await expect(subUsersPage.batchDeleteButton).toBeEnabled();
  });
});

test.describe('创作员管理页面 - 分页功能', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('应该显示分页组件', async () => {
    await expect(subUsersPage.pagination).toBeVisible();
  });

  test('应该显示总记录数', async () => {
    const totalText = subUsersPage.page.locator('.total-text');
    await expect(totalText).toBeVisible();
    await expect(totalText).toContainText('共');
    await expect(totalText).toContainText('条记录');
  });
});

test.describe('创作员管理页面 - 异常流程', () => {
  let loginPage: LoginPage;
  let subUsersPage: SubUsersPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    subUsersPage = new SubUsersPage(page);

    await loginPage.goto();
    await loginPage.loginWithPassword('admin', 'admin123');
    await subUsersPage.goto();
    await subUsersPage.expectOnSubUsersPage();
  });

  test('搜索不存在的用户应该正常处理', async ({ page }) => {
    await subUsersPage.searchUsers('this_user_should_not_exist_123456');
    await expect(subUsersPage.userTable).toBeVisible();
  });

  test('输入特殊字符搜索应该正常处理', async () => {
    await subUsersPage.searchUsers('!@#$%^&*()');
    await expect(subUsersPage.userTable).toBeVisible();
  });

  test('快速多次点击搜索按钮应该正常处理', async () => {
    await subUsersPage.searchKeywordInput.fill('test');
    for (let i = 0; i < 3; i++) {
      await subUsersPage.searchButton.click();
    }
    await expect(subUsersPage.userTable).toBeVisible();
  });
});
