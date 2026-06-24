# 妙笔内容工场 - API 设计文档

## 概述

本文档定义了妙笔内容工场的所有前后端接口，采用RESTful API设计规范。

### 技术栈

- **后端框架**：FastAPI (Python 3.11+)
- **认证方式**：JWT (python-jose)
- **实时通信**：WebSocket (fastapi-websockets)
- **前端框架**：Vue 3 + TypeScript + Vite

### API 基础信息

- **Base URL**：`http://localhost:8000/api/v1`
- **认证方式**：Bearer Token
- **请求格式**：JSON
- **响应格式**：JSON

### 通用响应格式

```typescript
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": any,
  "timestamp": 1711680000000
}

// 失败响应
{
  "code": 40001,
  "message": "错误描述",
  "data": null,
  "timestamp": 1711680000000
}
```

---

## 一、认证模块

### 1.1 账号密码登录

**接口**：`POST /login`

**请求体**：
```typescript
{
  username: string,       // 用户名
  password: string        // 密码
}
```

**响应**：
```typescript
{
  access_token: string,    // JWT访问令牌
  refresh_token: string,   // JWT刷新令牌
  token_type: "bearer",
  user: {
    id: number,
    userid: string,
    nickname: string,        // 管理员备注名（仅管理员可见）
    display_name: string,    // 用户自定义昵称（用户自己可见）
    role: "super_admin" | "operator" | "sub_user",
    avatar?: string
  }
}
```

**说明**：
- 连续5次登录失败会锁定账号15分钟
- 返回两个token：`access_token`（短期有效，用于API访问）和 `refresh_token`（长期有效，用于刷新access_token）

---

### 1.2 刷新Token

**接口**：`POST /refresh`

**请求头**：
```
Authorization: Bearer <refresh_token>
```

**说明**：使用 `refresh_token` 刷新 `access_token`

**响应**：
```typescript
{
  access_token: string,    // 新的访问令牌
  refresh_token: string,   // 新的刷新令牌
  token_type: "bearer"
}
```

### 1.6 登出

**接口**：`POST /logout`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：
```typescript
{
  message: "Successfully logged out"
}
```

### 1.7 修改密码

**接口**：`POST /change-password`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```typescript
{
  old_password: string,     // 原密码
  new_password: string      // 新密码
}
```

**响应**：
```typescript
{
  message: "Password changed successfully"
}
```

### 1.8 更新显示名称

**接口**：`POST /update-display-name`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```typescript
{
  display_name: string      // 新的显示名称
}
```

**响应**：
```typescript
{
  message: "Display name updated successfully"
}
```

### 1.9 获取当前用户信息

**接口**：`GET /me`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：
```typescript
{
  id: number,
  userid: string,
  nickname?: string,          // 管理员备注名（仅管理员可见）
  display_name: string,       // 用户自定义昵称
  role: "super_admin" | "operator" | "sub_user",
  avatar?: string,
  
  user_positioning?: string,
  user_category?: string,
  content_style?: string,     // 创作者专属：文案风格
  account_type?: string,      // 创作者专属：账号类型
  created_at: string,
  last_login_at?: string
}
```

---

## 二、用户管理模块

### 权限说明

**三级角色体系**：
- **超级管理员 (super_admin)**：可管理所有用户（包括创作管理员和创作者）
- **创作管理员 (operator)**：可管理自己的创作者
- **创作者 (sub_user)**：仅可查看自己的信息

---

### 2.1 超级创作管理员

#### 2.1.1 获取超级管理员列表

**接口**：`GET /super-admins`

**权限**：仅超级管理员

**请求参数**（Query）：
```typescript
{
  page?: number,        // 页码，默认1
  page_size?: number,    // 每页数量，默认20
  keyword?: string,      // 搜索关键词
  tag_id?: number       // 标签过滤
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    userid: string,
    nickname: string,
    role: "super_admin",
    status: "online" | "offline" | "disabled",
    created_at: string,
    tags: Array<{
      id: number,
      name: string,
      color: string
    }>
  }>
}
```

#### 2.1.2 创建超级管理员

**接口**：`POST /super-admins`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  userid?: string,           // 用户ID（自动生成，可选）
  nickname: string,         // 昵称
  password: string,         // 密码
  tag_ids?: number[]        // 标签ID列表
}
```

#### 2.1.3 获取超级管理员详情

**接口**：`GET /super-admins/{id}`

**权限**：仅超级管理员

#### 2.1.4 更新超级管理员

**接口**：`PUT /super-admins/{id}`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  nickname?: string,         // 昵称
  password?: string,         // 密码（不传则不修改）
  status?: "online" | "offline" | "disabled",  // 状态
  tag_ids?: number[]         // 标签ID列表（覆盖原标签）
}
```

#### 2.1.5 删除超级管理员

**接口**：`DELETE /super-admins/{id}`

**权限**：仅超级管理员

---

### 2.2 创作创作管理员

#### 2.2.1 获取创作管理员列表

**接口**：`GET /operators`

**权限**：超级管理员可查看所有，创作管理员仅可查看自己

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  keyword?: string,
  tag_id?: number
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    userid: string,
    nickname: string,
    role: "operator",
    status: "online" | "offline" | "disabled",
    user_positioning?: string,
    created_at: string,
    tags: Array<{
      id: number,
      name: string,
      color: string
    }>
  }>
}
```

#### 2.2.2 创建创作管理员

**接口**：`POST /operators`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  userid?: string,           // 用户ID（自动生成，可选）
  nickname: string,         // 昵称
  password: string,         // 密码
  user_positioning?: string,  // 运营定位
  tag_ids?: number[]        // 标签ID列表
}
```

#### 2.2.3 获取创作管理员详情

**接口**：`GET /operators/{id}`

**权限**：超级管理员可查看所有，创作管理员仅可查看自己

#### 2.2.4 更新创作管理员

**接口**：`PUT /operators/{id}`

**权限**：超级管理员可更新所有，创作管理员仅可更新自己

**请求体**：
```typescript
{
  nickname?: string,
  password?: string,
  user_positioning?: string,
  status?: "online" | "offline" | "disabled",
  tag_ids?: number[]
}
```

#### 2.2.5 删除创作管理员

**接口**：`DELETE /operators/{id}`

**权限**：仅超级管理员

**说明**：软删除，该管理员下的创作者需要先转移或删除

#### 2.2.6 转移创作管理员

**接口**：`POST /operators/transfer`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  from_operator_id: number,  // 源创作管理员ID
  to_operator_id: number     // 目标创作管理员ID
}
```

**说明**：将一个创作管理员的所有创作者转移给另一个创作管理员

---

### 2.3 创作员管理

#### 2.3.1 获取创作者列表

**接口**：`GET /sub-users`

**权限**：超级管理员可查看所有，创作管理员仅可查看自己的创作者

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  keyword?: string,
  tag_id?: number,
  status?: "online" | "offline" | "disabled",
  account_type?: string,
  content_style?: string
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    userid: string,
    nickname: string,
    display_name?: string,
    role: "sub_user",
    status: "online" | "offline" | "disabled",
    user_positioning?: string,
    content_style?: string,
    account_type?: string,
    owner_admin_id: number,
    created_at: string,
    tags: Array<{
      id: number,
      name: string,
      color: string
    }>
  }>
}
```

