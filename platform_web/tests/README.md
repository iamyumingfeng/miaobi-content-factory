# 前端测试文档

## 测试架构概览

本项目采用多层次的测试策略：

```
tests/
├── e2e/              # 端到端测试 (Playwright)
└── unit/             # 单元测试 (Vitest) - 待实现
```

## 测试类型

### 1. E2E 测试 (Playwright)
**位置**: `tests/e2e/`

覆盖关键用户流程：
- ✅ 登录流程 (账号登录 / 微信扫码)
- ✅ 仪表盘导航
- ✅ 模板管理 (列表、搜索、创建)
- ✅ 素材库 (浏览、上传、搜索)
- ✅ 内容生成 (创建任务、查看列表、详情)

### 2. 单元测试 (Vitest)
**位置**: `tests/unit/` - 待实现

测试范围：
- 工具函数
- 自定义 Hooks
- 组件逻辑
- Store 状态管理

## 快速开始

### 安装依赖

```bash
cd platform_web

# 安装 Playwright（如果还没有安装）
npm install

# 安装 Playwright 浏览器
npx playwright install
```

### 运行 E2E 测试

```bash
# 运行所有 E2E 测试
npm run test:e2e

# 运行特定测试文件
npm run test:e2e -- tests/e2e/auth/login.spec.ts

#  headed 模式（可见浏览器）
npm run test:e2e:headed

# UI 模式（逐步调试）
npm run test:e2e:ui

# 查看测试报告
npm run test:e2e:report
```

## E2E 测试文件结构

```
tests/e2e/
├── pages/                  # 页面对象模型
│   ├── LoginPage.ts       # 登录页
│   ├── DashboardPage.ts   # 仪表盘
│   ├── TemplatePage.ts    # 模板页
│   ├── MaterialPage.ts    # 素材页
│   └── GenerationPage.ts  # 内容生成页
├── auth/
│   └── login.spec.ts      # 登录测试
├── dashboard/
│   └── dashboard.spec.ts  # 仪表盘测试
├── templates/
│   └── templates.spec.ts  # 模板测试
├── materials/
│   └── materials.spec.ts  # 素材测试
├── generation/
│   └── generation.spec.ts # 生成测试
└── README.md              # E2E 详细文档
```

## 页面对象模型 (POM)

每个页面对象封装了与该页面交互的所有操作，使测试更易维护。

### 示例: LoginPage

```typescript
const loginPage = new LoginPage(page);
await loginPage.goto();
await loginPage.loginWithPassword('user', 'pass');
await loginPage.expectLoginSuccess();
```

## 配置说明

### Playwright 配置

配置文件: `playwright.config.ts`

主要配置项：
- **测试目录**: `tests/e2e/`
- **浏览器**: Chromium, Firefox, WebKit
- **基础 URL**: `http://localhost:5173`
- **失败截图**: 自动捕获
- **失败视频**: 自动保留
- **开发服务器**: 自动启动 `npm run dev`

### 环境变量

可以创建 `.env.test` 文件：

```env
# 测试账号
TEST_USERNAME=test_admin
TEST_PASSWORD=test_password

# 测试环境
BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
```

## 测试状态

### 当前状态

- ✅ E2E 测试框架已设置
- ✅ 页面对象模型已创建
- ✅ 关键用户流程测试用例已编写
- ⏸️ 测试用例标记为 `test.skip()`（需要后端服务）

### 启用测试

当有可用的测试环境时：

1. 确保后端 API 服务运行
2. 配置测试账号
3. 移除 `test.skip()` 标记
4. 运行测试

## 编写新测试

### 1. 创建页面对象 (如需要)

```typescript
// tests/e2e/pages/NewPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class NewPage {
  readonly page: Page;
  readonly someElement: Locator;

  constructor(page: Page) {
    this.page = page;
    this.someElement = page.locator('[data-testid="your-element"]');
  }

  async goto() {
    await this.page.goto('/your-path');
  }

  async doSomething() {
    await this.someElement.click();
  }
}
```

### 2. 编写测试用例

```typescript
// tests/e2e/your-feature/your-test.spec.ts
import { test, expect } from '@playwright/test';
import { NewPage } from '../pages/NewPage';

test.describe('功能描述', () => {
  test('测试用例', async ({ page }) => {
    const newPage = new NewPage(page);
    await newPage.goto();
    await newPage.doSomething();
    // 断言...
  });
});
```

## 最佳实践

### 1. 使用 data-testid

在 Vue 组件中添加 `data-testid` 属性：

```vue
<template>
  <button data-testid="submit-button">提交</button>
  <input data-testid="username-input" v-model="username" />
</template>
```

### 2. 等待而非超时

```typescript
// GOOD: 等待元素
await page.waitForSelector('[data-testid="result"]');

// BAD: 固定超时
await page.waitForTimeout(3000);
```

### 3. 独立测试

每个测试应该：
- 独立运行，不依赖其他测试
- 设置自己的前置条件
- 清理自己创建的数据

### 4. 有意义的断言

验证用户可见的行为：

```typescript
// GOOD
await expect(page.locator('text=欢迎')).toBeVisible();

// BAD（测试实现细节）
expect(component.state.isLoggedIn).toBe(true);
```

## 常见问题

### Q: 测试超时怎么办？

A: 检查：
1. 开发服务器是否正常运行
2. 网络连接是否正常
3. 增加测试超时时间

### Q: 选择器找不到元素？

A: 使用 `data-testid` 属性，或使用 Playwright Inspector 调试：

```bash
npx playwright test --debug
```

### Q: 如何在 CI 中运行？

A: 参考 `.github/workflows/e2e.yml` 示例配置。

## 下一步

### 短期计划
- [ ] 配置测试环境（Mock 后端或测试数据库）
- [ ] 启用登录测试（移除 skip）
- [ ] 添加用户管理测试
- [ ] 添加通知测试
- [ ] 添加设置测试

### 长期计划
- [ ] 实现单元测试 (Vitest)
- [ ] 添加组件测试
- [ ] 添加性能测试
- [ ] 添加视觉回归测试
- [ ] 集成到 CI/CD 流程

## 相关文档

- [E2E 测试详细文档](./e2e/README.md)
- [Playwright 官方文档](https://playwright.dev/)
- [Vue 测试指南](https://test-utils.vuejs.org/)

## 技术支持

如有问题，请查看：
1. Playwright 文档: https://playwright.dev/docs/intro
2. 项目 E2E 文档: [./e2e/README.md](./e2e/README.md)
3. 项目 Issue 跟踪
