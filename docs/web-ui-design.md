# 妙笔内容工场 - Web UI 页面设计完整文档

## 实现状态概览

### 已实现页面 ✅

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 登录页 | `/login` | ✅ 已实现 | 账号密码登录 |
| 仪表盘 | `/dashboard` | ✅ 已实现 | Tab切换(总览/趋势分析)、角色差异化统计卡片、筛选控件、最近内容/任务列表 |
| 创作管理员 | `/users/admin-users` | ✅ 已实现 | 管理员列表、创建、编辑、禁用 |
| 创作员管理 | `/users/sub-users` | ✅ 已实现 | 创作者列表、邀请码、分类标签、编辑 |
| 模板列表 | `/templates` | ✅ 已实现 | 左侧分类树、卡片/列表双视图、搜索筛选 |
| 模板编辑 | `/templates/edit/:id` | ✅ 已实现 | 多 Tab 表单（基本信息、提示词、变量、规则） |
| 素材库 | `/materials` | ✅ 已实现 | 左侧分类树、卡片/列表双视图、上传编辑 |
| 创建生成任务 | `/generation/create` | ✅ 已实现 | 步骤条导航表单（素材→模板→模型→种子→去重→对标→用户→确认） |
| 生成任务列表 | `/generation` | ✅ 已实现 | 创作者内容卡片视图、管理员任务卡片视图、状态筛选 |
| 生成任务详情 | `/generation/detail/:id` | ✅ 已实现 | 实时进度、批量操作、子任务管理 |
| 创意种子库 | `/settings/creative-seeds` | ✅ 已实现 | 种子列表、类型筛选、创建编辑、系统种子管理 |
| 系统设置 | `/settings` | ✅ 已实现 | 个人设置（昵称、密码）、模型平台配置（9平台）、过期清理策略 |

### 核心组件

| 组件 | 文件路径 | 说明 |
|------|----------|------|
| TrendAnalysisPanel | `components/dashboard/TrendAnalysisPanel.vue` | 趋势分析面板组件 |
| SubUserItemDetailDrawer | `components/generation/SubUserItemDetailDrawer.vue` | 创作者内容详情抽屉组件 |
| ModelConfigDialog | `components/settings/ModelConfigDialog.vue` | 模型配置编辑对话框 |

### 角色权限说明

| 角色 | 权限范围 |
|------|----------|
| super_admin | 全部功能，包括创作创作管理员、模型平台配置、过期清理策略 |
| operator | 模板管理、素材管理、内容生成、创作员管理、模型平台配置查看 |
| sub_user | 查看分发内容、确认发布、个人设置 |

### 设计系统

- **风格**：专业商务、简洁布局、高信息密度
- **UI 库**：Element Plus
- **主色调**：#409EFF（Element Plus 默认蓝色）
- **字体**：Noto Sans

### 状态配色

| 状态 | 颜色值 | 说明 |
|------|--------|------|
| 排队中 | #909399 | queued 状态 |
| 生成中 | #409EFF | generating 状态 |
| 已完成 | #67C23A | completed 状态 |
| 失败 | #F56C6C | failed 状态 |
| 已暂停 | #E6A23C | paused 状态 |
| 已分发 | #409EFF | distributed 状态 |
| 待发布 | #E6A23C | pending_publish 状态 |
| 已发布 | #67C23A | published 状态 |

---

## 概述

本文档基于最新的 API 设计、数据模型和 PRD，补充完善现有 Web UI 页面设计。主要新增和优化：

1. **图片/视频生成配置** - 各页面的尺寸、质量、分辨率等配置
2. **并发控制设计** - 模型并发限制、自适应调节
3. **任务状态管理** - 暂停/继续、批量重试、实时监控
4. **角色差异化设计** - 超级管理员/创作管理员/创作者的不同视图
5. **资源转移功能** - 超级管理员的创作管理员资源转移

---

## 设计系统更新

### 新增配色方案

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 排队中 | #909399 | queued 状态 |
| 生成中 | #409EFF | generating 状态 |
| 已完成 | #67C23A | completed 状态 |
| 失败 | #F56C6C | failed 状态 |
| 已暂停 | #E6A23C | paused 状态 |
| 已分发 | #409EFF | distributed 状态 |
| 待发布 | #E6A23C | pending_publish 状态 |
| 已发布 | #67C23A | published 状态 |

### 新增图标映射

```typescript
// 状态图标
const statusIcons = {
  queued: Clock,
  generating: Loading,
  completed: CircleCheck,
  failed: CircleClose,
  paused: VideoPause,
  distributed: Share,
  pending_publish: AlarmClock,
  published: SuccessFilled
}
```

---

---

## 登录页面设计

### 登录页面

**路由**: `/login`

**功能**:
- 账号密码登录
- 连续5次登录失败锁定账号15分钟
- 支持亮色/暗色主题

#### 页面布局（二分栏设计）

- **左栏（品牌区）**：渐变背景，展示品牌名称、产品描述及三个核心功能特性（内容创作、高效分发、团队协作）
- **右栏（登录区）**：登录表单卡片，包含用户名/密码输入和登录按钮，底部安全提示

#### 设计规范

```scss
// 样式变量（使用全局 CSS 变量，自动适配亮色/暗色主题）

// 品牌区
背景: linear-gradient(160deg, var(--color-primary-bg), var(--color-bg-tertiary), var(--color-bg-primary))
文字: var(--color-text-primary) / var(--color-text-secondary)
特性卡片: 白色半透明 + 边框, hover 时边框高亮 + 阴影加深（无 translateY）

// 表单区
输入框: 大圆角 (14px), focus 时蓝色光晕效果
按钮: 全宽, 48px 高, 圆角 var(--radius-lg)
安全提示: var(--color-text-secondary)

// 响应式
≤1024px: 隐藏品牌区，仅显示登录表单
```
---

## 新增：系统设置模块 - 个人设置

### 个人设置页面

**路由**: `/settings`

**功能**:
- 修改自定义昵称（display_name）
- 修改密码（需验证原密码）

#### 页面布局

```vue
<template>
  <div class="settings-view">
    <h2 class="page-title">系统设置</h2>

    <el-card class="mb-md">
      <el-tabs v-model="activeTab">
        <!-- 个人设置 -->
        <el-tab-pane label="个人设置" name="profile">
          <div class="profile-section">
            <el-form :model="profileForm" label-width="120px" style="max-width: 500px;">
              <!-- 自定义昵称 -->
              <el-form-item label="自定义昵称">
                <el-input v-model="profileForm.display_name" placeholder="设置您的昵称" clearable />
                <div class="form-tip">这个昵称是您在系统中看到的名称，仅自己可见</div>
              </el-form-item>

              <!-- 用户ID（只读） -->
              <el-form-item label="用户ID">
                <el-input v-model="profileForm.userid" disabled />
              </el-form-item>

              <!-- 角色（只读） -->
              <el-form-item label="角色">
                <el-tag :type="getRoleType(profileForm.role)">{{ getRoleLabel(profileForm.role) }}</el-tag>
              </el-form-item>

              <!-- 注册时间（只读） -->
              <el-form-item label="注册时间">
                <span>{{ profileForm.created_at }}</span>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="saveProfile" :loading="profileSaving">
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>

            <el-divider class="my-lg" />

            <!-- 修改密码 -->
            <h4 class="section-title">修改密码</h4>
            <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="120px" style="max-width: 500px;">
              <el-form-item label="原密码" prop="old_password">
                <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password />
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input v-model="passwordForm.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirm_password">
                <el-input v-model="passwordForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="changePassword" :loading="passwordSaving">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>

          </div>
        </el-tab-pane>

        <!-- 系统设置（仅超级管理员） -->
        <el-tab-pane label="系统设置" name="system" v-if="isSuperAdmin">
          <div class="system-section">
            <el-alert title="提示：此处配置为系统全局配置，仅超级管理员可修改" type="info" :closable="false" class="mb-md" />
            <!-- 系统设置内容... -->
          </div>
        </el-tab-pane>

        <!-- 模型配置（仅超级管理员） -->
        <el-tab-pane label="模型配置" name="models" v-if="isSuperAdmin">
          <!-- 模型配置内容（见上文第五章）... -->
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('profile')
const profileSaving = ref(false)
const passwordSaving = ref(false)
const passwordFormRef = ref()

// 用户信息
const profileForm = reactive({
  display_name: '',
  userid: '',
  role: '',
  created_at: ''
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 是否超级管理员
const isSuperAdmin = computed(() => profileForm.role === 'super_admin')

// 密码验证规则
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const getRoleType = (role: string) => {
  const types: Record<string, string> = {
    super_admin: 'danger',
    operator: 'warning',
    sub_user: 'info'
  }
  return types[role] || 'info'
}

const getRoleLabel = (role: string) => {
  const labels: Record<string, string> = {
    super_admin: '超级管理员',
    operator: '创作管理员',
    sub_user: '创作者'
  }
  return labels[role] || role
}

const saveProfile = async () => {
  profileSaving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('保存成功')
  } finally {
    profileSaving.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      passwordSaving.value = true
      try {
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('密码修改成功，请重新登录')
        // 清空表单
        Object.assign(passwordForm, { old_password: '', new_password: '', confirm_password: '' })
      } finally {
        passwordSaving.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.settings-view {
  .profile-section {
    padding: 8px 0;
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 20px;
  }

  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }

  .my-lg {
    margin: 24px 0;
  }
}

.mb-md {
  margin-bottom: 16px;
}
</style>
```

---

## 一、用户管理模块

### 1.1 超级管理员 - 创作管理员列表页面

**路由**: `/users/admin-users`

**新增功能**:
- 创作管理员资源统计卡片
- 资源转移功能入口
- 用户转移记录查看

#### 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  页面标题: 创作创作管理员                                      [新增] │
├─────────────────────────────────────────────────────────────────────┤
│  [统计卡片区]                                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 总创作管理员 │ │ 总创作者数  │ │ 总模板数    │ │ 总素材数    │ │
│  │     12      │ │    1,234    │ │     456     │ │     789     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                     │
│  [工具栏]                                                            │
│  [搜索输入框] [标签筛选] [状态筛选]          [新增创作管理员] [转移资源] │
│                                                                     │
│  [表格区]                                                            │
│  ┌────┬────────┬────────┬───────┬───────┬───────┬───────┬────────┐ │
│  │选  │管理员  │用户定  │创作者 │模板   │素材   │状态   │操作    │ │
│  │择  │ID/昵称 │位      │数     │数     │数     │       │        │ │
│  ├────┼────────┼────────┼───────┼───────┼───────┼───────┼────────┤ │
│  │☑   │A001    │美妆    │  156  │  45   │  89   │在线   │[编] [转]│ │
│  │    │张小明   │线      │       │       │       │       │[辑] [移]│ │
│  ├────┼────────┼────────┼───────┼───────┼───────┼───────┼────────┤ │
│  │☐   │A002    │母婴    │  234  │  67   │  123  │在线   │[编] [转]│ │
│  │    │李小红   │线      │       │       │       │       │[辑] [移]│ │
│  └────┴────────┴────────┴───────┴───────┴───────┴───────┴────────┘ │
│                                                                     │
│  [分页]                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