#### 2.3.2 创建创作者

**接口**：`POST /sub-users`

**权限**：超级管理员可创建任意创作者，创作管理员仅可创建自己的创作者

**请求体**：
```typescript
{
  userid?: string,
  nickname: string,
  password?: string,        // 不传则自动生成随机密码
  user_positioning?: string,
  content_style?: string,   // 文案风格
  account_type?: string,    // 账号类型
  tag_ids?: number[],
  owner_admin_id?: number   // 超级管理员专属：指定归属创作管理员
}
```

#### 2.3.3 获取创作者详情

**接口**：`GET /sub-users/{id}`

**权限**：超级管理员可查看所有，创作管理员仅可查看自己的创作者

#### 2.3.4 更新创作者

**接口**：`PUT /sub-users/{id}`

**权限**：超级管理员可更新所有，创作管理员仅可更新自己的创作者

**请求体**：
```typescript
{
  nickname?: string,
  password?: string,
  user_positioning?: string,
  content_style?: string,
  account_type?: string,
  status?: "online" | "offline" | "disabled",
  tag_ids?: number[]
}
```

#### 2.3.5 删除创作者

**接口**：`DELETE /sub-users/{id}`

**权限**：超级管理员可删除所有，创作管理员仅可删除自己的创作者

**说明**：软删除账号

#### 2.3.6 转移创作者

**接口**：`POST /sub-users/transfer`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  sub_user_ids: number[],   // 要转移的创作者ID列表
  to_operator_id: number    // 目标创作管理员ID
}
```

---

### 2.4 用户标签管理

**说明**：每个用户（超级管理员/创作管理员）独立管理自己的标签，互不干扰。

#### 2.4.1 获取标签列表

**接口**：`GET /tags`

**请求参数**（Query）：
```typescript
{
  tag_type?: "operator_tag" | "subuser_tag"  // 标签类型，不传则返回所有
}
```

**响应**：
```typescript
[
  {
    id: number,
    name: string,
    tag_type: "operator_tag" | "subuser_tag",
    description?: string,
    color?: string,
    created_at: string,
    updated_at: string
  }
]
```

#### 2.4.2 创建标签

**接口**：`POST /tags`

**请求体**：
```typescript
{
  name: string,
  tag_type: "operator_tag" | "subuser_tag",
  description?: string,
  color?: string
}
```

#### 2.4.3 更新标签

**接口**：`PUT /tags/{id}`

**请求体**：
```typescript
{
  name?: string,
  description?: string,
  color?: string
}
```

#### 2.4.4 删除标签

**接口**：`DELETE /tags/{id}`

**说明**：同时删除与用户的关联关系，不删除用户本身

---

## 三、模板管理模块

### 多租户隔离说明

**重要原则**：
- 每个创作管理员（operator）的模板、平台、分类、标签完全独立，互不干扰
- 超级管理员（super_admin）可查看所有创作管理员的模板
- 所有模板相关接口自动基于当前用户的 `owner_admin_id` 进行数据隔离
- 平台、分类和标签也按创作管理员隔离，每个创作创作管理员自己的分类体系

### 四级层次结构

模板管理采用 **Platform → Category → Tag → Template** 四级结构：
1. **平台（Platform）**：如"小红书"、"抖音"
2. **分类（Category）**：平台下的内容分类，如"美食"、"旅游"
3. **标签（Tag）**：模板标签，用于进一步分类
4. **模板（Template）**：具体的内容模板

**重要**：超级管理员不能创建模板、平台、分类、标签，必须使用创作管理员账号操作。

---

### 3.1 模板管理

#### 3.1.1 获取模板列表

**接口**：`GET /`

**权限**：创作管理员仅可查看自己的模板，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  keyword?: string,
  platform_id?: number,
  category_id?: number,
  tag_ids?: string,            // 标签ID列表，逗号分隔
  content_type?: "text" | "image_text" | "video_text",
  status?: "enabled" | "disabled",
  owner_admin_id?: number      // 超级管理员专属：筛选特定创作管理员
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    name: string,
    description?: string,
    content_type: "text" | "image_text" | "video_text",
    platform: {
      id: number,
      name: string,
      color: string
    },
    category?: {
      id: number,
      name: string,
      color: string
    },
    tags: Array<{
      id: number,
      name: string,
      color: string
    }>,
    status: "enabled" | "disabled",
    usage_count?: number,
    created_at: string,
    updated_at: string
  }>
}
```

#### 3.1.2 获取模板详情

**接口**：`GET /{id}`

**权限**：创作管理员仅可查看自己的模板，超级管理员可查看所有

#### 3.1.3 创建模板

**接口**：`POST /`

**权限**：仅创作管理员（超级管理员不能创建）

**请求格式**：`multipart/form-data` 或 `application/json`

**请求体**：
```typescript
{
  name: string,
  description?: string,
  content_type: "text" | "image_text" | "video_text",
  platform_id: number,
  category_id?: number,
  prompt_template: string,
  variables_json: any,
  style_reference?: string,
  platform_rules_json?: any,
  tag_ids?: number[],
  
  // 图片生成配置
  default_image_config?: {
    size?: "1:1" | "3:4" | "4:3" | "9:16" | "16:9" | "custom",
    width?: number,
    height?: number,
    quality?: "low" | "medium" | "high" | "ultra",
    style?: string
  },
  
  // 视频生成配置
  default_video_config?: {
    aspect_ratio?: "9:16" | "16:9" | "1:1",
    duration?: number,
    resolution?: "720p" | "1080p" | "4k",
    fps?: number,
    style?: string
  }
}
```

#### 3.1.4 上传模板附件

**接口**：`POST /upload`

**权限**：仅创作管理员

**请求格式**：`multipart/form-data`

**请求参数**：
```typescript
{
  file: File,                  // 上传的文件
  template_id?: number         // 关联的模板ID（可选）
}
```

#### 3.1.5 更新模板

**接口**：`PUT /{id}`

**权限**：创作管理员仅可更新自己的模板，超级管理员可更新所有

#### 3.1.6 删除模板

**接口**：`DELETE /{id}`

**权限**：创作管理员仅可删除自己的模板，超级管理员可删除所有

**说明**：软删除，已使用该模板的生成任务仍可正常查看

#### 3.1.7 批量操作

**批量更新状态**：`POST /batch-update-status`

**请求体**：
```typescript
{
  template_ids: number[],
  status: "enabled" | "disabled"
}
```

**批量删除**：`POST /batch-delete`

**请求体**：
```typescript
{
  template_ids: number[]
}
```

**批量添加标签**：`POST /batch-add-tags`

**请求体**：
```typescript
{
  template_ids: number[],
  tag_ids: number[]
}
```

---

### 3.2 平台管理

#### 3.2.1 获取平台列表

**接口**：`GET /platforms`

