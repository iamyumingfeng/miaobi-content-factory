import { Page, Locator, expect } from '@playwright/test';

export class SettingsPage {
  readonly page: Page;

  // 页面元素
  readonly pageTitle: Locator;
  readonly settingsMenu: Locator;
  readonly profileMenuItem: Locator;
  readonly modelMenuItem: Locator;
  readonly cleanupMenuItem: Locator;
  readonly notificationMenuItem: Locator;

  // 个人设置面板
  readonly profilePanel: Locator;
  readonly usernameInput: Locator;
  readonly nicknameInput: Locator;
  readonly saveNicknameButton: Locator;

  // 修改密码
  readonly oldPasswordInput: Locator;
  readonly newPasswordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly changePasswordButton: Locator;

  // 模型平台配置
  readonly modelPanel: Locator;
  readonly defaultTextModelSelect: Locator;
  readonly defaultImageModelSelect: Locator;
  readonly defaultVideoModelSelect: Locator;
  readonly platformTabs: Locator;
  readonly modelCollapse: Locator;

  constructor(page: Page) {
    this.page = page;

    // 页面标题
    this.pageTitle = page.locator('h2.page-title');

    // 设置菜单
    this.settingsMenu = page.locator('.settings-menu');
    this.profileMenuItem = page.locator('.el-menu-item', { hasText: '个人设置' });
    this.modelMenuItem = page.locator('.el-menu-item', { hasText: '模型平台配置' });
    this.cleanupMenuItem = page.locator('.el-menu-item', { hasText: '过期清理策略' });
    this.notificationMenuItem = page.locator('.el-menu-item', { hasText: '通知设置' });

    // 个人设置面板
    this.profilePanel = page.locator('.settings-panel', { hasText: '个人设置' });
    this.usernameInput = this.profilePanel.locator('input[disabled]');
    this.nicknameInput = this.profilePanel.locator('input[placeholder*="自定义昵称"]');
    this.saveNicknameButton = this.profilePanel.locator('button', { hasText: '保存昵称' });

    // 修改密码表单
    this.oldPasswordInput = this.profilePanel.locator('input[placeholder*="原密码"]');
    this.newPasswordInput = this.profilePanel.locator('input[placeholder*="新密码"]');
    this.confirmPasswordInput = this.profilePanel.locator('input[placeholder*="再次输入新密码"]');
    this.changePasswordButton = this.profilePanel.locator('button', { hasText: '修改密码' });

    // 模型平台配置
    this.modelPanel = page.locator('.settings-panel', { hasText: '模型平台配置' });
    this.defaultTextModelSelect = this.modelPanel.locator('.el-select').nth(0);
    this.defaultImageModelSelect = this.modelPanel.locator('.el-select').nth(1);
    this.defaultVideoModelSelect = this.modelPanel.locator('.el-select').nth(2);
    this.platformTabs = page.locator('.platform-tabs');
    this.modelCollapse = page.locator('.model-collapse');
  }

  /**
   * 导航到系统设置页面
   */
  async goto() {
    await this.page.goto('/settings');
  }

  /**
   * 验证在系统设置页面
   */
  async expectOnSettingsPage() {
    await expect(this.page).toHaveURL(/\/settings/, { timeout: 10000 });
    await expect(this.pageTitle).toBeVisible({ timeout: 10000 });
  }

  /**
   * 点击个人设置菜单
   */
  async clickProfileMenu() {
    await this.profileMenuItem.click();
    await expect(this.profilePanel).toBeVisible();
  }

  /**
   * 点击模型平台配置菜单
   */
  async clickModelMenu() {
    await this.modelMenuItem.click();
    await expect(this.modelPanel).toBeVisible();
  }

  /**
   * 点击过期清理策略菜单
   */
  async clickCleanupMenu() {
    await this.cleanupMenuItem.click();
  }

  /**
   * 点击通知设置菜单
   */
  async clickNotificationMenu() {
    await this.notificationMenuItem.click();
  }

  /**
   * 验证个人设置面板可见
   */
  async expectProfilePanelVisible() {
    await expect(this.profilePanel).toBeVisible();
    await expect(this.usernameInput).toBeVisible();
    await expect(this.nicknameInput).toBeVisible();
  }

  /**
   * 验证模型平台配置面板可见
   */
  async expectModelPanelVisible() {
    await expect(this.modelPanel).toBeVisible();
  }

  /**
   * 更新昵称
   */
  async updateNickname(nickname: string) {
    await this.nicknameInput.fill(nickname);
    await this.saveNicknameButton.click();
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string) {
    await this.oldPasswordInput.fill(oldPassword);
    await this.newPasswordInput.fill(newPassword);
    await this.confirmPasswordInput.fill(newPassword);
    await this.changePasswordButton.click();
  }

