import { Page, Locator, expect } from '@playwright/test';

export class TemplatePage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly templateCards: Locator;
  readonly searchInput: Locator;
  readonly categoryTree: Locator;
  readonly viewTabs: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '模板库' });
    this.createButton = page.locator('button', { hasText: '新建模板' });
    this.templateCards = page.locator('.template-card');
    this.searchInput = page.locator('input[placeholder*="搜索模板名称"]');
    this.categoryTree = page.locator('.category-panel .el-tree');
    this.viewTabs = page.locator('.view-tabs');
  }

  async goto() {
    await this.page.goto('/templates/list');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/templates\/list/);
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectTemplateCardsVisible() {
    await expect(this.templateCards.first()).toBeVisible();
  }

  async getTemplateCardCount() {
    return await this.templateCards.count();
  }

  async expectCreateButtonVisible() {
    await expect(this.createButton).toBeVisible();
  }

  async clickCreateButton() {
    await this.createButton.click();
  }

  async expectSearchInputVisible() {
    await expect(this.searchInput).toBeVisible();
  }

  async searchTemplates(keyword: string) {
    await this.searchInput.fill(keyword);
  }

  async expectCategoryTreeVisible() {
    await expect(this.categoryTree).toBeVisible();
  }

  async expectViewTabsVisible() {
    await expect(this.viewTabs).toBeVisible();
  }

  async switchToCardView() {
    const cardTab = this.page.locator('.el-tabs__item', { hasText: '卡片视图' });
    await cardTab.click();
  }

  async switchToListView() {
    const listTab = this.page.locator('.el-tabs__item', { hasText: '列表视图' });
    await listTab.click();
  }
}