**权限**：创作管理员仅可查看自己的平台，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  include_disabled?: boolean,
  owner_admin_id?: number      // 超级管理员专属
}
```

**响应**：
```typescript
[
  {
    id: number,
    name: string,
    description?: string,
    color?: string,
    sort_order: number,
    template_count?: number,
    status: "active" | "inactive",
    created_at: string,
    updated_at: string
  }
]
```

#### 3.2.2 创建平台

**接口**：`POST /platforms`

**权限**：仅创作管理员

**请求体**：
```typescript
{
  name: string,
  description?: string,
  color?: string,
  sort_order?: number
}
```

#### 3.2.3 更新平台

**接口**：`PUT /platforms/{id}`

**权限**：创作管理员仅可更新自己的平台，超级管理员可更新所有

#### 3.2.4 删除平台

**接口**：`DELETE /platforms/{id}`

**权限**：创作管理员仅可删除自己的平台，超级管理员可删除所有

**说明**：仅当该平台下没有模板时可删除

---

### 3.3 分类管理

#### 3.3.1 获取分类列表

**接口**：`GET /categories`

**权限**：创作管理员仅可查看自己的分类，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  platform_id?: number,        // 按平台筛选
  include_disabled?: boolean,
  owner_admin_id?: number      // 超级管理员专属
}
```

**响应**：
```typescript
[
  {
    id: number,
    name: string,
    description?: string,
    color?: string,
    platform_id: number,
    sort_order: number,
    template_count?: number,
    status: "active" | "inactive",
    created_at: string,
    updated_at: string
  }
]
```

#### 3.3.2 创建分类

**接口**：`POST /categories`

**权限**：仅创作管理员

**请求体**：
```typescript
{
  name: string,
  description?: string,
  color?: string,
  platform_id: number,
  sort_order?: number
}
```

#### 3.3.3 更新分类

**接口**：`PUT /categories/{id}`

**权限**：创作管理员仅可更新自己的分类，超级管理员可更新所有

#### 3.3.4 删除分类

**接口**：`DELETE /categories/{id}`

**权限**：创作管理员仅可删除自己的分类，超级管理员可删除所有

**说明**：仅当该分类下没有模板时可删除

---

### 3.4 标签管理

#### 3.4.1 获取标签列表

**接口**：`GET /tags`

**权限**：创作管理员仅可查看自己的标签，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  owner_admin_id?: number      // 超级管理员专属
}
```

**响应**：
```typescript
[
  {
    id: number,
    name: string,
    description?: string,
    color?: string,
    template_count?: number,
    created_at: string,
    updated_at: string
  }
]
```

#### 3.4.2 创建标签

**接口**：`POST /tags`

**权限**：仅创作管理员

**请求体**：
```typescript
{
  name: string,
  description?: string,
  color?: string
}
```

#### 3.4.3 更新标签

**接口**：`PUT /tags/{id}`

**权限**：创作管理员仅可更新自己的标签，超级管理员可更新所有

#### 3.4.4 删除标签

**接口**：`DELETE /tags/{id}`

**权限**：创作管理员仅可删除自己的标签，超级管理员可删除所有

**说明**：删除标签同时移除与模板的关联关系，不删除模板本身

---

## 四、素材管理模块

### 多租户隔离说明

**重要原则**：
- 每个创作管理员（operator）的素材、素材分类、素材标签完全独立，互不干扰
- 超级管理员（super_admin）可查看所有创作管理员的素材
- 所有素材相关接口自动基于当前用户的 `owner_admin_id` 进行数据隔离
- 素材分类和素材标签也按创作管理员隔离，每个创作创作管理员自己的分类体系

---

### 4.1 获取素材列表（分页）

**接口**：`GET /materials`

**请求参数**（Query）：
```typescript
{
  page?: number,              // 页码，默认1
  page_size?: number,          // 每页数量，默认20
  keyword?: string,            // 搜索关键词（标题/内容）
  category_id?: number,        // 素材分类ID筛选
  tag_ids?: string,            // 标签ID列表，逗号分隔（如"1,2,3"）
  content_type?: "text" | "image_text" | "video_text" | "mix",  // 内容类型筛选
  status?: "available" | "disabled",  // 状态筛选
  favorite?: boolean,          // 仅返回收藏的素材
  owner_admin_id?: number      // 【超级管理员专属】指定查看某个创作管理员的素材
}
```

**多租户说明**：
- 创作管理员：仅返回自己上传的素材
- 超级管理员：默认返回所有素材，可通过 `owner_admin_id` 筛选查看特定创作管理员的素材

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    total: number,
    items: Array<{
      id: number,
      title: string,
      content_type: "text" | "image_text" | "video_text" | "mix",
      category?: {
        id: number,
        name: string,
        color: string
      },
      tags: Array<{
        id: number,
        name: string,
        color: string
      }>,
      image_count: number,
      video_count: number,
      status: "available" | "disabled",
      is_favorite: boolean,
      usage_count?: number,      // 使用次数
      created_at: string,
      updated_at: string
    }>
  }
}
```

### 4.2 获取素材详情

**接口**：`GET /materials/:id`

**多租户说明**：
- 创作管理员：只能查看自己上传的素材，访问他人素材返回404
- 超级管理员：可查看任意素材

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    id: number,
    title: string,
    text_content?: string,
    source_url?: string,
    source_type: "upload" | "link" | "description",
    content_type: "text" | "image_text" | "video_text" | "mix",
    category_id?: number,
    category?: {
      id: number,
      name: string,
      color: string
    },
    image_count: number,
    video_count: number,
    status: "available" | "disabled",
    is_favorite: boolean,
    tag_ids: number[],              // 关联的标签ID列表
    tags?: Array<{
      id: number,
      name: string,
      color: string
    }>,
    attachments?: Array<{
      id: number,
      file_type: "image" | "video",
      file_url: string,
      file_name: string,
      file_size: number,
      sort_order: number,
      width?: number,
      height?: number,
      duration?: number,
      thumbnail_url?: string
    }>,
    original_material_id?: number,  // 复制来源素材ID
    created_by: number,
    owner_admin_id: number,
    created_at: string,
    updated_at: string
  }
}
```

### 4.3 创建/上传素材

**接口**：`POST /materials`

**多租户说明**：
- 自动将当前创作管理员的 ID 设置为 `owner_admin_id`
- 超级管理员创建素材时需指定 `owner_admin_id`

**请求格式**：`multipart/form-data`

**请求参数**：
```typescript
{
  title: string,                          // 素材标题
  text_content?: string,                  // 文本内容
  source_type: "upload" | "link" | "description",  // 来源类型
  source_url?: string,                    // 来源链接
  content_type: "text" | "image_text" | "video_text" | "mix",  // 内容类型
  category_id?: number,                   // 素材分类ID
  tag_ids?: number[],                     // 标签ID列表
  files?: File[],                         // 上传的文件（图片/视频）
  original_material_id?: number,          // 复制来源素材ID（可选，用于从已有素材复制）
  owner_admin_id?: number                 // 【超级管理员专属】指定素材的归属创作管理员
}
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    id: number,
    title: string,
    content_type: string,
    status: "available",
    created_at: string,
    updated_at: string
  }
}
```

### 4.4 更新素材

**接口**：`PUT /materials/:id`

**请求格式**：`multipart/form-data` 或 `application/json`

**请求参数**：
```typescript
{
  title?: string,
  text_content?: string,
  source_url?: string,
  source_type?: "upload" | "link" | "description",
  content_type?: "text" | "image_text" | "video_text" | "mix",
  category_id?: number,
  tag_ids?: number[],           // 覆盖原标签
  status?: "available" | "disabled",
  add_files?: File[],           // 新增的文件
  remove_attachment_ids?: number[]  // 要删除的附件ID列表
}
```

**响应**：同4.2获取素材详情

### 4.5 删除素材

**接口**：`DELETE /materials/:id`

**说明**：
- 软删除，素材不再显示在列表中
- 已使用该素材的生成任务仍可正常查看

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: null
}
```

