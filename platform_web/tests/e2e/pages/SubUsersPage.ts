import { Page, Locator, expect } from '@playwright/test';

export class SubUsersPage {
  readonly page: Page;

  // 页面元素
  readonly pageTitle: Locator;
  readonly categoryPanel: Locator;
  readonly userTable: Locator;
  readonly pagination: Locator;

  // 搜索和筛选
  readonly searchKeywordInput: Locator;
  readonly searchStatusSelect: Locator;
  readonly searchButton: Locator;
  readonly createUserButton: Locator;
  readonly batchDeleteButton: Locator;
  readonly batchTransferButton: Locator;

  // 创作管理员筛选（超级管理员）
  readonly operatorFilterSelect: Locator;

  // 标签相关
  readonly addTagButton: Locator;
  readonly tagList: Locator;
  readonly allTagItem: Locator;

  // 创建/编辑对话框
  readonly createDialog: Locator;
  readonly nicknameInput: Locator;
  readonly passwordInput: Locator;
  readonly userPositioningInput: Locator;
  readonly contentStyleInput: Locator;
  readonly tagSelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  // 标签对话框
  readonly tagDialog: Locator;
  readonly tagNameInput: Locator;
  readonly tagColorInput: Locator;
  readonly tagDescriptionInput: Locator;

  // 批量转移对话框
  readonly transferDialog: Locator;
  readonly transferTargetOperatorSelect: Locator;

  constructor(page: Page) {
    this.page = page;

    // 页面标题
    this.pageTitle = page.locator('h2.page-title');

    // 左侧标签面板
    this.categoryPanel = page.locator('.category-panel');
    this.addTagButton = this.categoryPanel.locator('button', { hasText: '新增标签' });
    this.tagList = this.categoryPanel.locator('.category-list');
    this.allTagItem = this.tagList.locator('.category-item', { hasText: '全部' });

    // 搜索和工具栏
    this.searchKeywordInput = page.locator('input[placeholder*="搜索备注名"]');
    this.searchStatusSelect = page.locator('.el-select').nth(0);
    this.searchButton = page.locator('button', { hasText: '搜索' });
    this.createUserButton = page.locator('button', { hasText: '创建用户' });
    this.batchDeleteButton = page.locator('button', { hasText: '批量删除' });
    this.batchTransferButton = page.locator('button', { hasText: '批量转移' });

    // 创作管理员筛选（超级管理员）
    this.operatorFilterSelect = page.locator('.el-select').nth(1);

    // 表格
    this.userTable = page.locator('.el-table');
    this.pagination = page.locator('.el-pagination');

    // 创建/编辑用户对话框
    this.createDialog = page.locator('.el-dialog', { hasText: /创建用户|编辑用户/ });
    this.nicknameInput = this.createDialog.locator('input[placeholder*="备注名"]');
    this.passwordInput = this.createDialog.locator('input[placeholder*="留空则自动生成"]');
    this.userPositioningInput = this.createDialog.locator('input[placeholder*="账号定位"]');
    this.contentStyleInput = this.createDialog.locator('input[placeholder*="内容风格"]');
    this.tagSelect = this.createDialog.locator('.el-select', { hasText: '请选择标签' });
    this.submitButton = this.createDialog.locator('button', { hasText: '确定' });
    this.cancelButton = this.createDialog.locator('button', { hasText: '取消' });

    // 标签对话框
    this.tagDialog = page.locator('.el-dialog', { hasText: /新增标签|编辑标签/ });
    this.tagNameInput = this.tagDialog.locator('input[placeholder*="标签名称"]');
    this.tagColorInput = this.tagDialog.locator('input[placeholder*="标签颜色"]');
    this.tagDescriptionInput = this.tagDialog.locator('textarea[placeholder*="描述"]');

    // 批量转移对话框
    this.transferDialog = page.locator('.el-dialog', { hasText: '批量转移用户' });
    this.transferTargetOperatorSelect = this.transferDialog.locator('.el-select', { hasText: '请选择目标创作管理员' });
  }

  /**
   * 导航到创作员管理页面
   */
  async goto() {
    await this.page.goto('/users/sub');
  }

  /**
   * 验证在创作员管理页面
   */
  async expectOnSubUsersPage() {
    await expect(this.page).toHaveURL(/\/users\/sub/, { timeout: 10000 });
    await expect(this.pageTitle).toBeVisible({ timeout: 10000 });
  }

  /**
   * 验证页面元素可见
   */
  async expectPageElementsVisible() {
    await expect(this.categoryPanel).toBeVisible();
    await expect(this.searchKeywordInput).toBeVisible();
    await expect(this.searchStatusSelect).toBeVisible();
    await expect(this.searchButton).toBeVisible();
    await expect(this.createUserButton).toBeVisible();
    await expect(this.userTable).toBeVisible();
  }