#### 资源转移对话框

```typescript
// 资源转移对话框组件
interface ResourceTransferDialog {
  visible: boolean
  step: 1 | 2 | 3  // 1:选择源和目标, 2:预览, 3:完成
  fromAdminId?: number
  toAdminId?: number
  resourceTypes: ('templates' | 'materials' | 'subusers')[]
  selectedTemplateIds?: number[]
  selectedMaterialIds?: number[]
  selectedSubuserIds?: number[]
}
```

**转移步骤**:
1. **选择源和目标** - 选择转出和转入的创作管理员
2. **选择资源类型** - 勾选要转移的资源类型（模板/素材/创作者）
3. **预览冲突** - 显示平台/标签冲突及处理策略
4. **确认转移** - 执行转移操作

---

### 1.2 创作管理员 - 创作员管理页面

**路由**: `/users/sub-users`

**优化功能**:
- 创作者个性化配置（文案风格、账号类型）
- 高级筛选（按风格、类型筛选）
- 批量操作（批量转移、批量打标签）

#### 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  页面标题: 创作员管理                          [生成邀请码] [批量操作] │
├─────────────────────────────────────────────────────────────────────┤
│  [左侧分类树]          [主内容区]                                  │
│  ┌─────────────┐      ┌──────────────────────────────────────────┐ │
│  │📋 全部分类   │      │ [工具栏]                                │ │
│  │  ├ 美妆号   │      │ [搜索] [标签] [风格] [类型] [状态]   │ │
│  │  ├ 母婴号   │      │                                          │ │
│  │  ├ 团购号   │      │ [视图切换: 卡片|列表] [批量选择]      │ │
│  │  └ ...      │      └──────────────────────────────────────────┘ │
│  └─────────────┘      ┌──────────────────────────────────────────┐ │
│                       │                                          │ │
│  [左侧标签树]          │ [创作者卡片网格]                       │ │
│  ┌─────────────┐      │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│ │
│  │🏷️ 全部标签   │      │ │用户1 │ │用户2 │ │用户3 │ │...   ││ │
│  │  ├ 北京团队 │      │ └──────┘ └──────┘ └──────┘ └──────┘│ │
│  │  ├ 上海团队 │      │                                          │ │
│  │  └ ...      │      │ [分页]                                 │ │
│  └─────────────┘      └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

#### 创作者卡片设计

```vue
<template>
  <div class="subuser-card">
    <div class="card-header">
      <el-avatar :size="48">{{ nickname[0] }}</el-avatar>
      <div class="user-info">
        <div class="nickname">{{ nickname }}</div>
        <div class="userid">{{ userid }}</div>
      </div>
      <el-tag :type="status === 'online' ? 'success' : 'info'" size="small">
        {{ status === 'online' ? '在线' : '离线' }}
      </el-tag>
    </div>

    <div class="card-body">
      <div class="info-row" v-if="user_positioning">
        <el-icon><Location /></el-icon>
        <span>{{ user_positioning }}</span>
      </div>
      <div class="info-row" v-if="content_style">
        <el-icon><Document /></el-icon>
        <span>文案: {{ content_style }}</span>
      </div>
      <div class="info-row" v-if="account_type">
        <el-icon><User /></el-icon>
        <span>类型: {{ account_type }}</span>
      </div>
      <div class="tags">
        <el-tag v-for="tag in tags" :key="tag.id" size="small" :color="tag.color">
          {{ tag.name }}
        </el-tag>
      </div>
    </div>

    <div class="card-footer">
      <div class="stats">
        <span>待发布: {{ pendingPublishCount }}</span>
        <span>已发布: {{ publishedCount }}</span>
      </div>
      <el-dropdown>
        <el-button link>操作</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="editUser">编辑</el-dropdown-item>
            <el-dropdown-item @click="viewContent">查看内容</el-dropdown-item>
            <el-dropdown-item @click="resetPassword">重置密码</el-dropdown-item>
            <el-dropdown-item divided @click="disableUser" :type="status === 'disabled' ? '' : 'danger'">
              {{ status === 'disabled' ? '启用' : '禁用' }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>
```

#### 创作者编辑对话框 - 个性化配置

```typescript
// 文案风格预设选项
const contentStyleOptions = [
  { label: '幽默风趣', value: '幽默风趣' },
  { label: '专业严谨', value: '专业严谨' },
  { label: '温馨亲切', value: '温馨亲切' },
  { label: '活泼可爱', value: '活泼可爱' },
  { label: '文艺清新', value: '文艺清新' },
  { label: '霸气干练', value: '霸气干练' },
  { label: '哲理思考', value: '哲理思考' }
]

// 账号类型预设选项
const accountTypeOptions = [
  { label: '宝妈好物分享', value: '宝妈好物分享' },
  { label: '旅游爱好者', value: '旅游爱好者' },
  { label: '美食探店', value: '美食探店' },
  { label: '科技测评', value: '科技测评' },
  { label: '时尚穿搭', value: '时尚穿搭' },
  { label: '美妆博主', value: '美妆博主' },
  { label: '健身达人', value: '健身达人' },
  { label: '职场经验', value: '职场经验' },
  { label: '情感咨询师', value: '情感咨询师' },
  { label: '家居装饰', value: '家居装饰' }
]
```

---

## 二、模板管理模块

### 2.1 模板编辑页面 - 新增图片/视频配置

**路由**: `/templates/edit/:id`

**新增 Tab**: 图片/视频配置

#### 新增 Tab 设计

```vue
<el-tab-pane label="图片/视频配置" name="media-config">
  <div class="media-config">
    <el-alert
      title="此处配置为模板的默认值，创建生成任务时可覆盖"
      type="info"
      :closable="false"
      class="mb-md"
    />

    <!-- 图片配置 -->
    <div class="config-section" v-if="['image_text', 'video_text'].includes(templateForm.contentType)">
      <h4 class="section-title">
        <el-icon><Picture /></el-icon>
        图片生成配置
      </h4>
      <el-form label-width="140px">
        <!-- 快速预设 -->
        <el-form-item label="平台预设">
          <el-radio-group v-model="imagePreset">
            <el-radio-button label="xiaohongshu">小红书</el-radio-button>
            <el-radio-button label="douyin">抖音</el-radio-button>
            <el-radio-button label="gongzhonghao">公众号</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 尺寸比例 -->
        <el-form-item label="图片尺寸">
          <el-radio-group v-model="templateForm.default_image_config.size">
            <el-radio label="1:1">
              <div class="ratio-preview square-1-1"></div>
              1:1
            </el-radio>
            <el-radio label="3:4">
              <div class="ratio-preview square-3-4"></div>
              3:4
            </el-radio>
            <el-radio label="4:3">
              <div class="ratio-preview square-4-3"></div>
              4:3
            </el-radio>
            <el-radio label="9:16">
              <div class="ratio-preview square-9-16"></div>
              9:16
            </el-radio>
            <el-radio label="16:9">
              <div class="ratio-preview square-16-9"></div>
              16:9
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 自定义尺寸 -->
        <el-form-item label="自定义尺寸" v-if="templateForm.default_image_config.size === 'custom'">
          <el-input-number v-model="templateForm.default_image_config.width" :min="256" :max="4096" />
          <span style="margin: 0 8px;">×</span>
          <el-input-number v-model="templateForm.default_image_config.height" :min="256" :max="4096" />
          <span style="margin-left: 8px; color: #909399;">像素</span>
        </el-form-item>

        <!-- 图片质量 -->
        <el-form-item label="图片质量">
          <el-radio-group v-model="templateForm.default_image_config.quality">
            <el-radio label="low">低质量</el-radio>
            <el-radio label="medium">中等</el-radio>
            <el-radio label="high">高质量</el-radio>
            <el-radio label="ultra">超高清</el-radio>
          </el-radio-group>
          <div class="quality-hint" style="margin-top: 8px; color: #909399; font-size: 12px;">
            <span v-if="templateForm.default_image_config.quality === 'low'">约 100-300KB，适合预览测试</span>
            <span v-else-if="templateForm.default_image_config.quality === 'medium'">约 300-800KB，日常使用推荐</span>
            <span v-else-if="templateForm.default_image_config.quality === 'high'">约 800KB-2MB，正式发布推荐</span>
            <span v-else-if="templateForm.default_image_config.quality === 'ultra'">约 2-5MB，专业用途</span>
          </div>
        </el-form-item>

        <!-- 图片风格 -->
        <el-form-item label="图片风格">
          <el-select v-model="templateForm.default_image_config.style" placeholder="选择图片风格（可选）" clearable style="width: 300px;">
            <el-option label="写实风格" value="realistic" />
            <el-option label="卡通风格" value="cartoon" />
            <el-option label="油画风格" value="oil_painting" />
            <el-option label="水彩风格" value="watercolor" />
            <el-option label="二次元风格" value="anime" />
            <el-option label="3D渲染" value="3d_render" />
            <el-option label="摄影风格" value="photography" />
            <el-option label="手绘风格" value="hand_drawn" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 视频配置 -->
    <div class="config-section mt-lg" v-if="templateForm.contentType === 'video_text'">
      <h4 class="section-title">
        <el-icon><VideoCamera /></el-icon>
        视频生成配置
      </h4>
      <el-form label-width="140px">
        <!-- 快速预设 -->
        <el-form-item label="平台预设">
          <el-radio-group v-model="videoPreset">
            <el-radio-button label="douyin">抖音/快手</el-radio-button>
            <el-radio-button label="shipinhao">视频号</el-radio-button>
            <el-radio-button label="bilibili">B站/YouTube</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 宽高比 -->
        <el-form-item label="视频宽高比">
          <el-radio-group v-model="templateForm.default_video_config.aspect_ratio">
            <el-radio label="9:16">
              <div class="ratio-preview square-9-16"></div>
              9:16 竖屏
            </el-radio>
            <el-radio label="16:9">
              <div class="ratio-preview square-16-9"></div>
              16:9 横屏
            </el-radio>
            <el-radio label="1:1">
              <div class="ratio-preview square-1-1"></div>
              1:1 正方形
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 分辨率 -->
        <el-form-item label="视频分辨率">
          <el-radio-group v-model="templateForm.default_video_config.resolution">
            <el-radio label="720p">720p (1280×720)</el-radio>
            <el-radio label="1080p">1080p (1920×1080)</el-radio>
            <el-radio label="4k">4K (3840×2160)</el-radio>
          </el-radio-group>
          <div class="resolution-hint" style="margin-top: 8px; color: #909399; font-size: 12px;">
            <span v-if="templateForm.default_video_config.resolution === '720p'">适合网络传播，推荐码率 2-4 Mbps</span>
            <span v-else-if="templateForm.default_video_config.resolution === '1080p'">高清视频，正式发布推荐，推荐码率 5-10 Mbps</span>
            <span v-else-if="templateForm.default_video_config.resolution === '4k'">超高清，专业制作，推荐码率 16-40 Mbps</span>
          </div>
        </el-form-item>

        <!-- 帧率 -->
        <el-form-item label="视频帧率">
          <el-radio-group v-model="templateForm.default_video_config.fps">
            <el-radio :label="24">24 fps 电影感</el-radio>
            <el-radio :label="30">30 fps 标准</el-radio>
            <el-radio :label="60">60 fps 高帧率</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 视频时长 -->
        <el-form-item label="视频时长">
          <el-input-number v-model="templateForm.default_video_config.duration" :min="5" :max="300" />
          <span style="margin-left: 8px; color: #909399;">秒</span>
        </el-form-item>

        <!-- 视频风格 -->
        <el-form-item label="视频风格">
          <el-select v-model="templateForm.default_video_config.style" placeholder="选择视频风格（可选）" clearable style="width: 300px;">
            <el-option label="写实风格" value="realistic" />
            <el-option label="卡通动画" value="cartoon" />
            <el-option label="定格动画" value="stop_motion" />
            <el-option label="手绘风格" value="hand_drawn" />
            <el-option label="3D动画" value="3d_animation" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
  </div>
</el-tab-pane>

<script setup lang="ts">
import { watch } from 'vue'

// 平台预设配置
const platformPresets = {
  xiaohongshu: {
    image: { size: '3:4', quality: 'high', width: 1080, height: 1440 }
  },
  douyin: {
    image: { size: '9:16', quality: 'high', width: 1080, height: 1920 },
    video: { aspect_ratio: '9:16', resolution: '1080p', fps: 30, duration: 15 }
  },
  gongzhonghao: {
    image: { size: '16:9', quality: 'medium', width: 1280, height: 720 }
  },
  shipinhao: {
    video: { aspect_ratio: '9:16', resolution: '1080p', fps: 30, duration: 30 }
  },
  bilibili: {
    video: { aspect_ratio: '16:9', resolution: '1080p', fps: 30, duration: 60 }
  }
}

const imagePreset = ref('custom')
const videoPreset = ref('custom')

// 监听图片预设变化
watch(imagePreset, (preset) => {
  if (preset !== 'custom' && platformPresets[preset as keyof typeof platformPresets]?.image) {
    Object.assign(templateForm.default_image_config, platformPresets[preset as keyof typeof platformPresets].image!)
  }
})

// 监听视频预设变化
watch(videoPreset, (preset) => {
  if (preset !== 'custom' && platformPresets[preset as keyof typeof platformPresets]?.video) {
    Object.assign(templateForm.default_video_config, platformPresets[preset as keyof typeof platformPresets].video!)
  }
})
</script>

<style lang="scss" scoped>
.media-config {
  padding: 8px 0;
}

.config-section {
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
  }
}

.ratio-preview {
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  background: #f5f7fa;
}

.square-1-1 { width: 20px; height: 20px; }
.square-3-4 { width: 15px; height: 20px; }
.square-4-3 { width: 20px; height: 15px; }
.square-9-16 { width: 11px; height: 20px; }
.square-16-9 { width: 20px; height: 11px; }

.mt-lg {
  margin-top: 24px;
}

.mb-md {
  margin-bottom: 16px;
}
</style>
```