### 4.6 复制素材

**接口**：`POST /materials/:id/copy`

**说明**：基于现有素材创建一个新素材

**请求体**：
```typescript
{
  title?: string  // 新素材标题，不传则自动生成（原标题_副本）
}
```

**响应**：同4.3创建素材

---

### 4.7 素材分类管理

#### 4.7.1 获取分类列表

**接口**：`GET /materials/categories`

**请求参数**（Query）：
```typescript
{
  include_disabled?: boolean,  // 是否包含已禁用的分类，默认false
  owner_admin_id?: number       // 【超级管理员专属】指定查看某个创作管理员的分类
}
```

**多租户说明**：
- 创作管理员：仅返回自己创建的分类
- 超级管理员：默认返回所有分类，可通过 `owner_admin_id` 筛选

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: Array<{
    id: number,
    name: string,
    description?: string,
    color?: string,
    sort_order: number,
    material_count?: number,  // 该分类下的素材数量
    status: "active" | "inactive",
    created_at: string,
    updated_at: string
  }>
}
```

#### 4.7.2 创建分类

**接口**：`POST /materials/categories`

**多租户说明**：
- 自动将当前创作管理员的 ID 设置为 `owner_admin_id`
- 每个创作管理员的分类列表独立，互不影响
- 分类名称在同一创作管理员下唯一

**请求体**：
```typescript
{
  name: string,
  description?: string,
  color?: string,           // 颜色值，如#409EFF
  sort_order?: number       // 排序值，默认0
}
```

#### 4.7.3 更新分类

**接口**：`PUT /materials/categories/:id`

**请求体**：
```typescript
{
  name?: string,
  description?: string,
  color?: string,
  sort_order?: number,
  status?: "active" | "inactive"
}
```

#### 4.7.4 删除分类

**接口**：`DELETE /materials/categories/:id`

**说明**：
- 仅当该分类下没有素材时可删除
- 或选择将素材迁移到其他分类

**请求参数**（Query）：
```typescript
{
  migrate_to_category_id?: number  // 迁移目标分类ID
}
```

---

### 4.8 素材标签管理

#### 4.8.1 获取标签列表

**接口**：`GET /materials/tags`

**请求参数**（Query）：
```typescript
{
  owner_admin_id?: number  // 【超级管理员专属】指定查看某个创作管理员的标签
}
```

**多租户说明**：
- 创作管理员：仅返回自己创建的标签
- 超级管理员：默认返回所有标签，可通过 `owner_admin_id` 筛选

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: Array<{
    id: number,
    name: string,
    description?: string,
    color?: string,
    material_count?: number,  // 使用该标签的素材数量
    created_at: string,
    updated_at: string
  }>
}
```

#### 4.8.2 创建标签

**接口**：`POST /materials/tags`

**请求体**：
```typescript
{
  name: string,
  description?: string,
  color?: string  // 颜色值，如#409EFF
}
```

#### 4.8.3 更新标签

**接口**：`PUT /materials/tags/:id`

**请求体**：
```typescript
{
  name?: string,
  description?: string,
  color?: string
}
```

#### 4.8.4 删除标签

**接口**：`DELETE /materials/tags/:id`

**说明**：删除标签同时移除与素材的关联关系，不删除素材本身

---

### 4.9 按分类/标签分组获取素材

**接口**：`GET /materials/grouped`

**说明**：获取按分类或标签分组的素材列表，用于侧边栏导航

**请求参数**（Query）：
```typescript
{
  group_by: "category" | "tag",  // 分组方式
  owner_admin_id?: number         // 【超级管理员专属】指定查看某个创作管理员的分组
}
```

**响应**（按分类分组）：
```typescript
{
  code: 0,
  message: "success",
  data: Array<{
    group: {
      id: number,
      name: string,
      color?: string
    },
    material_count: number,
    materials: Array<{
      id: number,
      title: string,
      content_type: string,
      status: string
    }>
  }>
}
```

---

## 五、内容生成模块（核心）

### 多租户隔离说明
- 每个创作管理员（operator）的生成任务完全隔离，互不干扰
- 超级管理员（super_admin）可查看所有创作管理员的任务
- 所有生成相关接口自动基于当前用户的 `owner_admin_id` 进行数据隔离

---

### 5.1 任务管理

#### 5.1.1 创建生成任务

**接口**：`POST /tasks`

**权限**：仅创作管理员

**请求体**：
```typescript
{
  material_id: number,
  template_ids: number[],
  model_selection_mode?: "auto" | "manual",
  model_platform?: string,
  model_id?: string,
  max_concurrency?: number,
  variable_values: Record<string, any>,
  dedup_rules?: any,
  subuser_ids: number[],
  
  // 图片生成配置
  image_config?: {
    size?: "1:1" | "3:4" | "4:3" | "9:16" | "16:9" | "custom",
    width?: number,
    height?: number,
    quality?: "low" | "medium" | "high" | "ultra",
    style?: string
  },
  
  // 视频生成配置
  video_config?: {
    aspect_ratio?: "9:16" | "16:9" | "1:1",
    duration?: number,
    resolution?: "720p" | "1080p" | "4k",
    fps?: number,
    style?: string
  }
}
```

**响应**：
```typescript
{
  id: number,
  status: "queued",
  total_count: number,
  created_at: string
}
```

**说明**：
- 创建任务后，系统自动为每个（创作者、模板）组合创建子任务（generation_item）
- 任务提交到Celery异步队列处理

#### 5.1.2 获取任务列表

**接口**：`GET /tasks`

