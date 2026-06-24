import { Page, Locator, expect } from '@playwright/test';

export class MaterialPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly uploadButton: Locator;
  readonly materialCards: Locator;
  readonly searchInput: Locator;
  readonly categoryTree: Locator;
  readonly viewTabs: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('.page-title', { hasText: '素材库' });
    this.uploadButton = page.locator('button', { hasText: '上传素材' });
    this.materialCards = page.locator('.material-card');
    this.searchInput = page.locator('input[placeholder*="搜索素材标题"]');
    this.categoryTree = page.locator('.category-panel .el-tree');
    this.viewTabs = page.locator('.view-tabs');
  }

  async goto() {
    await this.page.goto('/materials');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/materials/);
  }

  async expectPageTitleVisible() {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectMaterialCardsVisible() {
    await expect(this.materialCards.first()).toBeVisible();
  }

  async getMaterialCardCount() {
    return await this.materialCards.count();
  }

  async expectUploadButtonVisible() {
    await expect(this.uploadButton).toBeVisible();
  }

  async clickUploadButton() {
    await this.uploadButton.click();
  }

  async expectSearchInputVisible() {
    await expect(this.searchInput).toBeVisible();
  }

  async searchMaterials(keyword: string) {
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