---

## 三、内容生成模块

### 3.1 创建生成任务页面 - 优化

**路由**: `/generation/create`

**新增/优化**:
- 步骤 3 "配置模型" 增加并发控制配置
- 新增步骤 "图片/视频配置"（在模型配置之后）
- 步骤 7 确认页面增加预估时长和成本

#### 优化后的步骤

```typescript
// 步骤调整
const steps = [
  '选择素材',
  '选择模板',
  '配置模型',
  '图片/视频配置',  // 新增
  '填充变量',
  '去重规则',
  '选择用户',
  '确认提交'
]
```

#### 新增步骤 4: 图片/视频配置

```vue
<div v-if="currentStep === 3" class="step-panel">
  <h3 class="step-title">步骤 4：图片/视频配置</h3>

  <el-alert
    v-if="hasImageTemplate || hasVideoTemplate"
    title="根据选择的模板，配置图片/视频生成参数"
    type="info"
    :closable="false"
    class="mb-md"
  />
  <el-alert
    v-else
    title="当前选择的模板不包含图片/视频生成，可跳过此步骤"
    type="warning"
    :closable="false"
    class="mb-md"
  />

  <!-- 图片配置 -->
  <div class="config-section" v-if="hasImageTemplate">
    <h4 class="section-title">
      <el-icon><Picture /></el-icon>
      图片生成配置
    </h4>

    <!-- 快速预设 -->
    <div class="preset-buttons mb-md">
      <el-button
        v-for="preset in imagePresets"
        :key="preset.value"
        :type="imageConfigPreset === preset.value ? 'primary' : 'default'"
        @click="applyImagePreset(preset)"
      >
        {{ preset.label }}
      </el-button>
    </div>

    <el-form label-width="140px" style="max-width: 600px;">
      <el-form-item label="尺寸比例">
        <el-radio-group v-model="imageConfig.size">
          <el-radio label="1:1">1:1 (正方形)</el-radio>
          <el-radio label="3:4">3:4 (小红书)</el-radio>
          <el-radio label="9:16">9:16 (抖音)</el-radio>
          <el-radio label="16:9">16:9 (横版)</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="图片质量">
        <el-select v-model="imageConfig.quality" style="width: 200px;">
          <el-option label="低质量 (预览)" value="low" />
          <el-option label="中等质量" value="medium" />
          <el-option label="高质量 (推荐)" value="high" />
          <el-option label="超高质量" value="ultra" />
        </el-select>
      </el-form-item>

      <el-form-item label="图片风格">
        <el-select v-model="imageConfig.style" placeholder="可选" clearable style="width: 200px;">
          <el-option label="写实风格" value="realistic" />
          <el-option label="卡通风格" value="cartoon" />
          <el-option label="油画风格" value="oil_painting" />
        </el-select>
      </el-form-item>
    </el-form>

    <!-- 配置预览 -->
    <div class="config-preview mt-md">
      <div class="preview-title">配置预览</div>
      <div class="preview-content">
        <div class="preview-image-box" :style="getPreviewBoxStyle(imageConfig)">
          <div class="preview-placeholder">
            <el-icon :size="40"><Picture /></el-icon>
            <div>{{ imageConfig.size }}</div>
          </div>
        </div>
        <div class="preview-info">
          <div class="info-item">
            <span class="label">预计文件大小:</span>
            <span class="value">{{ getEstimatedImageSize(imageConfig) }}</span>
          </div>
          <div class="info-item">
            <span class="label">适用平台:</span>
            <span class="value">{{ getSuitablePlatforms(imageConfig) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 视频配置 -->
  <div class="config-section mt-lg" v-if="hasVideoTemplate">
    <h4 class="section-title">
      <el-icon><VideoCamera /></el-icon>
      视频生成配置
    </h4>

    <!-- 快速预设 -->
    <div class="preset-buttons mb-md">
      <el-button
        v-for="preset in videoPresets"
        :key="preset.value"
        :type="videoConfigPreset === preset.value ? 'primary' : 'default'"
        @click="applyVideoPreset(preset)"
      >
        {{ preset.label }}
      </el-button>
    </div>

    <el-form label-width="140px" style="max-width: 600px;">
      <el-form-item label="宽高比">
        <el-radio-group v-model="videoConfig.aspect_ratio">
          <el-radio label="9:16">9:16 (竖屏)</el-radio>
          <el-radio label="16:9">16:9 (横屏)</el-radio>
          <el-radio label="1:1">1:1 (正方形)</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="分辨率">
        <el-select v-model="videoConfig.resolution" style="width: 200px;">
          <el-option label="720p (网络传播)" value="720p" />
          <el-option label="1080p (高清推荐)" value="1080p" />
          <el-option label="4K (超高清)" value="4k" />
        </el-select>
      </el-form-item>

      <el-form-item label="帧率">
        <el-radio-group v-model="videoConfig.fps">
          <el-radio :label="24">24 fps</el-radio>
          <el-radio :label="30">30 fps</el-radio>
          <el-radio :label="60">60 fps</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="视频时长">
        <el-input-number v-model="videoConfig.duration" :min="5" :max="300" />
        <span style="margin-left: 8px;">秒</span>
      </el-form-item>
    </el-form>
  </div>
</div>
```

#### 优化后的步骤 3: 配置模型（增加并发控制）

```vue
<div v-if="currentStep === 2" class="step-panel">
  <h3 class="step-title">步骤 3：配置模型</h3>

  <el-form label-width="160px" style="max-width: 700px;">
    <!-- 模型选择模式 -->
    <el-form-item label="模型选择模式">
      <el-radio-group v-model="modelConfig.mode">
        <el-radio label="auto">
          <div class="radio-option">
            <div class="option-title">自动选择（推荐）</div>
            <div class="option-desc">系统根据各平台并发情况智能切换，最大化生成效率</div>
          </div>
        </el-radio>
        <el-radio label="manual">
          <div class="radio-option">
            <div class="option-title">手动指定</div>
            <div class="option-desc">使用指定的模型平台，遇到并发限制时等待重试</div>
          </div>
        </el-radio>
      </el-radio-group>
    </el-form-item>

    <!-- 手动选择模型 -->
    <template v-if="modelConfig.mode === 'manual'">
      <el-form-item label="语言模型">
        <el-select v-model="modelConfig.llm_model" placeholder="选择语言模型" style="width: 100%;">
          <el-option-group
            v-for="platform in llmPlatforms"
            :key="platform.platform"
            :label="platform.platform_name"
          >
            <el-option
              v-for="model in platform.models"
              :key="model.model_id"
              :value="model"
            >
              <span>{{ model.model_name }}</span>
              <span class="model-meta">
                (并发: {{ model.max_concurrency }})
              </span>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="图片模型" v-if="hasImageTemplate">
        <el-select v-model="modelConfig.image_model" placeholder="选择图片模型" style="width: 100%;">
          <el-option-group
            v-for="platform in imagePlatforms"
            :key="platform.platform"
            :label="platform.platform_name"
          >
            <el-option
              v-for="model in platform.models"
              :key="model.model_id"
              :value="model"
            >
              <span>{{ model.model_name }}</span>
              <span class="model-meta">
                (并发: {{ model.max_concurrency }})
              </span>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="视频模型" v-if="hasVideoTemplate">
        <el-select v-model="modelConfig.video_model" placeholder="选择视频模型" style="width: 100%;">
          <el-option-group
            v-for="platform in videoPlatforms"
            :key="platform.platform"
            :label="platform.platform_name"
          >
            <el-option
              v-for="model in platform.models"
              :key="model.model_id"
              :value="model"
            >
              <span>{{ model.model_name }}</span>
              <span class="model-meta">
                (并发: {{ model.max_concurrency }})
              </span>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>
    </template>

    <!-- 并发控制 -->
    <el-divider />
    <el-form-item label="最大并发数">
      <el-slider
        v-model="modelConfig.max_concurrency"
        :min="1"
        :max="getMaxConcurrencyLimit()"
        :step="1"
        :show-tooltip="true"
        style="width: 300px;"
      />
      <span style="margin-left: 12px; color: #909399;">
        当前: {{ modelConfig.max_concurrency }} 并发
      </span>
    </el-form-item>

    <!-- 并发说明 -->
    <el-alert
      title="并发说明"
      type="info"
      :closable="false"
      class="mt-md"
    >
      <template #default>
        <ul class="concurrency-notes">
          <li>根据选择的模型平台，最大并发限制为: <strong>{{ getMaxConcurrencyLimit() }}</strong></li>
          <li>预估完成 {{ selectedUsers.length }} 个创作者需要: <strong>{{ getEstimatedDuration() }}</strong></li>
          <li>建议值: 系统默认推荐值，平衡效率和稳定性</li>
        </ul>
      </template>
    </el-alert>
  </el-form>
</div>

<style lang="scss" scoped>
.radio-option {
  .option-title {
    font-weight: 500;
    margin-bottom: 4px;
  }
  .option-desc {
    font-size: 12px;
    color: #909399;
  }
}

.model-meta {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.concurrency-notes {
  margin: 0;
  padding-left: 16px;
  li {
    margin: 4px 0;
  }
}

.mt-md {
  margin-top: 16px;
}
</style>
```