**权限**：创作管理员仅可查看自己的任务，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  status?: "queued" | "generating" | "completed" | "failed" | "paused",
  start_date?: string,
  end_date?: string,
  owner_admin_id?: number      // 超级管理员专属
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    material: {
      id: number,
      title: string
    },
    status: string,
    total_count: number,
    queued_count: number,
    generating_count: number,
    completed_count: number,
    failed_count: number,
    paused_count: number,
    distributed_count: number,
    pending_publish_count: number,
    published_count: number,
    created_at: string,
    updated_at: string
  }>
}
```

#### 5.1.3 获取任务详情

**接口**：`GET /tasks/{id}`

**权限**：创作管理员仅可查看自己的任务，超级管理员可查看所有

**响应**：
```typescript
{
  id: number,
  material: any,
  templates: Array<any>,
  model_platform: string,
  model_id: string,
  model_selection_mode: "auto" | "manual",
  max_concurrency: number,
  status: string,
  total_count: number,
  queued_count: number,
  generating_count: number,
  completed_count: number,
  failed_count: number,
  paused_count: number,
  distributed_count: number,
  pending_publish_count: number,
  published_count: number,
  created_at: string,
  updated_at: string,
  progress_logs: Array<{
    created_at: string,
    queued_count: number,
    generating_count: number,
    completed_count: number,
    failed_count: number,
    paused_count: number,
    status: string,
    progress_message: string
  }>
}
```

#### 5.1.4 取消任务

**接口**：`POST /tasks/{id}/cancel`

**权限**：创作管理员仅可取消自己的任务，超级管理员可取消所有

#### 5.1.5 重试失败项

**接口**：`POST /tasks/{id}/retry`

**权限**：创作管理员仅可重试自己的任务，超级管理员可重试所有

**请求体**：
```typescript
{
  item_ids?: number[]    // 不传则重试所有失败项
}
```

---

### 5.2 子任务管理

#### 5.2.1 获取子任务列表

**接口**：`GET /items`

**权限**：创作管理员仅可查看自己的子任务，超级管理员可查看所有

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  task_id?: number,
  status?: "queued" | "generating" | "completed" | "failed" | "paused",
  distribution_status?: "pending_publish" | "published"
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    task_id: number,
    sub_user: {
      id: number,
      nickname: string,
      content_style?: string,
      account_type?: string
    },
    template: {
      id: number,
      name: string
    },
    model_platform?: string,
    model_id?: string,
    status: string,
    generated_title?: string,
    generated_text?: string,
    generated_image_urls_json?: string[],
    generated_video_url?: string,
    retry_count: number,
    error_message?: string,
    queued_at?: string,
    started_at?: string,
    completed_at?: string,
    distribution_status?: string,
    created_at: string,
    updated_at: string
  }>
}
```

#### 5.2.2 获取子任务详情

**接口**：`GET /items/{id}`

**权限**：创作管理员仅可查看自己的子任务，超级管理员可查看所有

#### 5.2.3 暂停子任务

**接口**：`POST /items/{id}/pause`

**权限**：创作管理员仅可暂停自己的子任务，超级管理员可暂停所有

#### 5.2.4 继续子任务

**接口**：`POST /items/{id}/resume`

**权限**：创作管理员仅可继续自己的子任务，超级管理员可继续所有

#### 5.2.5 重试子任务

**接口**：`POST /items/{id}/retry`

**权限**：创作管理员仅可重试自己的子任务，超级管理员可重试所有

---

### 5.3 创作者专属接口

#### 5.3.1 获取我的生成内容

**接口**：`GET /sub-user-items`

**权限**：仅创作者

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  status?: "queued" | "generating" | "completed" | "failed" | "paused",
  distribution_status?: "pending_publish" | "published"
}
```

**响应**：
```typescript
{
  total: number,
  items: Array<{
    id: number,
    generated_title?: string,
    generated_text?: string,
    generated_image_urls_json?: string[],
    generated_video_url?: string,
    status: string,
    distribution_status?: string,
    created_at: string,
    updated_at: string
  }>
}
```

---

### 5.4 调试接口

#### 5.4.1 调试生成任务

**接口**：`POST /debug/generate`

**权限**：仅创作管理员

**说明**：用于测试生成逻辑，不创建实际任务

**请求体**：
```typescript
{
  material_id: number,
  template_id: number,
  sub_user_id: number,
  model_platform?: string,
  model_id?: string
}
```

#### 5.4.2 调试提示词生成

**接口**：`POST /debug/prompt`

**权限**：仅创作管理员

**说明**：测试提示词生成逻辑

---

### 5.5 WebSocket 实时进度

**接口**：`WS /ws/generation/{task_id}`

**消息格式**：
```typescript
// 服务器推送
{
  type: "progress",
  data: {
    task_id: number,
    queued_count: number,
    generating_count: number,
    completed_count: number,
    failed_count: number,
    status: string,
    timestamp: string
  }
}

// 单个item完成消息
{
  type: "item_completed",
  data: {
    item_id: number,
    status: "completed" | "failed",
    generated_title?: string,
    generated_text?: string
  }
}
```

---

## 六、内容分发模块

### 6.1 分发内容

**接口**：`POST /distribution`

**请求体**：
```typescript
{
  task_id: number,                    // 生成任务ID
  generation_item_ids?: number[],     // 指定要分发的明细ID列表（不传则分发所有完成项）
  subuser_ids?: number[]              // 指定要分发给的创作者（不传则使用原任务的创作者）
}
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    distribution_count: number,
    distributions: Array<{
      id: number,
      generation_item_id: number,
      sub_user_id: number,
      publish_status: "distributed"
    }>
  }
}
```

### 6.2 获取分发记录列表（创作管理员）

**接口**：`GET /distribution`

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  task_id?: number,
  subuser_id?: number,
  publish_status?: "distributed" | "pending_publish" | "published"
}
```

### 6.3 获取创作者内容列表（创作者）

**接口**：`GET /distribution/my`

**请求参数**（Query）：
```typescript
{
  page?: number,
  page_size?: number,
  publish_status?: "distributed" | "pending_publish" | "published"
}
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    total: number,
    items: Array<{
      id: number,
      generation_item: {
        id: number,
        generated_title: string,
        generated_text: string,
        generated_image_urls_json: string[],
        generated_video_url?: string
      },
      publish_status: string,
      distributed_at: string,
      confirmed_at?: string
    }>
  }
}
```

### 6.4 确认发布（创作者）

**接口**：`POST /distribution/:id/confirm`

---

## 七、个人设置模块

### 权限说明
- **所有角色**：均可访问和修改自己的个人设置

---

### 7.1 获取当前用户信息

