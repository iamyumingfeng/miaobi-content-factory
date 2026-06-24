# 妙笔内容工场 - Web 管理后台

基于 Vue 3 + TypeScript + Vite + Element Plus 构建的 Web 管理后台。

## 技术栈

| 技术 | 说明 |
|------|------|
| Vue 3 | 渐进式 JavaScript 框架 |
| TypeScript | JavaScript 超集，提供类型检查 |
| Vite | 下一代前端构建工具 |
| Element Plus | 基于 Vue 3 的组件库 |
| Vue Router | Vue 官方路由管理 |
| Pinia | Vue 状态管理（预留） |
| ECharts | 数据可视化图表库 |
| SCSS | CSS 预处理器 |

## 项目结构

```
platform_web/
├── src/
│   ├── main.ts                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/
│   │   └── index.ts            # 路由配置
│   ├── layouts/
│   │   └── AdminLayout.vue     # 管理后台主布局
│   ├── views/
│   │   ├── login/
│   │   │   └── LoginView.vue              # 登录页
│   │   ├── dashboard/
│   │   │   └── DashboardView.vue          # 仪表盘
│   │   ├── users/
│   │   │   ├── AdminUsersView.vue       # 管理员管理
│   │   │   └── SubUsersView.vue          # 子用户管理
│   │   ├── templates/
│   │   │   ├── TemplateListView.vue    # 模板列表
│   │   │   └── TemplateEditView.vue     # 模板编辑
│   │   ├── materials/
│   │   │   └── MaterialListView.vue      # 素材库
│   │   ├── generation/
│   │   │   ├── GenerationCreateView.vue  # 创建生成任务
│   │   │   ├── GenerationListView.vue     # 生成任务列表
│   │   │   └── GenerationDetailView.vue   # 任务详情
│   │   ├── distribution/
│   │   │   ├── DistributeView.vue        # 内容分发
│   │   │   └── DistributionListView.vue  # 分发记录
│   │   ├── notifications/
│   │   │   └── NotificationListView.vue   # 站内通知
│   │   └── settings/
│   │       └── SettingsView.vue           # 系统设置
│   ├── api/
│   │   ├── request.ts             # Axios 请求封装
│   │   ├── types.ts             # API 类型定义
│   │   └── *.ts                  # 各模块 API
│   ├── stores/                   # Pinia 状态管理（预留）
│   ├── components/               # 通用组件
│   │   ├── Pagination.vue        # 分页组件
│   │   ├── ImagePreview.vue      # 图片预览
│   │   └── *.vue
│   ├── styles/
│   │   ├── variables.scss        # SCSS 变量
│   │   └── global.scss          # 全局样式
│   └── assets/                   # 静态资源
├── public/                       # 公共资源
├── tests/                       # 测试文件
│   ├── unit/                    # 单元测试
│   └── e2e/                     # E2E 测试
├── package.json
├── vite.config.ts
├── tsconfig.json
├── Dockerfile
└── nginx.conf
```

## 已实现页面

### 1. 登录页 (`/login`)
- 账号密码登录 + 微信扫码登录 Tab 切换
- 品牌展示区域
- 登录失败提示（连续 5 次锁定 15 分钟）

### 2. 主布局
- 左侧侧边栏导航（可折叠）
- 顶部导航栏（面包屑、通知、用户菜单）
- 通知抽屉

### 3. 仪表盘 (`/dashboard`)
- 统计卡片（子用户数、今日生成、待发布、已发布）
- 内容分发趋势图（ECharts）
- 最近生成任务列表
- 失败任务告警

### 4. 用户管理
- **管理员管理** (`/users/admin-users`)
  - 管理员列表、新增、编辑、禁用/启用
  - 资源转移功能（超级管理员）

- **子用户管理** (`/users/sub-users`)
  - 用户分类树 + 标签筛选
  - 子用户列表（卡片/表格视图）
  - 生成邀请码
  - 批量操作

### 5. 模板管理
- **模板列表** (`/templates/list`)
  - 分类树导航
  - 卡片式/列表式视图切换
  - 模板复制、启用/禁用、删除

- **模板编辑** (`/templates/edit/:id`)
  - 多 Tab 表单（基本信息、提示词编辑、变量配置、平台规则、图片/视频配置）

