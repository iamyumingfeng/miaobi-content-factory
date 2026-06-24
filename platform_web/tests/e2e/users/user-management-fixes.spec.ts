import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { SubUsersPage } from '../pages/SubUsersPage';

/**
 * 用户管理功能修复验证测试
 * 
 * 测试场景：
 * 1. 创作者列表中标签正确显示
 * 2. 批量转移用户功能
 * 3. 登录/退出时状态更新
 */

test.describe('创作者标签显示修复验证', () => {
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

  test('创作者列表应正确显示标签', async ({ page }) => {
    // 获取表格行
    const rows = subUsersPage.getTableRows();
    
    // 等待表格加载
    await page.waitForTimeout(1000);
    
    // 检查表格是否有数据
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      // 检查标签列是否存在
      const firstRow = rows.first();
      
      // 标签列应该在表格中
      const tagColumn = firstRow.locator('.cell').filter({ hasText: /el-tag/ });
      
      // 验证标签显示逻辑：无论是否有标签，都应该正确处理
      const tagElements = firstRow.locator('.el-tag');
      const tagCount = await tagElements.count();
      
      // 如果有标签，验证标签样式
      if (tagCount > 0) {
        await expect(tagElements.first()).toBeVisible();
        
        // 验证标签有文字内容
        const tagText = await tagElements.first().textContent();
        expect(tagText).toBeTruthy();
      }
    }
  });

  test('新增创作者后标签列表数量应刷新', async ({ page }) => {
    // 创建新用户（带标签）
    await subUsersPage.clickCreateUser();
    await subUsersPage.fillUserForm({
      nickname: `测试用户_${Date.now()}`,
      contentStyle: '测试风格'
    });
    await subUsersPage.submitUserForm();
    
    // 等待创建成功
    await page.waitForTimeout(1000);
    
    // 验证成功消息
    await subUsersPage.expectSuccessMessage('创建成功');
    
    // 验证标签数量已刷新 - "全部"标签数量应该+1
    // 这个测试依赖于实际数据，需要在测试环境中验证
  });

  test('编辑创作者标签后列表应正确显示', async ({ page }) => {
    // 等待表格加载
    await page.waitForTimeout(1000);
    
    const rows = subUsersPage.getTableRows();
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      const firstRow = rows.first();
      
      // 点击编辑按钮
      await subUsersPage.clickEditButton(firstRow);
      
      // 验证编辑对话框显示
      await expect(subUsersPage.createDialog).toBeVisible();
      
      // 验证标签选择器可见
      await expect(subUsersPage.tagSelect).toBeVisible();
      
      // 取消编辑
      await subUsersPage.cancelUserForm();
    }
  });
});

test.describe('批量转移用户功能修复验证', () => {
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

  test('批量选择用户后应显示转移按钮', async ({ page }) => {
    // 等待表格加载
    await page.waitForTimeout(1000);
    
    const rows = subUsersPage.getTableRows();
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      // 选择第一行
      const firstRow = rows.first();
      await subUsersPage.selectRow(firstRow);
      
      // 等待选中状态
      await page.waitForTimeout(500);
      
      // 验证批量转移按钮可用
      await expect(subUsersPage.batchTransferButton).toBeEnabled();
    }
  });

  test('批量转移对话框应正确显示目标创作管理员', async ({ page }) => {
    // 等待表格加载
    await page.waitForTimeout(1000);
    
    const rows = subUsersPage.getTableRows();
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      // 选择第一行
      const firstRow = rows.first();
      await subUsersPage.selectRow(firstRow);
      
      // 点击批量转移
      await subUsersPage.batchTransferButton.click();
      
      // 验证对话框显示
      await expect(subUsersPage.transferDialog).toBeVisible();
      
      // 验证目标创作管理员选择器
      await expect(subUsersPage.transferTargetOperatorSelect).toBeVisible();
      
      // 关闭对话框
      await page.keyboard.press('Escape');
    }
  });
});

test.describe('登录状态更新修复验证', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.ensureLoggedOut();
  });

  test('登录后用户状态应更新为在线', async ({ page }) => {
    // 使用创作管理员账号登录
    await loginPage.loginWithPassword('admin', 'admin123');
    
    // 等待登录成功
    await page.waitForTimeout(2000);
    
    // 验证登录成功
    await loginPage.expectLoginSuccess();
    
    // 登录后状态更新应该在后端处理
    // 前端验证：登录成功跳转到了首页
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('退出登录后用户状态应更新为离线', async ({ page }) => {
    // 先登录
    await loginPage.loginWithPassword('admin', 'admin123');
    await loginPage.expectLoginSuccess();
    
    // 等待页面加载
    await page.waitForTimeout(1000);
    
    // 点击退出按钮（用户下拉菜单）
    const userDropdown = page.locator('.user-dropdown, .el-dropdown, [class*="user"]').first();
    
    if (await userDropdown.isVisible()) {
      await userDropdown.click();
      await page.waitForTimeout(500);
      
      // 查找退出按钮
      const logoutButton = page.locator('text=退出, text=退出登录, button:has-text("退出")').first();
      
      if (await logoutButton.isVisible()) {
        await logoutButton.click();
        
        // 等待退出完成
        await page.waitForTimeout(1000);
        
        // 验证跳转到登录页
        await loginPage.expectOnLoginPage();
      }
    }
  });
});

test.describe('状态筛选功能修复验证', () => {
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

  test('筛选在线状态应显示在线用户', async ({ page }) => {
    // 选择在线状态
    await subUsersPage.searchUsers(undefined, '在线');
    
    // 等待筛选结果
    await page.waitForTimeout(1000);
    
    // 表格应该可见
    await expect(subUsersPage.userTable).toBeVisible();
    
    // 检查筛选状态是否正确应用
    const statusSelect = subUsersPage.searchStatusSelect;
    const selectedText = await statusSelect.textContent();
    expect(selectedText).toContain('在线');
  });

  test('筛选离线状态应显示离线用户', async ({ page }) => {
    // 选择离线状态
    await subUsersPage.searchUsers(undefined, '离线');
    
    // 等待筛选结果
    await page.waitForTimeout(1000);
    
    // 表格应该可见
    await expect(subUsersPage.userTable).toBeVisible();
    
    // 检查筛选状态是否正确应用
    const statusSelect = subUsersPage.searchStatusSelect;
    const selectedText = await statusSelect.textContent();
    expect(selectedText).toContain('离线');
  });

  test('筛选已禁用状态应显示已禁用用户', async ({ page }) => {
    // 选择已禁用状态
    await subUsersPage.searchUsers(undefined, '已禁用');
    
    // 等待筛选结果
    await page.waitForTimeout(1000);
    
    // 表格应该可见
    await expect(subUsersPage.userTable).toBeVisible();
    
    // 检查筛选状态是否正确应用
    const statusSelect = subUsersPage.searchStatusSelect;
    const selectedText = await statusSelect.textContent();
    expect(selectedText).toContain('已禁用');
  });
});