**接口**：`GET /user/profile`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    id: number,
    userid: string,
    nickname?: string,              // 【管理备注名】管理员备注名（仅管理员自己可见）
    display_name: string,            // 【自定义昵称】用户自定义显示昵称
    role: "super_admin" | "operator" | "sub_user",
    avatar?: string,
    
    user_positioning?: string,
    user_category?: string,
    content_style?: string,          // 【创作者专属】文案风格
    account_type?: string,            // 【创作者专属】账号类型
    created_at: string,
    last_login_at?: string
  }
}
```

---

### 7.2 更新个人信息

**接口**：`PUT /user/profile`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```typescript
{
  display_name?: string,            // 【自定义昵称】修改用户自定义显示昵称
  // 注意：nickname（管理备注名）只能由管理员在用户管理中修改
  user_positioning?: string,        // 账号定位（可选）
  user_category?: string,           // 账号分类（可选）
  content_style?: string,           // 【创作者专属】文案风格（可选）
  account_type?: string             // 【创作者专属】账号类型（可选）
}
```

**响应**：同7.1获取当前用户信息

---

### 7.3 修改密码

**接口**：`POST /user/change-password`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```typescript
{
  old_password: string,             // 原密码（必填）
  new_password: string,             // 新密码（必填，长度至少6位）
  confirm_password: string          // 确认新密码（必填，需与new_password一致）
}
```

**响应**：
```typescript
{
  code: 0,
  message: "密码修改成功",
  data: null
}
```

**错误码**：
| 错误码 | 说明 |
|--------|------|
| 40011 | 原密码错误 |
| 40012 | 两次输入的新密码不一致 |
| 40013 | 新密码长度不足6位 |
| 40014 | 新密码与原密码相同 |

---

## 八、系统设置模块

### 权限说明
- **超级管理员**：可管理所有模型配置，可添加/删除自定义模型
- **创作管理员**：可查看模型配置，可设置自己的默认模型

---

### 8.1 模型配置管理

#### 8.1.1 获取模型配置列表

**接口**：`GET /model-configs`

**权限**：所有角色可查看

**请求参数**（Query）：
```typescript
{
  platform?: string,
  model_type?: "llm" | "image" | "video",
  status?: "active" | "inactive"
}
```

**响应**：
```typescript
[
  {
    id: number,
    platform: string,
    model_id: string,
    model_name: string,
    model_type: "llm" | "image" | "video",
    base_url?: string,
    api_endpoint: string,
    is_default: boolean,
    max_concurrency: number,
    is_system: boolean,
    status: "active" | "inactive",
    created_at: string,
    updated_at: string
  }
]
```

#### 8.1.2 创建模型配置

**接口**：`POST /model-configs`

**权限**：仅超级管理员

**请求体**：
```typescript
{
  platform: string,
  model_id: string,
  model_name: string,
  model_type: "llm" | "image" | "video",
  base_url?: string,
  api_endpoint: string,
  is_default?: boolean,
  max_concurrency: number,
  config_json: Record<string, any>,
  status?: "active" | "inactive"
}
```

#### 8.1.3 更新模型配置

**接口**：`PUT /model-configs/{id}`

**权限**：仅超级管理员

#### 8.1.4 删除模型配置

**接口**：`DELETE /model-configs/{id}`

**权限**：仅超级管理员

**说明**：仅可删除自定义模型（is_system=false）

---

### 8.2 用户默认模型设置

#### 8.2.1 获取用户默认模型

**接口**：`GET /user-default-models`

**权限**：所有角色

**响应**：
```typescript
{
  llm_model_id?: number,
  image_model_id?: number,
  video_model_id?: number
}
```

#### 8.2.2 设置用户默认模型

**接口**：`POST /user-default-models`

**权限**：超级管理员和创作管理员

**请求体**：
```typescript
{
  model_type: "llm" | "image" | "video",
  model_id: number
}
```

---

### 8.3 平台模型类型查询

**接口**：`GET /platform-model-types`

**权限**：所有角色

**说明**：获取各平台支持的模型类型

**响应**：
```typescript
[
  {
    platform: string,
    platform_name: string,
    model_types: Array<"llm" | "image" | "video">,
    description?: string
  }
]
```

---

### 8.4 支持的模型平台

#### 平台列表

| 平台标识 | 平台名称 | 支持的模型类型 | 认证方式 |
|---------|---------|--------------|---------|
| bailian | 百炼 | llm, image, video | API Key |
| volcano | 火山引擎 | llm, image, video | API Key |
| jimeng | 即梦 | image, video | AccessKey + SecretKey |
| kling | 可灵 | image, video | AccessKey + SecretKey |
| autoglm | AutoGLM | llm | API Key |
| moonshot | 月之暗面 | llm | API Key |
| deepseek | DeepSeek | llm | API Key |
| lingyaai | 灵雅AI | llm | API Key |

#### 认证方式说明

**标准 API Key 认证**（6个平台）：
- bailian, volcano, autoglm, moonshot, deepseek, lingyaai
- 配置 `config_json` 时需提供：`{"api_key": "your-api-key"}`

**AccessKey + SecretKey 认证**（2个平台）：
- jimeng, kling
- 配置 `config_json` 时需提供：`{"access_key": "your-access-key", "secret_key": "your-secret-key"}`

#### 大语言模型配置

对于大语言模型（model_type="llm"），需额外配置：
- `base_url`：API Base URL
- `model_id`：模型标识符

示例：
```typescript
{
  platform: "deepseek",
  model_id: "deepseek-chat",
  model_name: "DeepSeek Chat",
  model_type: "llm",
  base_url: "https://api.deepseek.com/v1",
  api_endpoint: "/chat/completions",
  config_json: {
    "api_key": "sk-xxxxx"
  }
}
```

---

## 九、创意种子库模块

### 权限说明
- **创作管理员**：可管理自己的创意种子，可使用系统种子
- **超级管理员**：可管理所有创意种子（包括系统种子）

### 9.1 获取种子类型枚举

**接口**：`GET /creative-seeds/types`

**响应**：
```typescript
{
  seed_types: {
    opening: { label: "开头模式", description: "控制文案开头的风格" },
    emotion: { label: "情感基调", description: "控制文案的情感表达" },
    ending: { label: "结尾模式", description: "控制文案的收尾方式" }
  },
  categories: ["通用", "美妆护肤", "服饰穿搭", "美食探店", "家居生活", ...]
}
```

### 9.2 获取分组种子列表（用于下拉选择）

**接口**：`GET /creative-seeds/grouped`

**查询参数**：
- `category`: 品类筛选（可选）

**响应**：
```typescript
{
  opening: [
    { id: 1, name: "反常识开头", seed_type: "opening", template: "...", category: "通用" },
    ...
  ],
  emotion: [
    { id: 8, name: "轻松吐槽", seed_type: "emotion", template: "...", category: "通用" },
    ...
  ],
  ending: [
    { id: 15, name: "求建议", seed_type: "ending", template: "...", category: "通用" },
    ...
  ]
}
```

### 9.3 获取种子列表

**接口**：`GET /creative-seeds`

**查询参数**：
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）
- `seed_type`: 种子类型筛选（opening/emotion/ending）
- `category`: 品类筛选
- `status`: 状态筛选（enabled/disabled）
- `keyword`: 关键词搜索

**响应**：
```typescript
{
  items: [
    {
      id: 1,
      name: "反常识开头",
      seed_type: "opening",
      template: "[\"没想到这个xxx居然...\", \"谁能想到xxx竟然...\"]",
      description: "用反常识或意外的角度开头，打破读者预期",
      forbidden_patterns: ["最近买了", "上周入手", "大家好"],
      example_phrases: ["没想到", "谁能想到"],
      avoid_phrases: ["众所周知", "大家都知道"],
      category: "通用",
      status: "enabled",
      is_system: true,
      owner_operator_id: null,
      use_count: 150,
      success_rate: 0.92,
      created_at: "2026-05-01T00:00:00Z",
      updated_at: "2026-05-10T00:00:00Z"
    }
  ],
  total: 50,
  page: 1,
  limit: 20,
  total_pages: 3
}
```

### 9.4 获取种子详情

**接口**：`GET /creative-seeds/:id`

**响应**：同列表项结构

### 9.5 创建创意种子

**接口**：`POST /creative-seeds`

**权限**：仅创作管理员可创建

**请求体**：
```typescript
{
  name: "自定义开头",
  seed_type: "opening",
  template: "[\"这是一个自定义开头模板...\"]",
  description: "自定义开头模式说明",
  forbidden_patterns: ["禁止模式1", "禁止模式2"],
  example_phrases: ["示例1", "示例2"],
  avoid_phrases: ["避免1"],
  category: "美妆护肤",
  status: "enabled"
}
```

### 9.6 更新创意种子

**接口**：`PUT /creative-seeds/:id`

**权限说明**：
- 创作管理员：只能更新自己的种子（系统种子仅可修改状态）
- 超级管理员：可更新所有种子

**请求体**：同创建请求

### 9.7 删除创意种子

**接口**：`DELETE /creative-seeds/:id`

**权限说明**：
- 创作管理员：只能删除自己的种子（系统种子不可删除）
- 超级管理员：可删除所有种子（包括系统种子）

### 9.8 增加种子使用次数

**接口**：`POST /creative-seeds/:id/increment-use`

**说明**：在文案生成成功后调用，记录使用次数

---

### 10.1 小红书App快速发布（Web端）

**说明**：本功能基于小红书官方 JS SDK 实现，支持从Web端一键分享内容到小红书App。

#### 10.4.1 获取小红书分享配置

**接口**：`GET /xiaohongshu/share-config`

**说明**：获取小红书JS SDK分享所需的配置信息（不包含敏感的appSecret）。

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    enabled: boolean,                    // 是否启用小红书分享
    app_key: string,                     // 小红书开放平台appKey
    sdk_url: "https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js",  // JS SDK地址
  }
}
```

