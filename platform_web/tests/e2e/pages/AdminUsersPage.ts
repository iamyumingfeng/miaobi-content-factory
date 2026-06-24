import { Page, Locator, expect } from '@playwright/test';

export class AdminUsersPage {
  readonly page: Page;

  // 页面元素
  readonly pageTitle: Locator;
  readonly searchKeywordInput: Locator;
  readonly searchStatusSelect: Locator;
  readonly searchButton: Locator;
  readonly addAdminButton: Locator;
  readonly adminTable: Locator;
  readonly pagination: Locator;
  readonly createDialog: Locator;
  readonly dialogTitle: Locator;
  readonly nicknameInput: Locator;
  readonly displayNameInput: Locator;
  readonly passwordInput: Locator;
  readonly roleSelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // 页面标题和工具栏
    this.pageTitle = page.locator('h2.page-title');
    this.searchKeywordInput = page.locator('input[placeholder*="搜索备注名"]');
    this.searchStatusSelect = page.locator('.el-select').nth(0);
    this.searchButton = page.locator('button', { hasText: '搜索' });
    this.addAdminButton = page.locator('button', { hasText: '新增管理员' });

    // 表格
    this.adminTable = page.locator('.el-table');
    this.pagination = page.locator('.el-pagination');

    // 对话框
    this.createDialog = page.locator('.el-dialog', { hasText: /新增管理员|编辑管理员/ });
    this.dialogTitle = this.createDialog.locator('.el-dialog__title');
    this.nicknameInput = this.createDialog.locator('input[placeholder*="备注名"]');
    this.displayNameInput = this.createDialog.locator('input[placeholder*="自定义昵称"]');
    this.passwordInput = this.createDialog.locator('input[placeholder*="密码"]');
    this.roleSelect = this.createDialog.locator('.el-select', { hasText: '请选择角色' });
    this.submitButton = this.createDialog.locator('button', { hasText: '确定' });
    this.cancelButton = this.createDialog.locator('button', { hasText: '取消' });
  }

  /**
   * 导航到创作管理员页面
   */
  async goto() {
    await this.page.goto('/users/admin');
  }

  /**
   * 验证在创作管理员页面
   */
  async expectOnAdminUsersPage() {
    await expect(this.page).toHaveURL(/\/users\/admin/, { timeout: 10000 });
    await expect(this.pageTitle).toBeVisible({ timeout: 10000 });
  }

  /**
   * 验证页面元素可见
   */
  async expectPageElementsVisible() {
    await expect(this.searchKeywordInput).toBeVisible();
    await expect(this.searchStatusSelect).toBeVisible();
    await expect(this.searchButton).toBeVisible();
    await expect(this.addAdminButton).toBeVisible();
    await expect(this.adminTable).toBeVisible();
  }

  /**
   * 搜索管理员
   */
  async searchAdmins(keyword?: string, status?: string) {
    if (keyword) {
      await this.searchKeywordInput.fill(keyword);
    }
    if (status) {
      await this.searchStatusSelect.click();
      const statusOption = this.page.locator('.el-select-dropdown__item', { hasText: status });
      await statusOption.click();
    }
    await this.searchButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * 清空搜索条件
   */
  async clearSearch() {
    // 直接清空输入框
    await this.searchKeywordInput.fill('');
    // 按 Tab 键来确保失去焦点
    await this.searchKeywordInput.press('Tab');
  }

  /**
   * 点击新增管理员按钮
   */
  async clickAddAdmin() {
    await this.addAdminButton.click();
    await expect(this.createDialog).toBeVisible();
  }

  /**
   * 填写管理员表单
   */
  async fillAdminForm(data: {
    nickname: string;
    displayName?: string;
    password?: string;
    role?: string;
  }) {
    await this.nicknameInput.fill(data.nickname);

    if (data.displayName && await this.displayNameInput.isVisible()) {
      await this.displayNameInput.fill(data.displayName);
    }

    if (data.password && await this.passwordInput.isVisible()) {
      await this.passwordInput.fill(data.password);
    }

    if (data.role && await this.roleSelect.isVisible()) {
      await this.roleSelect.click();
      const roleOption = this.page.locator('.el-select-dropdown__item', { hasText: data.role });
      await roleOption.click();
    }
  }

  /**
   * 提交表单
   */
  async submitForm() {
    await this.submitButton.click();
  }

  /**
   * 取消对话框
   */
  async cancelDialog() {
    await this.cancelButton.click();
    await expect(this.createDialog).toBeHidden();
  }

  /**
   * 获取表格行
   */
  getTableRows() {
    return this.adminTable.locator('.el-table__row');
  }

  /**
   * 获取特定行
   */
  getRowByText(text: string) {
    return this.adminTable.locator('.el-table__row', { hasText: text });
  }

  /**
   * 点击行的编辑按钮
   */
  async clickEditButton(row: Locator) {
    const editButton = row.locator('button', { hasText: '编辑' });
    await editButton.click();
    await expect(this.createDialog).toBeVisible();
  }

  /**
   * 点击行的禁用/启用按钮
   */
  async clickToggleStatusButton(row: Locator) {
    const toggleButton = row.locator('button', { hasText: /禁用|启用/ });
    await toggleButton.click();
  }

  /**
   * 点击行的删除按钮
   */
  async clickDeleteButton(row: Locator) {
    const deleteButton = row.locator('button', { hasText: '删除' });
    await deleteButton.click();
  }

  /**
   * 点击行的重置密码按钮
   */
  async clickResetPasswordButton(row: Locator) {
    const resetButton = row.locator('button', { hasText: '重置密码' });
    await resetButton.click();
  }

  /**
   * 验证成功消息
   */
  async expectSuccessMessage(message: string) {
    const successMessage = this.page.locator('.el-message--success');
    await expect(successMessage).toContainText(message);
  }

  /**
   * 验证确认对话框
   */
  async expectConfirmDialog() {
    const confirmDialog = this.page.locator('.el-message-box');
    await expect(confirmDialog).toBeVisible();
  }

  /**
   * 确认对话框
   */
  async confirmDialog() {
    const confirmButton = this.page.locator('.el-message-box__btns button', { hasText: '确定' });
    await confirmButton.click();
  }

  /**
   * 取消确认对话框
   */
  async cancelConfirmDialog() {
    const cancelButton = this.page.locator('.el-message-box__btns button', { hasText: '取消' });
    await cancelButton.click();
  }

  /**
   * 切换分页
   */
  async goToPage(pageNum: number) {
    const pageButton = this.pagination.locator('.el-pager li', { hasText: pageNum.toString() });
    await pageButton.click();
  }

  /**
   * 验证表格有数据
   */
  async expectTableHasData() {
    const rows = this.getTableRows();
    await expect(rows.first()).toBeVisible();
  }

  /**
   * 验证表格包含特定文本
   */
  async expectTableContains(text: string) {
    await expect(this.adminTable).toContainText(text);
  }

  /**
   * 验证表格不包含特定文本
   */
  async expectTableNotContains(text: string) {
    await expect(this.adminTable).not.toContainText(text);
  }
}