  /**
   * 验证成功消息
   */
  async expectSuccessMessage(message: string) {
    const successMessage = this.page.locator('.el-message--success');
    await expect(successMessage).toContainText(message);
  }

  /**
   * 验证错误消息
   */
  async expectErrorMessage(message: string) {
    const errorMessage = this.page.locator('.el-message--error');
    await expect(errorMessage).toContainText(message);
  }

  /**
   * 获取用户菜单项数量
   */
  async getMenuItemCount() {
    return await this.settingsMenu.locator('.el-menu-item').count();
  }

  /**
   * 验证菜单项可见
   */
  async expectMenuItemsVisible(expectedItems: string[]) {
    for (const item of expectedItems) {
      const menuItem = this.settingsMenu.locator('.el-menu-item', { hasText: item });
      await expect(menuItem).toBeVisible();
    }
  }

  /**
   * 获取默认模型选择器数量
   */
  async getDefaultModelSelectCount() {
    return await this.modelPanel.locator('.el-select').count();
  }

  /**
   * 选择默认文本模型
   */
  async selectDefaultTextModel(modelName: string) {
    await this.defaultTextModelSelect.click();
    const option = this.page.locator('.el-select-dropdown__item', { hasText: modelName });
    await option.click();
  }

  /**
   * 获取平台标签页数量
   */
  async getPlatformTabCount() {
    return await this.platformTabs.locator('.el-tabs__item').count();
  }

  /**
   * 点击平台标签页
   */
  async clickPlatformTab(platformName: string) {
    const tab = this.platformTabs.locator('.el-tabs__item', { hasText: platformName });
    await tab.click();
  }

  /**
   * 获取模型折叠面板项数量
   */
  async getCollapseItemCount() {
    return await this.modelCollapse.locator('.el-collapse-item').count();
  }

  /**
   * 获取表格行数
   */
  async getTableRowCount(): Promise<number> {
    const table = this.page.locator('.el-table');
    const rows = table.locator('.el-table__row');
    return await rows.count();
  }

  /**
   * 验证表格可见
   */
  async expectTableVisible() {
    const table = this.page.locator('.el-table').first();
    await expect(table).toBeVisible();
  }

  /**
   * 点击添加模型按钮
   */
  async clickAddModelButton(modelType: 'text' | 'image' | 'video') {
    const typeText = {
      text: '文本模型',
      image: '图片模型',
      video: '视频模型'
    };
    const collapseItem = this.modelCollapse.locator('.el-collapse-item', { hasText: typeText[modelType] });
    const addButton = collapseItem.locator('button', { hasText: '添加' });
    await addButton.click();
  }

  /**
   * 验证模型对话框可见
   */
  async expectModelDialogVisible() {
    const dialog = this.page.locator('.el-dialog', { hasText: /添加模型|编辑模型/ });
    await expect(dialog).toBeVisible();
  }

  /**
   * 获取对话框
   */
  getModelDialog() {
    return this.page.locator('.el-dialog', { hasText: /添加模型|编辑模型/ });
  }

  /**
   * 获取对话框中的输入框
   */
  getDialogInput(placeholder: string) {
    const dialog = this.getModelDialog();
    return dialog.locator(`input[placeholder*="${placeholder}"]`);
  }

  /**
   * 获取对话框中的确定按钮
   */
  getDialogSubmitButton() {
    const dialog = this.getModelDialog();
    return dialog.locator('button', { hasText: '确定' });
  }

  /**
   * 获取对话框中的取消按钮
   */
  getDialogCancelButton() {
    const dialog = this.getModelDialog();
    return dialog.locator('button', { hasText: '取消' });
  }

  /**
   * 填写模型表单
   */
  async fillModelForm(data: {
    modelId: string;
    modelName: string;
    baseUrl?: string;
    apiKey?: string;
    maxConcurrency?: number;
  }) {
    const dialog = this.getModelDialog();

    const modelIdInput = dialog.locator('input[placeholder*="模型 ID"]');
    const modelNameInput = dialog.locator('input[placeholder*="模型名称"]');
    const baseUrlInput = dialog.locator('input[placeholder*="Base URL"]');
    const apiKeyInput = dialog.locator('input[placeholder*="API Key"]');

    await modelIdInput.fill(data.modelId);
    await modelNameInput.fill(data.modelName);

    if (data.baseUrl) {
      await baseUrlInput.fill(data.baseUrl);
    }

    if (data.apiKey) {
      await apiKeyInput.fill(data.apiKey);
    }

    if (data.maxConcurrency) {
      const numberInput = dialog.locator('.el-input-number');
      await numberInput.fill(data.maxConcurrency.toString());
    }
  }
}