#### 优化后的步骤 8: 确认提交（增加预估信息）

```vue
<div v-if="currentStep === 7" class="step-panel">
  <h3 class="step-title">步骤 8：确认提交</h3>

  <div class="confirmation-summary">
    <!-- 预估信息卡片 -->
    <el-card class="estimation-card mb-md">
      <template #header>
        <div class="card-header">
          <el-icon><TrendCharts /></el-icon>
          <span>任务预估</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="est-item">
            <div class="est-label">创作者数</div>
            <div class="est-value">{{ selectedUsers.length }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="est-item">
            <div class="est-label">模板数</div>
            <div class="est-value">{{ selectedTemplates.length }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="est-item">
            <div class="est-label">总子任务数</div>
            <div class="est-value highlight">{{ totalItemCount }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="est-item">
            <div class="est-label">预估时长</div>
            <div class="est-value highlight">{{ estimatedDuration }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 配置详情 -->
    <el-descriptions :column="2" border class="mb-md">
      <el-descriptions-item label="选择素材">
        {{ selectedMaterial?.title || '未选择' }}
      </el-descriptions-item>
      <el-descriptions-item label="使用模板">
        {{ selectedTemplates.map(t => t.name).join(', ') }}
      </el-descriptions-item>
      <el-descriptions-item label="模型配置">
        <template v-if="modelConfig.mode === 'auto'">
          <el-tag type="success">自动选择</el-tag>
        </template>
        <template v-else>
          语言: {{ modelConfig.llm_model?.model_name }}<br>
          <span v-if="modelConfig.image_model">图片: {{ modelConfig.image_model?.model_name }}</span><br>
          <span v-if="modelConfig.video_model">视频: {{ modelConfig.video_model?.model_name }}</span>
        </template>
      </el-descriptions-item>
      <el-descriptions-item label="并发设置">
        {{ modelConfig.max_concurrency }} 并发
      </el-descriptions-item>
      <el-descriptions-item label="图片配置" v-if="hasImageTemplate">
        尺寸: {{ imageConfig.size }} | 质量: {{ imageConfig.quality }}
      </el-descriptions-item>
      <el-descriptions-item label="视频配置" v-if="hasVideoTemplate">
        分辨率: {{ videoConfig.resolution }} | 时长: {{ videoConfig.duration }}s
      </el-descriptions-item>
      <el-descriptions-item label="目标创作者" :span="2">
        {{ selectedUsers.length }} 个创作者
        <template v-if="selectedUsers.length <= 5">
          ({{ selectedUsers.map(u => u.nickname).join(', ') }})
        </template>
      </el-descriptions-item>
    </el-descriptions>

    <!-- 温馨提示 -->
    <el-alert
      title="温馨提示"
      type="info"
      show-icon
      class="mt-lg"
    >
      <ul>
        <li>提交后系统将开始后台生成任务，您可以在任务列表查看实时进度</li>
        <li>任务执行过程中可以暂停/继续子任务，或对失败项进行重试</li>
        <li>任务完成后可将内容分发给创作者</li>
      </ul>
    </el-alert>
  </div>
</div>

<style lang="scss" scoped">
.estimation-card {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }

  .est-item {
    text-align: center;
    .est-label {
      color: #909399;
      font-size: 12px;
      margin-bottom: 4px;
    }
    .est-value {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      &.highlight {
        color: #409EFF;
      }
    }
  }
}

.mb-md {
  margin-bottom: 16px;
}

.mt-lg {
  margin-top: 24px;
}
</style>
```

---

### 3.2 生成任务列表页面

**路由**: `/generation`

**角色差异化设计**:
- **创作者**: 显示"我的内容"列表,包含标题、正文、话题、图片预览
- **管理员**: 显示"生成任务列表",包含任务卡片、进度统计、筛选功能

#### 创作者视图 - 内容卡片列表

```vue
<template v-if="isSubUser">
  <h2 class="page-title">我的内容</h2>
  
  <div class="toolbar flex-between mb-md">
    <div class="toolbar-left flex gap-md">
      <el-select v-model="subUserSearchStatus" placeholder="状态筛选" style="width: 140px;">
        <el-option label="全部" value="" />
        <el-option label="待发布" value="pending_publish" />
        <el-option label="已发布" value="published" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="handleSubUserSearch">搜索</el-button>
    </div>
  </div>

  <div class="sub-user-item-list" v-loading="subUserLoading">
    <el-empty v-if="subUserItems.length === 0" description="暂无内容" />
    <el-card v-for="item in subUserItems" :key="item.id" class="sub-user-item-card mb-md" shadow="hover">
      <div class="item-header flex-between">
        <div class="item-title">
          <span class="task-name">{{ item.taskName || '任务 #' + item.task_id }}</span>
          <el-tag :type="getSubUserItemStatusType(item)" size="small" style="margin-left: 12px;">
            {{ getSubUserItemStatusLabel(item) }}
          </el-tag>
        </div>
        <div class="item-time">{{ formatDate(item.created_at) }}</div>
      </div>
      
      <div class="item-content mt-md">
        <!-- 标题 -->
        <div v-if="item.generated_title" class="content-row title-row">
          <span class="row-label">📌 标题</span>
          <span class="row-value title-value">{{ item.generated_title }}</span>
        </div>
        
        <!-- 正文 -->
        <div v-if="item.generated_text" class="content-row text-row">
          <span class="row-label">📄 正文</span>
          <span class="row-value text-value">
            {{ item.generated_text.length > 150 ? item.generated_text.substring(0, 150) + '...' : item.generated_text }}
          </span>
        </div>
        
        <!-- 话题 -->
        <div v-if="parseTopics(item.output_topics).length > 0" class="content-row topics-row">
          <span class="row-label">🏷️ 话题</span>
          <div class="row-value topics-value">
            <el-tag v-for="(tag, idx) in parseTopics(item.output_topics).slice(0, 3)" :key="idx" type="warning" size="small" class="topic-mini-tag">
              #{{ tag }}
            </el-tag>
            <span v-if="parseTopics(item.output_topics).length > 3" class="more-topics">
              +{{ parseTopics(item.output_topics).length - 3 }}
            </span>
          </div>
        </div>
        
        <!-- 图片预览 -->
        <div v-if="item.generated_image_urls_json && item.generated_image_urls_json.length > 0" class="content-row images-row">
          <span class="row-label">🖼️ 图片</span>
          <div class="row-value images-value">
            <div class="image-thumbs">
              <el-image
                v-for="(img, idx) in (item.generated_image_thumbnails_json || item.generated_image_urls_json).slice(0, 4)"
                :key="idx"
                :src="img"
                class="image-thumb"
                fit="cover"
                preview-teleported
                :preview-src-list="item.generated_image_urls_json"
                :initial-index="idx"
              />
              <div v-if="item.generated_image_urls_json.length > 4" class="more-images">
                +{{ item.generated_image_urls_json.length - 4 }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="item-footer flex-between mt-sm">
        <div class="item-meta">
          <span class="meta-item id-tag">内容 #{{ item.id }}</span>
        </div>
        <div class="item-actions">
          <el-button type="primary" link @click="viewSubUserItemDetail(item)">查看详情</el-button>
        </div>
      </div>
    </el-card>
  </div>

  <div class="pagination mt-lg flex-between">
    <span class="total-text">共 {{ subUserTotal }} 条记录</span>
    <el-pagination
      v-model:current-page="subUserCurrentPage"
      v-model:page-size="subUserPageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="subUserTotal"
      layout="total, sizes, prev, pager, next, jumper"
    />
  </div>
</template>
```

#### 管理员视图 - 任务列表

```vue
<template v-else>
  <h2 class="page-title">生成任务列表</h2>
  
  <div class="toolbar flex-between mb-md">
    <div class="toolbar-left flex gap-md">
      <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 140px;">
        <el-option label="排队中" value="pending" />
        <el-option label="生成中" value="processing" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务ID/名称"
        :prefix-icon="Search"
        clearable
        style="width: 240px;"
      />
      <!-- 超级管理员：创作管理员筛选 -->
      <el-select
        v-if="isSuperAdmin"
        v-model="selectedOperatorId"
        placeholder="选择管理员"
        clearable
        style="width: 150px"
      >
        <el-option
          v-for="op in operatorList"
          :key="op.id"
          :label="op.name"
          :value="op.id"
        />
      </el-select>
      <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
    </div>
    <div class="toolbar-right">
      <el-button v-if="!isSuperAdmin" type="primary" :icon="Plus" @click="goToCreate">创建任务</el-button>
    </div>
  </div>

  <div class="task-list" v-loading="loading">
    <el-empty v-if="tasks.length === 0" description="暂无任务数据" />
    <el-card v-for="task in tasks" :key="task.id" class="task-card mb-md" shadow="hover">
      <div class="task-header flex-between">
        <div class="task-title">
          <span class="task-id">#{{ task.id }}</span>
          <span class="task-name">{{ task.name || task.material?.title || '素材 #' + task.material?.id || '-' }}</span>
          <el-tag :type="getStatusType(task.status)" size="small" style="margin-left: 12px;">
            {{ getStatusLabel(task.status) }}
          </el-tag>
        </div>
        <div class="task-time">{{ formatDate(task.created_at) }}</div>
      </div>
      
      <!-- 任务进度 -->
      <div class="task-progress mt-md">
        <el-progress :percentage="task.progress || 0" :stroke-width="8" />
        <div class="progress-stats">
          <span>已完成: {{ task.completed_count || 0 }} / {{ task.total_count || 0 }}</span>
        </div>
      </div>
      
      <!-- 任务详情 -->
      <div class="task-footer flex-between mt-sm">
        <div class="task-meta">
          <span>子任务: {{ task.total_count || 0 }}</span>
          <span class="dot">·</span>
          <span>模板: {{ task.template_name || '-' }}</span>
        </div>
        <el-button type="primary" link size="small" @click="goToTaskDetail(task.id)">查看详情</el-button>
      </div>
    </el-card>
  </div>
</template>
```

---

### 3.3 生成任务详情页面 - 优化

**路由**: `/generation/detail/:id`

**新增/优化**:
- 实时进度 WebSocket 连接
- 子任务暂停/继续批量操作
- 时间统计展示（排队时间、生成耗时）
- 分发功能入口
- 进度历史图表