### 6. 素材库 (`/materials`)
- 素材列表（卡片/列表视图）
- 素材上传（文本、图片、视频）
- 素材收藏
- 素材预览和管理

### 7. 内容生成
- **创建生成任务** (`/generation/create`)
  - 7 步骤向导式表单
  - 素材选择 → 模板选择 → 模型配置 → 图片/视频配置 → 变量填充 → 去重规则 → 用户选择 → 确认提交

- **生成任务列表** (`/generation/list`)
  - 任务卡片列表
  - 进度统计和进度条
  - 状态管理

- **任务详情** (`/generation/detail/:id`)
  - 任务概览和进度
  - 子任务列表（暂停/继续/重试）
  - 实时 WebSocket 进度推送
  - 内容预览

### 8. 分发管理
- **内容分发** (`/distribution/distribute`)
  - 生成内容选择
  - 目标子用户选择
  - 分发确认和预览

- **分发记录** (`/distribution/records`)
  - 分发历史列表
  - 发布状态跟踪

### 9. 站内通知 (`/notifications`)
- 通知时间线
- 未读/已读筛选
- 批量已读和清空

### 10. 系统设置 (`/settings`)
- **个人设置**：自定义昵称、修改密码、微信绑定
- **系统设置**（超级管理员）：模型配置、并发设置、过期清理策略

## 设计系统

### 色彩系统

| 用途 | 颜色值 |
|------|--------|
| 主色 | #409EFF |
| 主色深 | #337ECC |
| 成功 | #67C23A |
| 警告 | #E6A23C |
| 危险 | #F56C6C |
| 信息 | #909399 |
| 文字主色 | #303133 |
| 文字副色 | #606266 |
| 文字辅助 | #909399 |
| 背景色 | #F5F7FA |
| 白色 | #FFFFFF |

### 状态色彩

| 状态 | 颜色值 |
|------|--------|
| 排队中 | #909399 |
| 生成中 | #409EFF |
| 已完成 | #67C23A |
| 失败 | #F56C6C |
| 已暂停 | #E6A23C |
| 已分发 | #409EFF |
| 待发布 | #E6A23C |
| 已发布 | #67C23A |

### 字体系统

| 用途 | 字号 | 字重 |
|------|------|------|
| 标题 | 20px | 600 |
| 副标题 | 16px | 500 |
| 正文 | 14px | 400 |
| 辅助文字 | 12px | 400 |

## 快速开始

### 安装依赖

```bash
cd platform_web
npm install
```

### 开发模式运行

```bash
npm run dev
```

访问 http://localhost:5173 查看应用（开发模式）

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 环境变量

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 生产环境
VITE_API_BASE_URL=https://your-domain.com/api/v1
```

## API 代理配置

开发模式下，Vite 会代理 `/api` 请求到后端服务。

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

## E2E 测试

### 运行 E2E 测试

```bash
# 使用 Playwright
npx playwright test

# 打开 Playwright UI
npx playwright test --ui
```

### 测试配置

```typescript
// playwright.config.ts
export default {
  testDir: './tests/e2e',
  baseURL: 'http://localhost:5173',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
}
```

## 常用开发命令

```bash
npm run dev          # 启动开发服务器
npm run build         # 构建生产版本
npm run preview       # 预览生产版本
npm run test          # 运行测试
npm run lint          # 代码检查
npm run lint:fix     # 自动修复代码问题
```

## 组件开发指南

### 新增页面

1. 在 `src/views/` 下创建页面组件
2. 在 `src/router/index.ts` 中添加路由
3. 在侧边栏菜单配置中添加菜单项

### 新增 API

1. 在 `src/api/` 下创建 API 模块
2. 使用 `request.ts` 中的封装方法

```typescript
// src/api/example.ts
import request from './request'

export const getExample = (params: any) => {
  return request.get('/example', { params })
}

export const createExample = (data: any) => {
  return request.post('/example', data)
}
```

### 新增组件

1. 在 `src/components/` 下创建组件
2. 如需全局注册，在 `src/main.ts` 中引入并注册

## 相关文档

- [Web UI 设计文档](../docs/web-ui-design.md)
- [API 设计文档](../docs/api-design.md)
- [项目总 PRD](../docs/media-aigc-platform-prd.md)

## 许可证

Copyright © 2025
