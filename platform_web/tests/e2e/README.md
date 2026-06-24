# E2E 测试说明

## 概述

本项目使用 Playwright 进行端到端（E2E）测试，覆盖关键用户流程。

## 目录结构

```
tests/e2e/
├── pages/                  # 页面对象模型 (Page Object Model)
│   ├── LoginPage.ts       # 登录页面对象
│   ├── DashboardPage.ts   # 仪表盘页面对象
│   ├── TemplatePage.ts    # 模板页面对象
│   ├── MaterialPage.ts    # 素材页面对象
│   └── GenerationPage.ts  # 内容生成页面对象
├── auth/                   # 认证相关测试
│   └── login.spec.ts      # 登录功能测试
├── dashboard/              # 仪表盘相关测试
│   └── dashboard.spec.ts  # 仪表盘功能测试
├── templates/              # 模板相关测试
│   └── templates.spec.ts  # 模板管理测试
├── materials/              # 素材相关测试
│   └── materials.spec.ts  # 素材库测试
└── generation/             # 内容生成相关测试
    └── generation.spec.ts # 内容生成测试
```

## 页面对象模型 (POM)

我们使用页面对象模型来组织测试代码，使测试更易维护和复用。每个页面对象封装了与该页面交互的所有操作。

**优点：**
- 代码复用
- 易于维护
- 测试更清晰
- 修改 UI 只需更新一处

## 运行测试

### 前置条件

1. 安装 Playwright 浏览器：
```bash
npm install
npx playwright install
```

2. 确保后端服务正在运行（或使用 mock）

3. 确保前端开发服务器可以启动

### 运行所有测试

```bash
# 安装依赖（首次运行）
npm install -D @playwright/test

# 运行所有测试
npx playwright test

# 运行特定浏览器
npx playwright test --project=chromium

# 运行特定测试文件
npx playwright test tests/e2e/auth/login.spec.ts

# 运行特定测试用例
npx playwright test -g "应该能够显示登录页面"
```

### 调试模式

```bash
#  headed 模式（可见浏览器）
npx playwright test --headed

# 调试模式
npx playwright test --debug

# 逐步执行
npx playwright test --ui
```

### 查看测试报告

```bash
# 生成 HTML 报告
npx playwright show-report
```

## 测试配置

Playwright 配置在 `playwright.config.ts` 中，包括：

- **测试目录**: `tests/e2e/`
- **浏览器**: Chromium, Firefox, WebKit
- **基本 URL**: `http://localhost:5173`
- **截图**: 仅失败时
- **视频**: 仅失败时保留
- **追踪**: 首次重试时

## 测试数据

目前测试使用 `test.skip()` 标记，需要在实际环境中配置：

1. **测试账号**: 在 `playwright.config.ts` 或环境变量中配置
2. **Mock 数据**: 考虑使用 API mock 来避免依赖真实后端

## 编写新测试

### 1. 创建页面对象

```typescript
// tests/e2e/pages/YourPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class YourPage {
  readonly page: Page;
  readonly someElement: Locator;

  constructor(page: Page) {
    this.page = page;
    this.someElement = page.locator('selector');
  }

  async goto() {
    await this.page.goto('/your-path');
  }

  async someAction() {
    await this.someElement.click();
  }

  async expectSomething() {
    await expect(this.someElement).toBeVisible();
  }
}
```

### 2. 编写测试用例

```typescript
// tests/e2e/your-feature/your-test.spec.ts
import { test, expect } from '@playwright/test';
import { YourPage } from '../pages/YourPage';

test.describe('功能描述', () => {
  test('测试用例描述', async ({ page }) => {
    const yourPage = new YourPage(page);
    await yourPage.goto();
    await yourPage.someAction();
    await yourPage.expectSomething();
  });
});
```

## 最佳实践

1. **使用 data-testid**: 在组件中添加 `data-testid` 属性，使选择器更稳定
2. **等待而非超时**: 使用 `waitFor` 而不是 `waitForTimeout`
3. **独立测试**: 每个测试应该独立运行，不依赖其他测试
4. **清理状态**: 测试后清理创建的数据
5. **有意义的断言**: 验证用户可见的行为，而非实现细节

## 持续集成

在 CI/CD 流程中：

```yaml
# .github/workflows/e2e.yml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npx playwright test

- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## 故障排查

### 测试超时
- 检查开发服务器是否正常运行
- 增加测试超时时间
- 检查网络连接

### 选择器问题
- 使用 `data-testid` 而非 CSS 类
- 检查元素是否在正确的 frame 中
- 使用 Playwright Inspector 调试

### 浏览器问题
- 确保已安装浏览器: `npx playwright install`
- 尝试不同的浏览器项目

## 相关资源

- [Playwright 文档](https://playwright.dev/)
- [Page Object Model](https://playwright.dev/docs/pom)
- [测试最佳实践](https://playwright.dev/docs/best-practices)