#### 页面顶部 - 任务概览优化

```vue
<template>
  <div class="generation-detail-view">
    <!-- 页面头部 -->
    <div class="page-header flex-between mb-md">
      <div>
        <el-page-header @back="goBack" title="返回列表">
          <template #content>
            <span class="page-title">
              <el-tag :type="getStatusType(task.status)" size="large" class="mr-md">
                {{ task.statusLabel }}
              </el-tag>
              {{ task.name }}
            </span>
          </template>
        </el-page-header>
      </div>
      <div class="header-actions">
        <!-- 实时连接状态 -->
        <div class="ws-status" :class="{ connected: wsConnected }">
          <span class="dot"></span>
          <span>{{ wsConnected ? '实时同步中' : '连接断开' }}</span>
        </div>

        <!-- 操作按钮 -->
        <template v-if="task.status === 'processing'">
          <el-button type="warning" :icon="VideoPause" @click="pauseAllTasks">
            全部暂停
          </el-button>
          <el-button type="danger" :icon="Close" @click="cancelTask">
            取消任务
          </el-button>
        </template>
        <template v-else-if="task.status === 'completed'">
          <el-button type="success" :icon="Share" @click="openDistributeDialog">
            批量分发
          </el-button>
        </template>
        <template v-if="task.failed_count > 0">
          <el-button type="warning" :icon="Refresh" @click="retryAllFailed">
            重试失败 ({{ task.failed_count }})
          </el-button>
        </template>
      </div>
    </div>

    <!-- 任务概览卡片 -->
    <el-row :gutter="20" class="mb-md">
      <!-- 生成进度 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header flex-between">
              <span><el-icon class="mr-sm"><TrendCharts /></el-icon>生成进度</span>
              <el-radio-group v-model="progressChartType" size="small">
                <el-radio-button value="realtime">实时</el-radio-button>
                <el-radio-button value="history">历史</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <!-- 进度条 -->
          <div class="progress-section mb-lg">
            <div class="progress-header flex-between">
              <span class="progress-title">总体进度</span>
              <span class="progress-text">{{ task.progress }}%</span>
            </div>
            <el-progress
              :percentage="task.progress"
              :status="task.status === 'failed' ? 'exception' : undefined"
              :stroke-width="20"
            />
          </div>

          <!-- 状态统计 -->
          <div class="status-stats">
            <div class="stat-row">
              <div class="stat-item queued">
                <div class="stat-icon"><Clock /></div>
                <div class="stat-info">
                  <div class="stat-count">{{ task.queued_count }}</div>
                  <div class="stat-label">排队中</div>
                </div>
              </div>
              <div class="stat-item generating">
                <div class="stat-icon"><Loading /></div>
                <div class="stat-info">
                  <div class="stat-count">{{ task.generating_count }}</div>
                  <div class="stat-label">生成中</div>
                </div>
              </div>
              <div class="stat-item completed">
                <div class="stat-icon"><CircleCheck /></div>
                <div class="stat-info">
                  <div class="stat-count">{{ task.completed_count }}</div>
                  <div class="stat-label">已完成</div>
                </div>
              </div>
              <div class="stat-item failed">
                <div class="stat-icon"><CircleClose /></div>
                <div class="stat-info">
                  <div class="stat-count">{{ task.failed_count }}</div>
                  <div class="stat-label">失败</div>
                </div>
              </div>
              <div class="stat-item paused">
                <div class="stat-icon"><VideoPause /></div>
                <div class="stat-info">
                  <div class="stat-count">{{ task.paused_count }}</div>
                  <div class="stat-label">已暂停</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 进度图表 -->
          <div class="chart-container mt-lg" v-if="progressChartType === 'history'">
            <div ref="progressChartRef" style="height: 200px;"></div>
          </div>
        </el-card>
      </el-col>

      <!-- 分发进度 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span><el-icon class="mr-sm"><Share /></el-icon>分发进度</span>
          </template>
          <div class="distribution-stats">
            <div class="dist-stat">
              <div class="dist-label">已分发</div>
              <div class="dist-value primary">{{ task.distributed_count }}</div>
            </div>
            <div class="dist-stat">
              <div class="dist-label">待发布</div>
              <div class="dist-value warning">{{ task.pending_publish_count }}</div>
            </div>
            <div class="dist-stat">
              <div class="dist-label">已发布</div>
              <div class="dist-value success">{{ task.published_count }}</div>
            </div>
          </div>
          <el-progress
            :percentage="distributeProgress"
            :stroke-width="12"
            class="mt-md"
          />
        </el-card>

        <!-- 时间统计 -->
        <el-card class="mt-md">
          <template #header>
            <span><el-icon class="mr-sm"><Timer /></el-icon>时间统计</span>
          </template>
          <div class="time-stats">
            <div class="time-item">
              <span class="label">创建时间</span>
              <span class="value">{{ task.created_at }}</span>
            </div>
            <div class="time-item">
              <span class="label">运行时长</span>
              <span class="value highlight">{{ runningDuration }}</span>
            </div>
            <div class="time-item" v-if="task.status === 'completed'">
              <span class="label">平均单条</span>
              <span class="value">{{ avgDurationPerItem }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
```

#### 子任务表格 - 增加批量操作和时间统计

```vue
    <!-- 子任务列表 -->
    <el-card>
      <template #header>
        <div class="toolbar flex-between">
          <div class="toolbar-left flex gap-md">
            <!-- 批量选择 -->
            <el-checkbox v-model="selectAllItems" @change="handleSelectAll">
              全选 ({{ selectedItems.length }})
            </el-checkbox>

            <!-- 批量操作 -->
            <template v-if="selectedItems.length > 0">
              <el-button type="primary" size="small" @click="batchPause" :disabled="!hasUnpausedSelected">
                暂停
              </el-button>
              <el-button type="success" size="small" @click="batchResume" :disabled="!hasPausedSelected">
                继续
              </el-button>
              <el-button type="warning" size="small" @click="batchRetry" :disabled="!hasFailedSelected">
                重试
              </el-button>
            </template>

            <!-- 状态筛选 -->
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px;">
              <el-option label="全部" value="" />
              <el-option label="排队中" value="queued" />
              <el-option label="生成中" value="generating" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="已暂停" value="paused" />
            </el-select>

            <!-- 搜索 -->
            <el-input
              v-model="searchKeyword"
              placeholder="搜索创作者昵称"
              :prefix-icon="Search"
              clearable
              style="width: 200px;"
            />
          </div>

          <div class="toolbar-right">
            <!-- 视图切换 -->
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button value="table">表格</el-radio-button>
              <el-radio-button value="card">卡片</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <el-table
        v-if="viewMode === 'table'"
        :data="items"
        @selection-change="handleItemSelection"
        style="width: 100%"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="sub_user_id" label="用户ID" width="90" />
        <el-table-column prop="sub_user_nickname" label="创作者" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="24">{{ row.sub_user_nickname?.[0] }}</el-avatar>
              <span class="nickname">{{ row.sub_user_nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="template_name" label="模板" width="140" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getItemStatusType(row.status)" size="small">
              <el-icon v-if="row.status === 'generating'" class="is-loading"><Loading /></el-icon>
              {{ getItemStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 时间统计 -->
        <el-table-column label="耗时统计" width="220">
          <template #default="{ row }">
            <div class="time-stats-cell">
              <template v-if="row.status === 'completed'">
                <div class="time-row">
                  <span class="time-label">排队:</span>
                  <span class="time-value">{{ formatDuration(row.queued_at, row.started_at) }}</span>
                </div>
                <div class="time-row">
                  <span class="time-label">生成:</span>
                  <span class="time-value success">{{ formatDuration(row.started_at, row.completed_at) }}</span>
                </div>
              </template>
              <template v-else-if="row.status === 'generating'">
                <div class="time-row">
                  <span class="time-label">已运行:</span>
                  <span class="time-value primary">{{ formatDuration(row.started_at) }}</span>
                </div>
              </template>
              <template v-else-if="row.status === 'queued'">
                <div class="time-row">
                  <span class="time-label">已等待:</span>
                  <span class="time-value warning">{{ formatDuration(row.queued_at) }}</span>
                </div>
              </template>
              <span v-else>-</span>
            </div>
          </template>
        </el-table-column>

        <!-- 模型信息 -->
        <el-table-column label="使用模型" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.model_platform && row.model_id">
              <span>{{ row.model_platform }} / {{ row.model_id }}</span>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">
              {{ row.error_message }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewItem(row)" :disabled="row.status !== 'completed'">
              预览
            </el-button>
            <el-button
              type="warning"
              link
              size="small"
              @click="pauseItem(row)"
              v-if="['queued', 'generating'].includes(row.status)"
            >
              暂停
            </el-button>
            <el-button
              type="success"
              link
              size="small"
              @click="resumeItem(row)"
              v-if="row.status === 'paused'"
            >
              继续
            </el-button>
            <el-button
              type="warning"
              link
              size="small"
              @click="retryItem(row)"
              v-if="row.status === 'failed'"
            >
              重试
            </el-button>
            <el-dropdown>
              <el-button link size="small">更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="distributeItem(row)" v-if="row.status === 'completed'">
                    分发
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="viewLog(row)">
                    查看日志
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination mt-lg flex-between">
        <span class="total-text">共 {{ total }} 条子任务</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>
```

#### WebSocket 实时进度更新