#### 9.4.2 获取小红书JS SDK签名（关键接口）

**接口**：`POST /xiaohongshu/signature`

**说明**：后端调用小红书API获取access_token，并生成JS SDK所需的签名。
此接口执行两次签名流程：
1. 第一次签名：使用appSecret获取access_token
2. 第二次签名：使用access_token生成JS SDK签名

**请求体**：
```typescript
{
  // 无请求参数，后端自动生成nonce和timestamp
}
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    app_key: string,       // 应用标识
    nonce: string,         // 随机字符串
    timestamp: string,     // 时间戳（毫秒）
    signature: string      // 签名
  }
}
```

#### 9.4.3 获取内容的小红书分享数据

**接口**：`GET /xiaohongshu/content/:id/share-data`

**说明**：获取指定内容的小红书分享数据包。

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    content_id: number,
    type: 'normal' | 'video',        // 笔记类型：normal(图文) | video(视频)
    title?: string,                   // 笔记标题
    content?: string,                 // 笔记正文
    images?: string[],                // 图文类型必填，图片URL数组（必须是服务器地址）
    video?: string,                   // 视频类型必填，视频URL（必须是服务器地址）
    cover?: string                    // 视频封面图URL（必须是服务器地址）
  }
}
```

#### 9.4.4 记录分享到小红书

**接口**：`POST /xiaohongshu/content/:id/share`

**说明**：在用户成功分享到小红书后，调用此接口记录分享操作。

**请求体**：
```typescript
{
  share_time: string,                      // 分享时间（ISO 8601）
  status: "success" | "cancelled" | "failed",  // 分享状态
  error_message?: string,                  // 失败原因（如果失败）
}
```

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: {
    share_record_id: number,
    published_at?: string                  // 发布时间（如果成功）
  }
}
```

#### 9.4.5 获取小红书分享记录

**接口**：`GET /xiaohongshu/content/:id/shares`

**说明**：获取某条内容的小红书分享历史记录。

**响应**：
```typescript
{
  code: 0,
  message: "success",
  data: Array<{
    id: number,
    status: "success" | "cancelled" | "failed",
    share_time: string,
    error_message?: string
  }>
}
```

---

## 小红书JS SDK Web端集成说明

### 小红书官方JS SDK说明

小红书 JS SDK 是面向网页开发者提供的基于分享内容到小红书 App 的网页开发工具包。

**官方SDK地址**：`https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js`

### Web端完整实现流程

```
1. 引入小红书JS SDK
   <script src="https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js"></script>

2. 获取分享配置
   GET /xiaohongshu/share-config

3. 获取SDK签名（每次分享前调用）
   POST /xiaohongshu/signature

4. 获取内容分享数据
   GET /xiaohongshu/content/{id}/share-data

5. 调用xhs.share()方法唤起小红书App

6. 用户在小红书发布完成后，记录分享结果
   POST /xiaohongshu/content/{id}/share
```

### 前端代码示例

```html
<!-- 引入小红书JS SDK -->
<script src="https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js"></script>

<script>
// 分享到小红书函数
async function shareToXiaohongshu(contentId) {
  try {
    // 1. 获取SDK签名
    const signRes = await fetch('/api/v1/xiaohongshu/signature', {
      method: 'POST'
    }).then(r => r.json())
    
    if (signRes.code !== 0) {
      throw new Error(signRes.message)
    }
    
    const verifyConfig = signRes.data
    
    // 2. 获取内容分享数据
    const contentRes = await fetch(`/api/v1/xiaohongshu/content/${contentId}/share-data`)
      .then(r => r.json())
    
    if (contentRes.code !== 0) {
      throw new Error(contentRes.message)
    }
    
    const shareInfo = contentRes.data
    
    // 3. 调用小红书SDK分享
    xhs.share({
      shareInfo: shareInfo,
      verifyConfig: verifyConfig,
      fail: (e) => {
        console.error('分享失败:', e)
        // 记录分享失败
        recordShareResult(contentId, 'failed', e.message)
      }
    })
    
    // 4. 记录分享成功（用户实际发布后可进一步确认）
    recordShareResult(contentId, 'success')
    
  } catch (error) {
    console.error('分享流程出错:', error)
  }
}

// 记录分享结果
async function recordShareResult(contentId, status, errorMessage) {
  await fetch(`/api/v1/xiaohongshu/content/${contentId}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      share_time: new Date().toISOString(),
      status: status,
      error_message: errorMessage
    })
  })
}
</script>
```

### 后端签名实现说明

#### 签名算法

签名生成规则：
1. 参与签名的字段：nonce（随机字符串）、timeStamp（时间戳）、appKey（应用标识）
2. 对所有待签名参数按键名排序，使用URL键值对格式拼接（key1=value1&key2=value2...）
3. 在拼接的字符串后直接拼接密钥（第一次用appSecret，第二次用access_token）
4. 对最终字符串作SHA-256加密，得到签名

#### 后端签名代码示例（Python）

```python
import hashlib
import time
import random
import string
import requests
from typing import Dict, Tuple