  /**
   * 点击标签
   */
  async clickTag(tagName: string | null) {
    if (tagName === null) {
      await this.allTagItem.click();
    } else {
      const tagItem = this.tagList.locator('.category-item', { hasText: tagName });
      await tagItem.click();
    }
    await this.page.waitForTimeout(300);
  }

  /**
   * 获取标签计数
   */
  async getTagCount(tagName: string): Promise<number> {
    const tagItem = this.tagList.locator('.category-item', { hasText: tagName });
    const countText = await tagItem.locator('.category-count').textContent();
    if (!countText) return 0;
    const match = countText.match(/\((\d+)\)/);
    return match ? parseInt(match[1]) : 0;
  }

  /**
   * 搜索创作者
   */
  async searchUsers(keyword?: string, status?: string) {
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
   * 清空搜索
   */
  async clearSearch() {
    const clearIcon = this.searchKeywordInput.locator('.el-input__clear');
    if (await clearIcon.isVisible()) {
      await clearIcon.click();
    }
    await this.searchStatusSelect.click();
    const allOption = this.page.locator('.el-select-dropdown__item', { hasText: '全部' });
    if (await allOption.isVisible()) {
      await allOption.click();
    }
  }

  /**
   * 点击创建用户
   */
  async clickCreateUser() {
    await this.createUserButton.click();
    await expect(this.createDialog).toBeVisible();
  }

  /**
   * 填写用户表单
   */
  async fillUserForm(data: {
    nickname: string;
    password?: string;
    userPositioning?: string;
    contentStyle?: string;
    tagIds?: number[];
  }) {
    await this.nicknameInput.fill(data.nickname);

    if (data.password && await this.passwordInput.isVisible()) {
      await this.passwordInput.fill(data.password);
    }

    if (data.userPositioning && await this.userPositioningInput.isVisible()) {
      await this.userPositioningInput.fill(data.userPositioning);
    }

    if (data.contentStyle && await this.contentStyleInput.isVisible()) {
      await this.contentStyleInput.fill(data.contentStyle);
    }

    if (data.tagIds && data.tagIds.length > 0 && await this.tagSelect.isVisible()) {
      await this.tagSelect.click();
      for (const tagId of data.tagIds) {
        // 这里简化处理，实际可能需要更精确的选择
        const tagOption = this.page.locator('.el-select-dropdown__item').nth(tagId);
        if (await tagOption.isVisible()) {
          await tagOption.click();
        }
      }
      await this.page.keyboard.press('Escape');
    }
  }

  /**
   * 提交用户表单
   */
  async submitUserForm() {
    await this.submitButton.click();
  }

  /**
   * 取消用户表单
   */
  async cancelUserForm() {
    await this.cancelButton.click();
    await expect(this.createDialog).toBeHidden();
  }

  /**
   * 点击新增标签
   */
  async clickAddTag() {
    await this.addTagButton.click();
    await expect(this.tagDialog).toBeVisible();
  }

  /**
   * 填写标签表单
   */
  async fillTagForm(data: {
    name: string;
    color?: string;
    description?: string;
  }) {
    await this.tagNameInput.fill(data.name);
    if (data.color) {
      await this.tagColorInput.fill(data.color);
    }
    if (data.description) {
      await this.tagDescriptionInput.fill(data.description);
    }
  }

  /**
   * 获取表格行
   */
  getTableRows() {
    return this.userTable.locator('.el-table__row');
  }

  /**
   * 获取特定行
   */
  getRowByText(text: string) {
    return this.userTable.locator('.el-table__row', { hasText: text });
  }

  /**
   * 选择表格行
   */
  async selectRow(row: Locator) {
    const checkbox = row.locator('.el-checkbox');
    await checkbox.click();
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
   * 点击批量删除
   */
  async clickBatchDelete() {
    await this.batchDeleteButton.click();
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
    await expect(this.userTable).toContainText(text);
  }

  /**
   * 验证表格不包含特定文本
   */
  async expectTableNotContains(text: string) {
    await expect(this.userTable).not.toContainText(text);
  }

  /**
   * 验证创建对话框不显示自定义昵称输入框
   */
  async expectCreateDialogNoDisplayName() {
    // 创建用户对话框中不应该有自定义昵称输入框
    const displayNameInput = this.createDialog.locator('input[placeholder*="自定义昵称"]');
    await expect(displayNameInput).toBeHidden();
  }

  /**
   * 验证编辑对话框显示自定义昵称输入框
   */
  async expectEditDialogHasDisplayName() {
    // 编辑用户对话框中应该有自定义昵称输入框
    const displayNameInput = this.createDialog.locator('input[placeholder*="自定义昵称"]');
    await expect(displayNameInput).toBeVisible();
  }
}