```typescript
// WebSocket 连接和处理
import { onMounted, onUnmounted, ref } from 'vue'

const wsConnected = ref(false)
let ws: WebSocket | null = null

const connectWebSocket = () => {
  const wsUrl = `ws://localhost:8000/ws/generation/${taskId.value}?token=${accessToken}`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    console.log('WebSocket connected')
  }

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    handleWebSocketMessage(message)
  }

  ws.onclose = () => {
    wsConnected.value = false
    console.log('WebSocket disconnected')
    // 自动重连
    setTimeout(connectWebSocket, 5000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

const handleWebSocketMessage = (message: any) => {
  switch (message.type) {
    case 'progress':
      // 更新任务进度
      Object.assign(task, message.data)
      // 记录进度历史
      progressHistory.value.push({
        timestamp: new Date().toISOString(),
        ...message.data
      })
      break
    case 'item_completed':
      // 更新子任务
      const itemIndex = items.value.findIndex(i => i.id === message.data.item_id)
      if (itemIndex !== -1) {
        items.value[itemIndex] = { ...items.value[itemIndex], ...message.data }
      }
      break
    case 'item_failed':
      // 子任务失败
      const failIndex = items.value.findIndex(i => i.id === message.data.item_id)
      if (failIndex !== -1) {
        items.value[failIndex] = { ...items.value[failIndex], ...message.data }
      }
      break
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})
```

---

## 四、内容分发模块

### 4.1 批量分发页面

**路由**: `/distribution/distribute/:taskId`

#### 页面布局

```vue
<template>
  <div class="distribute-view">
    <h2 class="page-title">批量分发内容</h2>

    <el-card class="mb-md">
      <template #header>
        <div class="card-header flex-between">
          <span><el-icon class="mr-sm"><Document /></el-icon>选择要分发的内容</span>
          <div class="selection-info">
            已选择 <strong>{{ selectedItems.length }}</strong> / {{ totalItems }} 条
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar mb-md">
        <el-checkbox v-model="selectAll" @change="handleSelectAll">全选</el-checkbox>
        <el-divider direction="vertical" />
        <el-select v-model="filterTemplate" placeholder="按模板筛选" clearable style="width: 180px;">
          <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="filterSubuser" placeholder="按创作者筛选" clearable style="width: 180px;">
          <el-option v-for="u in subusers" :key="u.id" :label="u.nickname" :value="u.id" />
        </el-select>
        <el-button type="primary" @click="applyFilter">筛选</el-button>
      </div>

      <!-- 内容列表 -->
      <el-table :data="items" @selection-change="handleSelection" style="width: 100%;">
        <el-table-column type="selection" width="50" />
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <div class="preview-thumb">
              <el-image
                v-if="row.generated_image_urls_json?.length"
                :src="row.generated_image_urls_json[0]"
                fit="cover"
                class="thumb-img"
                :preview-src-list="row.generated_image_urls_json"
              />
              <div v-else class="text-thumb">
                <el-icon><Document /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="generated_title" label="标题" width="200" show-overflow-tooltip />
        <el-table-column label="创作者" width="120">
          <template #default="{ row }">
            {{ row.sub_user_nickname }}
          </template>
        </el-table-column>
        <el-table-column label="模板" width="120">
          <template #default="{ row }">
            {{ row.template_name }}
          </template>
        </el-table-column>
        <el-table-column label="分发状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getDistStatusType(row.distribution_status)" size="small">
              {{ getDistStatusLabel(row.distribution_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="170" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="previewContent(row)">
              预览
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination mt-md flex-between">
        <span></span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalItems"
        />
      </div>
    </el-card>

    <!-- 选择目标用户（可选，默认使用原任务用户） -->
    <el-card class="mb-md">
      <template #header>
        <div class="card-header">
          <el-icon class="mr-sm"><User /></el-icon>
          <span>目标用户（可选，不选则分发给原任务用户）</span>
        </div>
      </template>

      <el-checkbox v-model="overrideTargetUsers">重新指定目标用户</el-checkbox>

      <div v-if="overrideTargetUsers" class="target-users mt-md">
        <el-tree
          ref="userTreeRef"
          :data="userTreeData"
          show-checkbox
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
        />
      </div>
    </el-card>

    <!-- 底部操作栏 -->
    <div class="bottom-actions">
      <div class="selection-summary">
        即将分发 <strong>{{ selectedItems.length }}</strong> 条内容
        <template v-if="overrideTargetUsers">
          给 <strong>{{ selectedTargetUsers.length }}</strong> 个创作者
        </template>
      </div>
      <div>
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" @click="submitDistribute" :loading="submitting">
          确认分发
        </el-button>
      </div>
    </div>
  </div>
</template>
```

---

## 五、创意种子库模块

### 5.1 创意种子库管理页面

**路由**: `/settings/creative-seeds`

**功能模块**:
- 种子列表展示（表格视图）
- 类型筛选（全部/开头模式/情感基调/结尾模式）
- 品类筛选
- 状态筛选
- 关键词搜索
- 创建/编辑种子
- 启用/禁用种子
- 删除自定义种子

#### 页面布局

```vue
<template>
  <div class="creative-seed-view">
    <h2 class="page-title">创意种子库管理</h2>

    <div class="card">
      <!-- 类型筛选 Tab -->
      <el-tabs v-model="activeType" @tab-change="loadSeeds" class="mb-md">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="开头模式" name="opening" />
        <el-tab-pane label="情感基调" name="emotion" />
        <el-tab-pane label="结尾模式" name="ending" />
      </el-tabs>

      <!-- 工具栏 -->
      <div class="toolbar flex-between mb-md">
        <div class="toolbar-left">
          <el-select v-model="filterCategory" placeholder="品类筛选" clearable>
            <el-option label="全部" value="" />
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable>
            <el-option label="全部" value="" />
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
          <el-input v-model="searchKeyword" placeholder="搜索种子名称/模板" clearable>
            <template #append>
              <el-button :icon="Search" @click="loadSeeds" />
            </template>
          </el-input>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新建种子
        </el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="seeds" v-loading="loading" stripe>
        <el-table-column prop="name" label="种子名称" min-width="150" />
        <el-table-column prop="seed_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.seed_type)" size="small">
              {{ getTypeLabel(row.seed_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="template" label="模板示例" min-width="250">
          <template #default="{ row }">
            <div class="template-cell" v-html="formatTemplateHtml(row.template)" />
          </template>
        </el-table-column>
        <el-table-column prop="category" label="适用品类" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.category || '通用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'danger'" size="small">
              {{ row.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button
              v-if="row.is_system"
              size="small"
              :type="row.status === 'enabled' ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'enabled' ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="!row.is_system"
              size="small"
              type="danger"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadSeeds"
        @current-change="loadSeeds"
      />
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑种子' : '新建种子'" width="600px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="种子名称" prop="name">
          <el-input v-model="formData.name" placeholder="如：反常识开头" />
        </el-form-item>
        <el-form-item label="种子类型" prop="seed_type">
          <el-select v-model="formData.seed_type" placeholder="选择类型" :disabled="isEdit">
            <el-option label="开头模式" value="opening" />
            <el-option label="情感基调" value="emotion" />
            <el-option label="结尾模式" value="ending" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板示例" prop="template">
          <el-input
            v-model="formData.template"
            type="textarea"
            :rows="4"
            placeholder="JSON数组格式，如：[\"没想到这个xxx居然...\", \"谁能想到xxx竟然...\"]"
          />
        </el-form-item>
        <el-form-item label="使用说明" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="适用品类" prop="category">
          <el-select v-model="formData.category" placeholder="选择品类">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="禁止模式" prop="forbidden_patterns">
          <el-input
            v-model="forbiddenPatternsText"
            type="textarea"
            :rows="2"
            placeholder="每行一个禁止模式"
          />
        </el-form-item>
        <el-form-item label="典型表达" prop="example_phrases">
          <el-input
            v-model="examplePhrasesText"
            type="textarea"
            :rows="2"
            placeholder="每行一个典型表达"
          />
        </el-form-item>
        <el-form-item label="避免表达" prop="avoid_phrases">
          <el-input
            v-model="avoidPhrasesText"
            type="textarea"
            :rows="2"
            placeholder="每行一个避免表达"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

#### 种子类型说明

| 类型 | 标签颜色 | 说明 |
|------|---------|------|
| opening（开头模式） | primary | 控制文案开头的风格，如反常识、自嘲、悬念 |
| emotion（情感基调） | success | 控制文案的情感表达，如轻松吐槽、真诚分享 |
| ending（结尾模式） | warning | 控制文案的收尾方式，如求建议、留悬念 |

---

## 六、系统设置模块

### 5.1 系统设置页面

**路由**: `/settings`

**功能模块**:
- 个人设置（所有角色）
- 模型平台配置（超级管理员和创作管理员）
- 过期清理策略（仅超级管理员）

#### 实际实现布局

```vue
<template>
  <div class="settings-view">
    <h2 class="page-title">系统设置</h2>

    <el-row :gutter="20">
      <el-col :span="6">
        <div class="card">
          <el-menu
            :default-active="activeMenu"
            class="settings-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="profile">
              <el-icon><User /></el-icon>
              <span>个人设置</span>
            </el-menu-item>
            <!-- 仅超级管理员和创作管理员可见模型平台配置 -->
            <el-menu-item v-if="!isSubUser" index="model">
              <el-icon><Setting /></el-icon>
              <span>模型平台配置</span>
            </el-menu-item>
            <!-- 仅超级管理员可见过期清理策略 -->
            <el-menu-item v-if="isSuperAdmin" index="cleanup">
              <el-icon><Delete /></el-icon>
              <span>过期清理策略</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>

      <el-col :span="18">
        <div class="card">
          <!-- 个人设置 -->
          <div v-if="activeMenu === 'profile'" class="settings-panel">
            <h3 class="section-title">个人设置</h3>

            <el-divider content-position="left">个人信息</el-divider>
            <el-form label-width="120px" style="max-width: 450px;">
              <el-form-item label="当前用户名">
                <el-input v-model="profileForm.username" disabled />
              </el-form-item>
              <el-form-item label="自定义昵称">
                <el-input v-model="profileForm.nickname" placeholder="请输入自定义昵称" clearable />
              </el-form-item>
            </el-form>
            <div class="settings-actions">
              <el-button type="primary" @click="saveProfile">保存昵称</el-button>
            </div>

            <el-divider content-position="left" class="mt-lg">修改密码</el-divider>
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="120px"
              style="max-width: 450px;"
            >
              <el-form-item label="原密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  placeholder="请输入原密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  show-password
                />
              </el-form-item>
            </el-form>
            <div class="settings-actions">
              <el-button type="primary" @click="savePassword">修改密码</el-button>
            </div>
          </div>

          <!-- 模型平台配置 -->
          <div v-if="activeMenu === 'model'" class="settings-panel">
            <h3 class="section-title">模型平台配置</h3>

            <el-divider content-position="left">默认模型设置</el-divider>
            <el-form label-width="160px" style="max-width: 480px;">
              <el-form-item label="默认文本模型">
                <el-select v-model="defaultModels.text" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllTextModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="默认图片模型">
                <el-select v-model="defaultModels.image" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllImageModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="默认Embedding模型">
                <el-select v-model="defaultModels.embedding" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllEmbeddingModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
            </el-form>

            <!-- 仅超级管理员可见模型平台详细配置 -->
            <el-tabs v-if="isSuperAdmin" v-model="activePlatform" class="platform-tabs">
              <el-tab-pane
                v-for="platform in platforms"
                :key="platform.id"
                :label="platform.name"
                :name="platform.id"
              >
                <div class="platform-content">
                  <el-collapse v-model="activeCollapse" class="model-collapse">
                    <!-- 文本模型 -->
                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'llm')" name="text">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="primary" size="small">文本模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'llm').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'llm')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'llm')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <!-- 图片模型 -->
                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'image')" name="image">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="success" size="small">图片模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'image').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'image')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'image')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <!-- 视频模型 -->
                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'video')" name="video">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="warning" size="small">视频模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'video').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'video')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'video')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <!-- Embedding模型 -->
                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'embedding')" name="embedding">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="info" size="small">Embedding模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'embedding').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'embedding')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'embedding')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 过期清理策略 -->
          <div v-if="activeMenu === 'cleanup'" class="settings-panel">
            <h3 class="section-title">过期清理策略</h3>
            <!-- 清理策略配置内容 -->
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

    <!-- 模型列表 -->
    <el-card>
      <template #header>
        <div class="card-header flex-between">
          <div class="header-left">
            <el-select v-model="filterPlatform" placeholder="选择平台" style="width: 150px;">
              <el-option
                v-for="p in platforms"
                :key="p.platform"
                :label="p.platform_name"
                :value="p.platform"
              />
            </el-select>
            <el-select v-model="filterModelType" placeholder="模型类型" style="width: 120px; margin-left: 12px;">
              <el-option label="全部" value="" />
              <el-option label="语言模型" value="llm" />
              <el-option label="图片模型" value="image" />
              <el-option label="视频模型" value="video" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" style="width: 100px; margin-left: 12px;">
              <el-option label="全部" value="" />
              <el-option label="启用" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </div>
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">
            添加模型配置
          </el-button>
        </div>
      </template>

      <el-table :data="models" style="width: 100%;">
        <el-table-column prop="platform_name" label="平台" width="100">
          <template #default="{ row }">
            <el-tag :color="getPlatformColor(row.platform)" size="small">
              {{ row.platform_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" width="180" />
        <el-table-column prop="model_id" label="模型ID" width="180" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.model_type === 'llm'" type="info" size="small">语言</el-tag>
            <el-tag v-else-if="row.model_type === 'image'" type="success" size="small">图片</el-tag>
            <el-tag v-else-if="row.model_type === 'video'" type="warning" size="small">视频</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Base URL" width="200" show-overflow-tooltip v-if="filterModelType === 'llm' || !filterModelType">
          <template #default="{ row }">
            <span v-if="row.base_url">{{ row.base_url }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_concurrency" label="最大并发" width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.max_concurrency"
              :min="1"
              :max="100"
              size="small"
              @change="updateModelConcurrency(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tooltip v-if="row.is_default" content="默认模型">
              <el-icon class="is-warning" color="#E6A23C"><StarFilled /></el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="'active'"
              :inactive-value="'inactive'"
              @change="toggleModelStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="setDefault(row)" v-if="!row.is_default">
              设为默认
            </el-button>
            <el-button type="primary" link size="small" @click="editModel(row)">
              编辑
            </el-button>
            <el-popconfirm
              title="确定要删除这个模型配置吗？"
              @confirm="deleteModel(row)"
              v-if="!row.is_system"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="editingModel ? '编辑模型配置' : '添加模型配置'"
      width="600px"
    >
      <el-form :model="modelForm" label-width="120px">
        <el-form-item label="平台">
          <el-select v-model="modelForm.platform" placeholder="选择平台" style="width: 100%;">
            <el-option
              v-for="p in availablePlatforms"
              :key="p.platform"
              :label="p.platform_name"
              :value="p.platform"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型类型">
          <el-radio-group v-model="modelForm.model_type">
            <el-radio label="llm">语言模型</el-radio>
            <el-radio label="image">图片模型</el-radio>
            <el-radio label="video">视频模型</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.model_name" placeholder="例如: GPT-4" />
        </el-form-item>
        <el-form-item label="模型ID">
          <el-input v-model="modelForm.model_id" placeholder="例如: gpt-4" />
        </el-form-item>
        <el-form-item label="Base URL" v-if="modelForm.model_type === 'llm'">
          <el-input v-model="modelForm.base_url" placeholder="https://api.example.com/v1" />
        </el-form-item>
        <el-form-item label="API端点">
          <el-input v-model="modelForm.api_endpoint" placeholder="API端点路径" />
        </el-form-item>
        <el-form-item label="最大并发">
          <el-input-number v-model="modelForm.max_concurrency" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="API配置">
          <el-input
            v-model="modelForm.config_json_text"
            type="textarea"
            :rows="4"
            placeholder='{"api_key": "your-api-key"}'
          />
          <div class="form-tip">JSON格式，包含API Key等配置信息</div>
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="modelForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, StarFilled } from '@element-plus/icons-vue'
import apiClient from '@/api/client'

#### 平台列表

实际支持的平台（8个）:
- **阿里百炼 (bailian)** - 文本、图片、Embedding模型
- **火山引擎 (volcano)** - 文本、图片、视频模型
- **即梦 (jimeng)** - 图片、视频模型
- **可灵 (kling)** - 图片、视频模型
- **AutoGLM (autoglm)** - 文本模型
- **月之暗面 (moonshot)** - 文本模型
- **DeepSeek (deepseek)** - 文本、Embedding模型
- **灵牙AI (lingyaai)** - 文本、Embedding模型

#### 认证方式

不同平台采用不同的认证方式:

**标准 API Key 认证**（6个平台）:
- 阿里百炼: `api_key`
- 火山引擎: `api_key`
- AutoGLM: `api_key`
- 月之暗面: `api_key`
- DeepSeek: `api_key`
- 灵牙AI: `api_key`

**AccessKey + SecretKey 认证**（2个平台）:
- **即梦 (jimeng)**: 使用 `access_key` + `secret_key` 进行 HMAC-SHA256 签名
- **可灵 (kling)**: 使用 `access_key` + `secret_key` 动态生成 JWT Token

// 模型列表
const models = ref([
  {
    id: 1,
    platform: 'bailian',
    platform_name: '阿里云百炼',
    model_id: 'qwen-max',
    model_name: '千问-Max',
    model_type: 'llm',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_endpoint: '/chat/completions',
    max_concurrency: 5,
    is_default: true,
    is_system: true,
    status: 'active'
  },
  {
    id: 2,
    platform: 'bailian',
    platform_name: '阿里云百炼',
    model_id: 'wanx-v2',
    model_name: '万相-V2',
    model_type: 'image',
    api_endpoint: '/services/aigc/text2image/image-synthesis',
    max_concurrency: 10,
    is_default: true,
    is_system: true,
    status: 'active'
  },
  {
    id: 3,
    platform: 'jimeng',
    platform_name: '即梦',
    model_id: 'jimeng-v4',
    model_name: '即梦4.0',
    model_type: 'image',
    api_endpoint: '/api/v1/image/generation',
    max_concurrency: 2,
    is_default: false,
    is_system: true,
    status: 'active'
  },
  {
    id: 4,
    platform: 'kling',
    platform_name: '可灵',
    model_id: 'kling-v1',
    model_name: '可灵视频',
    model_type: 'video',
    api_endpoint: '/api/v1/video/generation',
    max_concurrency: 5,
    is_default: true,
    is_system: true,
    status: 'active'
  }
])

// 筛选
const filterPlatform = ref('')
const filterModelType = ref('')
const filterStatus = ref('')

// 对话框
const showDialog = ref(false)
const editingModel = ref<any>(null)
const saving = ref(false)
const modelForm = reactive({
  platform: '',
  model_type: 'llm',
  model_name: '',
  model_id: '',
  base_url: '',
  api_endpoint: '',
  max_concurrency: 5,
  config_json_text: '',
  is_default: false
})

// 可用平台（API文档中定义的）
const availablePlatforms = computed(() => [
  { platform: 'bailian', platform_name: '阿里云百炼' },
  { platform: 'yuanbao', platform_name: '元宝' },
  { platform: 'moonshot', platform_name: '月之暗面' },
  { platform: 'zhipu', platform_name: '智谱AI' },
  { platform: 'doubao', platform_name: '豆包' },
  { platform: 'jimeng', platform_name: '即梦' },
  { platform: 'kling', platform_name: '可灵' }
])

const getPlatformColor = (platform: string) => {
  const colors: Record<string, string> = {
    bailian: '#FF6A00',
    yuanbao: '#165DFF',
    moonshot: '#000000',
    zhipu: '#1377EB',
    doubao: '#FE2C55',
    jimeng: '#7C4DFF',
    kling: '#00C853'
  }
  return colors[platform] || ''
}

const togglePlatform = (platform: any) => {
  ElMessage.success(`${platform.platform_name} 已${platform.active ? '启用' : '禁用'}`)
}

const viewPlatformDocs = (platform: any) => {
  // 打开API文档链接
  const docUrls: Record<string, string> = {
    bailian: 'https://bailian.console.aliyun.com/',
    yuanbao: 'https://www.yuanbao.com/',
    moonshot: 'https://platform.moonshot.cn/',
    zhipu: 'https://open.bigmodel.cn/',
    doubao: 'https://www.volcengine.com/docs/82379',
    jimeng: 'https://www.volcengine.com/docs/85621',
    kling: 'https://klingai.com/document-api'
  }
  if (docUrls[platform.platform]) {
    window.open(docUrls[platform.platform], '_blank')
  }
}

const openCreateDialog = () => {
  editingModel.value = null
  Object.assign(modelForm, {
    platform: '',
    model_type: 'llm',
    model_name: '',
    model_id: '',
    base_url: '',
    api_endpoint: '',
    max_concurrency: 5,
    config_json_text: '',
    is_default: false
  })
  showDialog.value = true
}

const editModel = (model: any) => {
  editingModel.value = model
  Object.assign(modelForm, {
    platform: model.platform,
    model_type: model.model_type,
    model_name: model.model_name,
    model_id: model.model_id,
    base_url: model.base_url || '',
    api_endpoint: model.api_endpoint,
    max_concurrency: model.max_concurrency,
    config_json_text: JSON.stringify(model.config_json || {}, null, 2),
    is_default: model.is_default
  })
  showDialog.value = true
}

const saveModel = async () => {
  saving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('保存成功')
    showDialog.value = false
  } finally {
    saving.value = false
  }
}

const setDefault = (model: any) => {
  ElMessageBox.confirm(`确定将 ${model.model_name} 设为默认模型吗？`, '提示')
    .then(() => {
      // 更新默认模型
      models.value.forEach(m => {
        if (m.model_type === model.model_type) {
          m.is_default = m.id === model.id
        }
      })
      ElMessage.success('已设为默认')
    })
    .catch(() => {})
}

const toggleModelStatus = (model: any) => {
  ElMessage.success(`${model.model_name} 已${model.status === 'active' ? '启用' : '禁用'}`)
}

const updateModelConcurrency = (model: any) => {
  // 并发数更新
}

const deleteModel = (model: any) => {
  const index = models.value.findIndex(m => m.id === model.id)
  if (index !== -1) {
    models.value.splice(index, 1)
    ElMessage.success('删除成功')
  }
}
</script>

<style lang="scss" scoped>
.model-config-view {
  .platform-card {
    transition: all 0.3s;
    &.disabled {
      opacity: 0.6;
    }
    .platform-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      .platform-name {
        font-weight: 600;
        font-size: 16px;
      }
    }
    .platform-stats {
      .stat {
        display: flex;
        justify-content: space-between;
        margin: 4px 0;
        .label {
          color: #909399;
        }
        .value {
          font-weight: 500;
        }
      }
    }
    .platform-actions {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #ebeef5;
    }
  }
}

.mb-md {
  margin-bottom: 16px;
}

.text-gray {
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
```

---

## 六、仪表盘页面

### 6.1 仪表盘页面

**路由**: `/dashboard`

**核心功能**:
- Tab切换：总览、趋势分析
- 角色差异化显示：创作者与管理员看到不同内容
- 统计卡片筛选：日期范围、管理员筛选（仅超级管理员）
- 最近内容/任务列表：根据角色显示不同数据

#### 实际实现布局

```vue
<template>
  <div class="dashboard-view">
    <h2 class="page-title">AIGC看板</h2>

    <!-- Tab切换 -->
    <div class="tab-container">
      <el-radio-group v-model="activeTab" size="default">
        <el-radio-button value="overview">总览</el-radio-button>
        <el-radio-button value="trend">趋势分析</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 总览Tab -->
    <div v-show="activeTab === 'overview'">
      <!-- 统计卡片筛选控件 - 仅对管理员显示 -->
      <el-row v-if="!isSubUser" :gutter="12" class="mb-md" align="middle">
        <el-col :span="1.5">
          <span class="filter-label">统计范围</span>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="statsDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="handleStatsFilterChange"
          />
        </el-col>
        <el-col v-if="isSuperAdmin" :span="1.5">
          <span class="filter-label">管理员</span>
        </el-col>
        <el-col v-if="isSuperAdmin" :span="4">
          <el-select
            v-model="statsOperatorId"
            placeholder="全部管理员"
            clearable
            size="small"
            style="width: 100%"
            @change="handleStatsFilterChange"
          >
            <el-option
              v-for="op in operatorList"
              :key="op.id"
              :label="op.name"
              :value="op.id"
            />
          </el-select>
        </el-col>
      </el-row>

      <!-- 统计卡片 -->
      <el-row :gutter="20">
        <!-- 创作者只显示待发布和已发布 -->
        <el-col v-if="!isSubUser" :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <el-icon :size="32" color="#fff"><User /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.total_sub_users || 0 }}</div>
              <div class="stat-label">总创作者数</div>
            </div>
          </div>
        </el-col>
        <el-col v-if="!isSubUser" :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <el-icon :size="32" color="#fff"><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.today_generated || 0 }}</div>
              <div class="stat-label">生成内容（周期内）</div>
            </div>
          </div>
        </el-col>
        <el-col :span="isSubUser ? 12 : 6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <el-icon :size="32" color="#fff"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.pending_publish || 0 }}</div>
              <div class="stat-label">今日待发内容</div>
            </div>
          </div>
        </el-col>
        <el-col :span="isSubUser ? 12 : 6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
              <el-icon :size="32" color="#fff"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.published || 0 }}</div>
              <div class="stat-label">今日已发内容</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 最近内容/任务列表 -->
    <el-row :gutter="20" class="mt-lg">
      <el-col :span="24">
        <div class="card">
          <div class="card-header flex-between">
            <h3 class="section-title" style="margin-bottom: 0;">{{ isSubUser ? '最近内容' : '最近任务' }}</h3>
            <div class="flex-center gap-sm">
              <!-- 超级管理员：创作管理员筛选 -->
              <el-select
                v-if="isSuperAdmin"
                v-model="selectedOperatorId"
                placeholder="选择管理员"
                clearable
                size="small"
                style="width: 150px"
                @change="handleOperatorChange"
              >
                <el-option
                  v-for="op in operatorList"
                  :key="op.id"
                  :label="op.name"
                  :value="op.id"
                />
              </el-select>
              <!-- 日期范围筛选 -->
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
              />
            </div>
          </div>
          
          <!-- 创作者：显示内容卡片列表 -->
          <div v-if="isSubUser" class="content-list">
            <el-empty v-if="recentItems.length === 0" description="暂无内容" />
            <el-card v-for="item in recentItems" :key="item.id" class="content-card mb-md" shadow="hover">
              <div class="item-header flex-between">
                <div class="item-title">
                  <span class="task-name">{{ item.taskName || '任务 #' + item.task_id }}</span>
                  <el-tag :type="item.status === 'published' ? 'success' : 'warning'" size="small" style="margin-left: 12px;">
                    {{ item.status === 'published' ? '已发布' : '待发布' }}
                  </el-tag>
                </div>
                <div class="item-time">{{ formatDate(item.created_at) }}</div>
              </div>
              <div class="item-content mt-md">
                <!-- 标题 -->
                <div v-if="item.generated_title" class="content-row">
                  <span class="row-label">📌 标题</span>
                  <span class="row-value">{{ item.generated_title }}</span>
                </div>
                <!-- 正文 -->
                <div v-if="item.generated_text" class="content-row">
                  <span class="row-label">📄 正文</span>
                  <span class="row-value">{{ item.generated_text.substring(0, 100) }}...</span>
                </div>
                <!-- 图片预览 -->
                <div v-if="item.generated_image_urls_json?.length" class="content-row">
                  <span class="row-label">🖼️ 图片</span>
                  <div class="image-thumbs">
                    <el-image
                      v-for="(img, idx) in item.generated_image_urls_json.slice(0, 4)"
                      :key="idx"
                      :src="img"
                      class="image-thumb"
                      fit="cover"
                      :preview-src-list="item.generated_image_urls_json"
                    />
                  </div>
                </div>
              </div>
              <div class="item-footer flex-between mt-sm">
                <span class="meta-item">内容 #{{ item.id }}</span>
                <el-button type="primary" link size="small" @click="viewItemDetail(item)">查看详情</el-button>
              </div>
            </el-card>
          </div>
          
          <!-- 管理员：显示任务列表 -->
          <div v-else class="task-list">
            <el-empty v-if="recentTasks.length === 0" description="暂无任务" />
            <el-card v-for="task in recentTasks" :key="task.id" class="task-card mb-md" shadow="hover">
              <div class="task-header flex-between">
                <div class="task-title">
                  <span class="task-id">#{{ task.id }}</span>
                  <span class="task-name">{{ task.name || '任务' }}</span>
                  <el-tag :type="getStatusType(task.status)" size="small" style="margin-left: 12px;">
                    {{ getStatusLabel(task.status) }}
                  </el-tag>
                </div>
                <div class="task-time">{{ formatDate(task.created_at) }}</div>
              </div>
              <div class="task-progress mt-md">
                <el-progress
                  :percentage="task.progress || 0"
                  :stroke-width="8"
                />
                <div class="progress-stats">
                  <span>已完成: {{ task.completed_count || 0 }} / {{ task.total_count || 0 }}</span>
                </div>
              </div>
              <div class="task-footer flex-between mt-sm">
                <div class="task-meta">
                  <span>子任务: {{ task.total_count || 0 }}</span>
                  <span class="dot">·</span>
                  <span>模板: {{ task.template_name || '-' }}</span>
                </div>
                <el-button type="primary" link size="small" @click="goToTaskDetail(task.id)">查看详情</el-button>
              </div>
            </el-card>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势分析Tab -->
    <div v-show="activeTab === 'trend'">
      <TrendAnalysisPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, Loading, AlarmClock, CircleCheck, Top, Plus, Document, Picture, Share, Bell, CircleClose
} from '@element-plus/icons-vue'

const router = useRouter()

const stats = ref({
  subuser_count: 156,
  today_generating: 3,
  today_generated: 234,
  pending_publish: 89,
  published: 3421,
  today_published: 67
})

const runningTasks = ref([
  {
    id: 1,
    name: '美妆产品种草笔记批量生成',
    total_count: 50,
    completed_count: 32,
    progress: 64,
    created_at: '2024-03-26 14:30'
  },
  {
    id: 2,
    name: '母婴好物分享内容生成',
    total_count: 80,
    completed_count: 15,
    progress: 19,
    created_at: '2024-03-26 15:00'
  }
])

const trendPeriod = ref('7')

const goToCreateTask = () => router.push('/generation/create')
const goToTemplates = () => router.push('/templates')
const goToMaterials = () => router.push('/materials')
const goToSubusers = () => router.push('/users/sub-users')
const goToGenerationList = () => router.push('/generation')
const goToTaskDetail = (id: number) => router.push(`/generation/detail/${id}`)
const goToPending = () => router.push('/distribution?status=pending_publish')
</script>

<style lang="scss" scoped">
.dashboard-view {
  .stat-card {
    display: flex;
    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      .el-icon {
        font-size: 28px;
        color: white;
      }
      &.subuser { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
      &.generating { background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%); }
      &.pending { background: linear-gradient(135deg, #E6A23C 0%, #f3d19e 100%); }
      &.published { background: linear-gradient(135deg, #67C23A 0%, #95d475 100%); }
    }
    .stat-content {
      flex: 1;
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
        line-height: 1.2;
        margin-bottom: 4px;
        &.warning { color: #E6A23C; }
        &.success { color: #67C23A; }
      }
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 4px;
      }
      .stat-trend {
        font-size: 12px;
        color: #909399;
        display: flex;
        align-items: center;
        gap: 4px;
        &.up { color: #67C23A; }
      }
      .stat-action {
        padding: 0;
      }
    }
  }

  .quick-actions {
    .action-btn {
      width: 100%;
      justify-content: flex-start;
      margin-bottom: 8px;
      .action-icon {
        margin-right: 8px;
      }
    }
  }

  .running-tasks {
    .task-item {
      display: flex;
      align-items: center;
      padding: 12px;
      border: 1px solid #ebeef5;
      border-radius: 8px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s;
      &:hover {
        border-color: #409EFF;
        background: #f5f7fa;
      }
      .task-info {
        flex: 1;
        .task-name {
          font-weight: 500;
          margin-bottom: 4px;
        }
        .task-meta {
          font-size: 12px;
          color: #909399;
          .dot { margin: 0 8px; }
        }
      }
      .task-progress {
        display: flex;
        align-items: center;
        gap: 12px;
        .progress-stats {
          font-size: 14px;
          .completed { color: #67C23A; font-weight: 500; }
        }
      }
    }
  }
}

.mb-md {
  margin-bottom: 20px;
}
</style>
```

---

## 七、总结

本文档基于实际代码实现,完整记录了 妙笔内容工场的 Web UI 设计:

### 1. **角色差异化设计**
- **超级管理员**: 创作创作管理员、资源转移、模型平台配置、过期清理策略
- **创作管理员**: 批量生成、分发管理、模型平台配置查看
- **创作者**: 内容查看、确认发布、个人设置

### 2. **Dashboard 页面**
- Tab 切换: 总览、趋势分析
- 统计卡片: 根据角色显示不同指标
- 筛选控件: 日期范围、管理员筛选(仅超级管理员)
- 最近内容/任务: 创作者看内容卡片,管理员看任务列表

### 3. **Settings 页面**
- 左侧菜单: 个人设置、模型平台配置、过期清理策略
- 模型平台配置:
  - 默认模型设置(文本、图片、Embedding)
  - 8个平台Tab切换
  - 模型类型折叠面板(llm、image、video、embedding)
  - 表格展示模型列表

### 4. **Generation 列表页面**
- 创作者视图: 内容卡片列表,显示标题、正文、话题、图片预览
- 管理员视图: 任务卡片列表,显示进度、状态、筛选功能

### 5. **模型平台配置**
- 8个平台: 阿里百炼、火山引擎、即梦、可灵、AutoGLM、月之暗面、DeepSeek、灵牙AI
- 认证方式:
  - 标准 API Key (6个平台)
  - AccessKey + SecretKey (即梦、可灵)

### 6. **图片/视频配置系统**
- 模板编辑页新增图片/视频配置Tab
- 快速预设（小红书、抖音、公众号等）
- 尺寸比例可视化选择
- 质量、分辨率、帧率细调

### 7. **并发控制与任务监控**
- 创建任务时的并发数设置（滑块+提示）
- 任务详情页的实时WebSocket进度
- 子任务暂停/继续批量操作
- 时间统计展示（排队时间、生成耗时）

所有设计均基于实际代码实现,确保与后端接口完全对应。