class XiaohongshuSignature:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.access_token_expires = 0
    
    def generate_nonce(self, length: int = 16) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_signature(self, params: Dict[str, str], secret: str) -> str:
        """生成签名"""
        # 按key排序
        sorted_params = sorted(params.items())
        # 拼接参数
        param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
        # 拼接密钥
        sign_str = param_str + secret
        # SHA-256加密
        sha256 = hashlib.sha256()
        sha256.update(sign_str.encode('utf-8'))
        return sha256.hexdigest()
    
    def get_access_token(self) -> str:
        """获取access_token（第一次签名）"""
        # 检查token是否有效
        if self.access_token and time.time() * 1000 < self.access_token_expires:
            return self.access_token
        
        nonce = self.generate_nonce()
        timestamp = str(int(time.time() * 1000))
        
        # 第一次签名：使用appSecret
        params = {
            'appKey': self.app_key,
            'nonce': nonce,
            'timeStamp': timestamp
        }
        signature = self.generate_signature(params, self.app_secret)
        
        # 调用小红书API
        url = 'https://edith.xiaohongshu.com/api/sns/v1/ext/access/token'
        data = {
            'app_key': self.app_key,
            'nonce': nonce,
            'timestamp': int(timestamp),
            'signature': signature
        }
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get('success'):
            self.access_token = result['data']['access_token']
            self.access_token_expires = result['data']['expires_in']
            return self.access_token
        else:
            raise Exception(f'获取access_token失败: {result}')
    
    def get_js_sdk_signature(self) -> Dict[str, str]:
        """获取JS SDK签名（第二次签名）"""
        access_token = self.get_access_token()
        nonce = self.generate_nonce()
        timestamp = str(int(time.time() * 1000))
        
        # 第二次签名：使用access_token
        params = {
            'appKey': self.app_key,
            'nonce': nonce,
            'timeStamp': timestamp
        }
        signature = self.generate_signature(params, access_token)
        
        return {
            'app_key': self.app_key,
            'nonce': nonce,
            'timestamp': timestamp,
            'signature': signature
        }
```

---

## 错误码定义

| 错误码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如重复创建） |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

### 常见错误响应示例

**参数错误**：
```typescript
{
  "detail": "Invalid request parameters"
}
```

**认证失败**：
```typescript
{
  "detail": "Could not validate credentials"
}
```

**权限不足**：
```typescript
{
  "detail": "Not enough permissions"
}
```

**资源不存在**：
```typescript
{
  "detail": "Resource not found"
}
```

**账号锁定**：
```typescript
{
  "detail": "Account is locked due to multiple failed login attempts. Please try again after 15 minutes."
}
```

---

## 分页参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | number | 1 | 页码，从1开始 |
| page_size | number | 20 | 每页数量，最大100 |

---

## 日期时间格式

所有日期时间字段使用ISO 8601格式：
```
YYYY-MM-DDTHH:mm:ss.SSSZ
例如：2025-03-29T12:00:00.000Z
```

---

## WebSocket 连接流程

1. 前端连接：`ws://localhost:8000/ws/generation/{task_id}?token={access_token}`
2. 认证通过后，服务器开始推送进度
3. 任务完成后，连接保持，可继续获取后续更新
4. 前端可通过心跳包保持连接

---

## 文件上传说明

所有文件上传使用腾讯云COS：
1. 前端请求上传签名：`POST /storage/upload-signature`
2. 使用签名直接上传到COS
3. 将返回的file_url传给后端

---

## 图片/视频尺寸配置说明

### 图片尺寸选项

| 尺寸比例 | 说明 | 常见分辨率 | 适用场景 |
|----------|------|-----------|---------|
| 1:1 | 正方形 | 1024×1024, 1080×1080 | 微信朋友圈、小红书正方形笔记、Instagram |
| 3:4 | 竖版3:4 | 768×1024, 900×1200 | 小红书、抖音图文 |
| 4:3 | 横版4:3 | 1024×768, 1200×900 | 公众号头图、横版展示 |
| 9:16 | 竖版9:16 | 1080×1920, 720×1280 | 抖音、快手、视频号竖屏 |
| 16:9 | 横版16:9 | 1920×1080, 1280×720 | YouTube、B站、视频号横屏 |
| custom | 自定义尺寸 | 用户自定义width×height | 特殊需求场景 |

### 图片质量选项

| 质量等级 | 说明 | 建议使用场景 | 文件大小参考 |
|----------|------|-------------|-------------|
| low | 低质量 | 预览、测试 | ~100-300KB |
| medium | 中等质量 | 日常使用 | ~300-800KB |
| high | 高质量 | 正式发布 | ~800KB-2MB |
| ultra | 超高质量 | 打印、专业用途 | ~2MB-5MB |

### 视频宽高比选项

| 宽高比 | 说明 | 常见分辨率 | 适用场景 |
|--------|------|-----------|---------|
| 9:16 | 竖版9:16 | 1080×1920, 720×1280 | 抖音、快手、视频号竖屏 |
| 16:9 | 横版16:9 | 1920×1080, 1280×720 | YouTube、B站、视频号横屏 |
| 1:1 | 正方形 | 1080×1080 | 微信朋友圈、Instagram |

### 视频分辨率选项

| 分辨率 | 说明 | 适用场景 | 码率建议 |
|--------|------|---------|---------|
| 720p | 1280×720 | 网络传播、日常分享 | 2-4 Mbps |
| 1080p | 1920×1080 | 高清视频、正式发布 | 5-10 Mbps |
| 4k | 3840×2160 | 超高清、专业制作 | 16-40 Mbps |

### 视频帧率选项

| 帧率 | 说明 | 适用场景 |
|------|------|---------|
| 24 fps | 电影帧率 | 电影感、叙事类视频 |
| 30 fps | 标准帧率 | 大多数场景通用 |
| 60 fps | 高帧率 | 运动、游戏类视频 |

### 各平台推荐配置

#### 小红书
- 图片推荐：
  - 尺寸：3:4（1080×1440）或 1:1（1080×1080）
  - 质量：high 或 ultra
- 视频推荐：
  - 宽高比：9:16
  - 分辨率：1080p
  - 帧率：30 fps

#### 抖音/快手
- 图片推荐：
  - 尺寸：9:16（1080×1920）
  - 质量：high
- 视频推荐：
  - 宽高比：9:16
  - 分辨率：1080p
  - 帧率：30 fps

#### 微信视频号
- 图片推荐：
  - 尺寸：16:9（1920×1080）或 9:16（1080×1920）
  - 质量：high
- 视频推荐：
  - 宽高比：16:9 或 9:16
  - 分辨率：1080p
  - 帧率：30 fps

#### 微信公众号
- 图片推荐：
  - 封面图：16:9（1920×1080）或 2.35:1（2.35:1）
  - 正文图：1:1（1080×1080）或 16:9（1920×1080）
  - 质量：medium 或 high
- 视频推荐：
  - 宽高比：16:9
  - 分辨率：1080p
  - 帧率：30 fps

#### B站/YouTube
- 图片推荐：
  - 封面图：16:9（1920×1080）
  - 质量：high
- 视频推荐：
  - 宽高比：16:9
  - 分辨率：1080p 或 4k
  - 帧率：30 fps 或 60 fps

### 前端UI设计建议

1. **分步骤选择**：
   - 第一步：选择内容类型（图文/视频）
   - 第二步：选择目标平台（自动推荐配置）
   - 第三步：手动调整细节（可选）

2. **快速预设**：
   - 提供常用平台的"一键配置"按钮
   - 例如："小红书配置"、"抖音配置"等

3. **高级模式**：
   - 默认隐藏高级选项
   - 点击"高级设置"展开自定义选项

4. **实时预览**：
   - 选择尺寸时显示比例预览图
   - 提示适用场景说明
