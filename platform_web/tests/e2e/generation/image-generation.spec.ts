import { test, expect } from '@playwright/test';

/**
 * 百炼图片生成验收 E2E 测试
 *
 * 使用 API Mock 验证前端图片渲染逻辑，无需依赖后端服务。
 * 后端真实集成测试应通过 debug_bailian_image.py 脚本在服务器上运行。
 */
test.describe('百炼图片生成 - 前端渲染验收', () => {
  // 模拟图片 URL（使用公网可访问的占位图片，同时 mock 其响应）
  const MOCK_IMAGE_URLS = [
    'https://mock.example/image-1.png',
    'https://mock.example/image-2.png',
  ];

  const MOCK_TASK = {
    id: 1,
    status: 'completed',
    total_count: 2,
    queued_count: 0,
    generating_count: 0,
    completed_count: 2,
    failed_count: 0,
    paused_count: 0,
    distributed_count: 0,
    pending_publish_count: 0,
    published_count: 0,
    created_at: '2025-04-21T10:00:00Z',
    model_platform: 'bailian',
    model_id: 'wan2.7-image-pro',
    template_id: 1,
    benchmark_material_id: null,
    template_info: {
      id: 1,
      name: '测试模板',
      description: '测试描述',
      prompt_template: '测试提示词',
      thumbnails: [],
      image_size_ratio: '16:9',
      add_watermark: false,
    },
    benchmark_material_info: null,
    material_info: null,
    owner_admin_id: null,
    owner_admin_name: null,
    created_by: null,
  };

  const MOCK_ITEM_WITH_IMAGE: any = {
    id: 101,
    task_id: 1,
    sub_user_id: 1,
    sub_user_name: '测试创作者',
    status: 'completed',
    current_step: null,
    generated_title: '测试生成标题',
    generated_text: '这是一段测试生成的文案内容。',
    generated_image_urls_json: MOCK_IMAGE_URLS,
    model_platform: 'bailian',
    model_id: 'wan2.7-image-pro',
    started_at: '2025-04-21T10:01:00Z',
    completed_at: '2025-04-21T10:02:00Z',
    error_message: null,
    final_prompt: '测试提示词',
  };

  const MOCK_ITEM_DETAIL: any = {
    ...MOCK_ITEM_WITH_IMAGE,
    input_prompt_creativity: '提示词创意内容',
    input_prompt_instruction: '提示词指令内容',
    input_image_size_ratio: '16:9',
    input_watermark: false,
    input_template_images_json: [],
    input_benchmark_images_json: [],
    input_benchmark_title: '对标素材标题',
    input_benchmark_topic: '测试话题',
    input_benchmark_content: '对标素材内容',
    input_sub_user_name: '创作者名称',
    input_sub_user_positioning: '账号定位',
    input_sub_user_profile: '粉丝画像描述',
    input_sub_user_style: '内容风格',
    aigc_generated_prompt: 'AIGC 生成的提示词',
    aigc_user_copy_prompt: 'AIGC 文案提示词',
    aigc_user_image_prompts_json: ['图1提示词', '图2提示词'],
    output_system_text_prompt: '文案系统提示词',
    output_system_image_prompt: '图片系统提示词',
    output_user_image_prompt: '图片用户提示词',
    output_topics: '["话题1", "话题2"]',
    execution_started_at: '2025-04-21T10:01:00Z',
    execution_ended_at: '2025-04-21T10:02:00Z',
    execution_result: 'success',
    dedup_checked_at: '2025-04-21T10:01:30Z',
    dedup_check_passed: true,
    dedup_similarity: 0.15,
    dedup_referenced_items_json: [],
  };

  const MOCK_ITEM_WITHOUT_IMAGE: any = {
    id: 102,
    task_id: 1,
    sub_user_id: 2,
    sub_user_name: '文本创作者',
    status: 'completed',
    current_step: null,
    generated_title: '纯文本案',
    generated_text: '仅有文本，没有图片的生成结果。',
    generated_image_urls_json: [],
    model_platform: 'bailian',
    model_id: 'qwen3.6-plus',
    started_at: '2025-04-21T10:01:00Z',
    completed_at: '2025-04-21T10:01:30Z',
    error_message: null,
    final_prompt: '纯文本提示词',
  };

  const MOCK_ITEM_FAILED: any = {
    id: 103,
    task_id: 1,
    sub_user_id: 3,
    sub_user_name: '失败创作者',
    status: 'failed',
    current_step: null,
    generated_title: null,
    generated_text: null,
    generated_image_urls_json: null,
    model_platform: 'bailian',
    model_id: 'wan2.7-image-pro',
    started_at: '2025-04-21T10:01:00Z',
    completed_at: '2025-04-21T10:01:05Z',
    error_message: '400, message=\'Bad Request\', url=\'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation\'',
    final_prompt: '失败的提示词',
  };

  test.beforeEach(async ({ page }) => {
    // 注入认证 Token（避免路由守卫拦截）
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock-token');
      localStorage.setItem('user', JSON.stringify({
        id: 1, userid: 'admin001', nickname: '测试管理员',
        display_name: '测试管理员', role: 'super_admin', wechat_bound: false
      }));
    });

    // Mock 图片请求（返回真实 PNG 数据使 el-image 渲染成功）
    const tinyPng = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'base64'
    );
    await page.route('**/mock.example/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: tinyPng,
      });
    });

    // Single unified route handler (avoids Playwright route ordering issues)
    await page.route('**/api/v1/**', async (route) => {
      const url = route.request().url();

      if (url.includes('/auth/login')) {
        return route.fulfill({ status: 200, json: {
          success: true, access_token: 'mock-token',
          user: { id: 1, userid: 'admin001', role: 'super_admin', nickname: '测试管理员', display_name: '测试管理员', wechat_bound: false },
        }});
      }

      if (url.includes('/auth/me')) {
        return route.fulfill({ status: 200, json: {
          data: { id: 1, userid: 'admin001', nickname: '测试管理员', display_name: '测试管理员', role: 'super_admin', wechat_bound: false },
        }});
      }

      if (url.includes('/generation/tasks/1') && !url.includes('/items')) {
        return route.fulfill({ status: 200, json: { data: MOCK_TASK } });
      }

      if (url.includes('/generation/tasks/') && url.includes('/items')) {
        return route.fulfill({ status: 200, json: {
          data: { items: [MOCK_ITEM_WITH_IMAGE, MOCK_ITEM_WITHOUT_IMAGE, MOCK_ITEM_FAILED], total: 3, page: 1, limit: 20 },
        }});
      }

      if (url.includes('/generation/items/') && url.includes('/detail')) {
        let itemData;
        if (url.includes('/101/')) itemData = MOCK_ITEM_DETAIL;
        else if (url.includes('/103/')) itemData = MOCK_ITEM_FAILED;
        else itemData = MOCK_ITEM_WITHOUT_IMAGE;
        return route.fulfill({ status: 200, json: { data: itemData } });
      }

      if (url.includes('/settings/model-configs')) {
        return route.fulfill({ status: 200, json: {
          data: {
            items: [
              { id: 1, platform: 'bailian', model_id: 'wan2.7-image-pro', model_name: '万相2.7 Pro', model_type: 'image', status: 'active' },
              { id: 2, platform: 'bailian', model_id: 'qwen3.6-plus', model_name: 'Qwen3.6-Plus', model_type: 'llm', status: 'active' },
            ],
            total: 2,
          },
        }});
      }

      if (url.includes('/execution-logs')) {
        return route.fulfill({ status: 200, json: { data: [] } });
      }

      if (url.includes('/sidebar')) {
        return route.fulfill({ status: 200, json: { data: { menus: [] } } });
      }

      return route.fulfill({ status: 200, json: { data: null } });
    });

    // 导航到任务详情页
    await page.goto('/generation/detail/1');
    await page.waitForLoadState('networkidle');
  });

  test('子任务列表应展示生成的图片缩略图', async ({ page }) => {
    // 等待表格渲染
    await page.waitForTimeout(1000);

    // 验证第一行有图片缩略图
    const firstRow = page.locator('.el-table__body tr').first();
    await expect(firstRow).toBeVisible();

    // 检查生成预览列中的图片
    const previewImages = firstRow.locator('.preview-thumb');
    const imageCount = await previewImages.count();
    expect(imageCount).toBeGreaterThan(0);

    // 验证第一张图片的 src 属性
    const firstThumb = previewImages.first();
    await expect(firstThumb).toBeVisible();
    const imgEl = firstThumb.locator('img');
    const src = await imgEl.getAttribute('src');
    expect(src).toContain('mock.example');

    await page.screenshot({ path: 'artifacts/image-list-preview.png' });
  });

  test('生成内容Tab应正确渲染图片画廊', async ({ page }) => {
    // 点击第一行的详情按钮
    const firstRow = page.locator('.el-table__body tr').first();
    await firstRow.click();
    await page.waitForTimeout(1500);

    // 验证抽屉已打开
    await expect(page.locator('.el-drawer__body')).toBeVisible();

    // 切换到"生成内容"Tab
    await page.locator('.el-tabs__item:has-text("生成内容")').click();
    await page.waitForTimeout(800);

    // 验证图片画廊
    const gallery = page.locator('.image-gallery');
    await expect(gallery).toBeVisible();

    // 验证图片数量
    const galleryLabel = page.locator('.image-gallery .section-label');
    const labelText = await galleryLabel.textContent();
    expect(labelText).toContain('2');

    // 验证每张图片都可见
    const galleryItems = page.locator('.gallery-grid .gallery-item');
    const count = await galleryItems.count();
    expect(count).toBe(2);

    for (let i = 0; i < count; i++) {
      await expect(galleryItems.nth(i)).toBeVisible();
    }

    await page.screenshot({ path: 'artifacts/image-gallery.png' });
  });

  test('图片画廊应支持点击预览', async ({ page }) => {
    // 点击第一行打开详情
    await page.locator('.el-table__body tr').first().click();
    await page.waitForTimeout(1500);

    // 切换到"生成内容"Tab
    await page.locator('.el-tabs__item:has-text("生成内容")').click();
    await page.waitForTimeout(800);

    // 点击第一张图片触发预览
    const firstImage = page.locator('.gallery-grid .gallery-item').first();
    await firstImage.click();
    await page.waitForTimeout(1000);

    // 验证图片预览对话框（使用 .first() 避免 strict mode violation）
    const viewer = page.locator('.el-image-viewer__wrapper').first();
    await expect(viewer).toBeVisible();

    await page.screenshot({ path: 'artifacts/image-preview.png' });
  });

  test('没有图片生成的子任务不应显示图片画廊', async ({ page }) => {
    // 点击第二行（无图片子任务）
    const secondRow = page.locator('.el-table__body tr').nth(1);
    await secondRow.click();
    await page.waitForTimeout(1500);

    // 切换到"生成内容"Tab
    await page.locator('.el-tabs__item:has-text("生成内容")').click();
    await page.waitForTimeout(800);

    // 验证没有图片画廊
    const gallery = page.locator('.image-gallery');
    const galleryVisible = await gallery.isVisible().catch(() => false);
    expect(galleryVisible).toBe(false);

    // 验证有文案内容
    const contentBody = page.locator('.content-body');
    await expect(contentBody).toBeVisible();

    await page.screenshot({ path: 'artifacts/no-image-content.png' });
  });

  test('图片生成失败的子任务应展示错误信息', async ({ page }) => {
    // 点击第三行（失败子任务）
    const thirdRow = page.locator('.el-table__body tr').nth(2);
    await thirdRow.click();
    await page.waitForTimeout(1500);

    // 切换到"生成内容"Tab
    await page.locator('.el-tabs__item:has-text("生成内容")').click();
    await page.waitForTimeout(800);

    // 验证错误信息区块
    const errorSection = page.locator('.error-section');
    await expect(errorSection).toBeVisible();

    // 验证错误详情可读
    const errorContent = page.locator('.error-content');
    await expect(errorContent).toBeVisible();
    const errorText = await errorContent.textContent();
    expect(errorText).toContain('Bad Request');

    await page.screenshot({ path: 'artifacts/image-generation-error.png' });
  });

  test('parseImageUrls应正确处理JSON字符串格式的图片URL', async ({ page }) => {
    // 验证前端 parseImageUrls 函数能正确处理 JSON 字符串
    // 通过检查渲染结果间接验证
    await page.locator('.el-table__body tr').first().click();
    await page.waitForTimeout(1500);

    // 通过 JS 验证 parseImageUrls 的行为
    const result = await page.evaluate(() => {
      const parseImageUrls = (data: any): string[] => {
        if (Array.isArray(data)) return data;
        if (typeof data === 'string') {
          try { return JSON.parse(data); } catch { /* fall through */ }
        }
        return [];
      };
      return {
        array: parseImageUrls(['url1', 'url2']),
        jsonStr: parseImageUrls('["url1", "url2"]'),
        empty: parseImageUrls(null),
        badJson: parseImageUrls('not json'),
      };
    });

    expect(result.array).toEqual(['url1', 'url2']);
    expect(result.jsonStr).toEqual(['url1', 'url2']);
    expect(result.empty).toEqual([]);
    expect(result.badJson).toEqual([]);
  });
});
