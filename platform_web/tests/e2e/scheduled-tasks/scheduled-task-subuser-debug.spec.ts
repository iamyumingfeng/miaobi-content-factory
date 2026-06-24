import { test, expect } from '@playwright/test';
import { ScheduledTaskCreatePage } from '../pages/ScheduledTaskCreatePage';
import { LoginPage } from '../pages/LoginPage';

/**
 * 调试定时任务创作者选择问题
 * 
 * 问题：选择了创作者，但实际执行定时子任务时却无创作者
 */

test.describe('定时任务创作者选择调试', () => {
  let createPage: ScheduledTaskCreatePage;

  test.beforeEach(async ({ page }) => {
    await LoginPage.loginAsAdmin(page);
    createPage = new ScheduledTaskCreatePage(page);
    await createPage.goto();
  });

  test('创建定时任务时应正确保存创作者选择', async ({ page }) => {
    // 1. 填写任务名称
    await createPage.fillName('创作者调试测试任务');
    
    // 2. 选择调度类型（每日）
    await createPage.selectScheduleType('daily');
    
    // 3. 添加执行时间
    await createPage.addTimePoint();
    // 设置时间为当前时间后10分钟（便于测试执行）
    const now = new Date();
    const futureTime = new Date(now.getTime() + 10 * 60000);
    const timeString = `${String(futureTime.getHours()).padStart(2, '0')}:${String(futureTime.getMinutes()).padStart(2, '0')}`;
    
    // 修改第一个时间点的时间
    const firstTimeInput = page.locator('.time-point-item input[type="time"]').first();
    await firstTimeInput.fill(timeString);
    
    // 4. 选择素材（如果需要）
    // TODO: 先创建一个测试素材
    
    // 5. 选择模板
    await createPage.selectTemplate();
    // 等待模板选择对话框出现
    await page.waitForSelector('.template-select-dialog', { state: 'visible', timeout: 5000 });
    // 选择一个模板
    const firstTemplate = page.locator('.template-card').first();
    await firstTemplate.click();
    // 确认选择
    await page.locator('.template-select-dialog .confirm-btn').click();
    
    // 6. 选择创作者（关键步骤）
    await createPage.selectSubUser();
    // 等待创作者选择对话框出现
    await page.waitForSelector('.sub-user-select-dialog', { state: 'visible', timeout: 5000 });
    
    // 截图：显示创作者选择对话框
    await page.screenshot({ path: 'test-results/subuser-dialog-before-select.png' });
    
    // 选择第一个创作者
    const firstSubUser = page.locator('.sub-user-item').first();
    await firstSubUser.click();
    
    // 截图：显示已选择创作者
    await page.screenshot({ path: 'test-results/subuser-dialog-after-select.png' });
    
    // 确认选择
    await page.locator('.sub-user-select-dialog .confirm-btn').click();
    
    // 等待对话框关闭
    await page.waitForSelector('.sub-user-select-dialog', { state: 'hidden', timeout: 5000 });
    
    // 截图：显示已选择的创作者标签
    await page.screenshot({ path: 'test-results/subuser-selected-tags.png' });
    
    // 验证创作者已被选择（检查标签是否显示）
    const subUserTags = page.locator('.selected-sub-user-tag');
    await expect(subUserTags).toHaveCount(1, { timeout: 5000 });
    
    // 7. 提交表单
    await createPage.submit();
    
    // 等待提交完成（应该跳转到列表页）
    await page.waitForURL(/\/scheduled-tasks\/?$/, { timeout: 10000 });
    
    // 截图：任务列表页
    await page.screenshot({ path: 'test-results/scheduled-task-list-after-create.png' });
    
    // 8. 点击刚创建的任务，查看详情
    const newTaskRow = page.locator('.el-table__row', { hasText: '创作者调试测试任务' }).first();
    await newTaskRow.click();
    
    // 等待详情页加载
    await page.waitForURL(/\/scheduled-tasks\/\d+$/, { timeout: 10000 });
    
    // 截图：任务详情页
    await page.screenshot({ path: 'test-results/scheduled-task-detail.png' });
    
    // 验证详情页是否显示创作者信息
    // 检查页面是否包含创作者相关信息
    const pageContent = await page.content();
    
    // 截图：详细信息
    await page.screenshot({ path: 'test-results/scheduled-task-detail-full.png' });
    
    // 9. 调用 API 检查任务数据（通过浏览器控制台）
    const taskData = await page.evaluate(async () => {
      const response = await fetch('/api/v1/scheduled-tasks/1');  // 假设新任务的 ID 是 1
      return await response.json();
    });
    
    console.log('Task data from API:', JSON.stringify(taskData, null, 2));
    
    // 验证 sub_user_ids_json 字段
    expect(taskData.sub_user_ids_json).toBeDefined();
    expect(taskData.sub_user_ids_json.length).toBeGreaterThan(0);
    
    // 10. 截图最终状态
    await page.screenshot({ path: 'test-results/final-state.png' });
  });

  test('检查前端提交的数据格式', async ({ page }) => {
    // 这个测试用于拦截 API 请求，检查提交的数据格式
    
    // 拦截创建定时任务的 API 请求
    let requestBody: any = null;
    await page.route('/api/v1/scheduled-tasks', async (route) => {
      if (route.request().method() === 'POST') {
        requestBody = JSON.parse(route.request().postData() || '{}');
        console.log('Request body:', JSON.stringify(requestBody, null, 2));
      }
      await route.continue();
    });
    
    // 填写表单
    await createPage.fillName('数据格式测试');
    await createPage.selectScheduleType('daily');
    await createPage.addTimePoint();
    
    // 选择创作者
    await createPage.selectSubUser();
    await page.waitForSelector('.sub-user-select-dialog', { state: 'visible' });
    const firstSubUser = page.locator('.sub-user-item').first();
    await firstSubUser.click();
    await page.locator('.sub-user-select-dialog .confirm-btn').click();
    await page.waitForSelector('.sub-user-select-dialog', { state: 'hidden' });
    
    // 提交表单
    await createPage.submit();
    
    // 等待请求完成
    await page.waitForTimeout(2000);
    
    // 验证请求体中的 sub_user_ids_json 字段
    expect(requestBody).not.toBeNull();
    expect(requestBody.sub_user_ids_json).toBeDefined();
    expect(Array.isArray(requestBody.sub_user_ids_json)).toBeTruthy();
    expect(requestBody.sub_user_ids_json.length).toBeGreaterThan(0);
    
    console.log('sub_user_ids_json in request:', requestBody.sub_user_ids_json);
  });
});
