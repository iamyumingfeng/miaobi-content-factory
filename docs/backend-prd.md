# 妙笔内容工场 - 后端服务详细 PRD

## 一、产品概述

### 1.1 产品定位

妙笔内容工场后端服务是整个平台的核心，提供：

- **用户管理**: 超级管理员、创作管理员、创作者的三级管理体系
- **模板管理**: Prompt 模板的创建、编辑、分类管理
- **素材管理**: 参考素材的上传、存储、分类管理
- **内容生成**: 基于 AI 模型的批量内容生成引擎
- **内容分发**: 生成内容向创作者的批量分发
- **发布确认**: 创作者确认发布的状态跟踪

### 1.2 核心价值

- **提效**: 批量生成，分发自动化
- **保质**: 去重、去 AI 味，差异化生成
- **可控**: 实时进度监控，失败重试
- **安全**: 角色隔离，数据隔离

## 二、技术架构

### 2.1 技术栈

| 组件 | 技术选型 | 版本要求 |
|------|---------|---------|
| 框架 | FastAPI | 0.104+ |
| Python | Python | 3.11+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | MySQL | 8.0+ |
| 缓存/队列 | Redis | 7.0+ |
| 异步任务 | Celery | 5.3+ |
| 迁移工具 | Alembic | 最新版 |
| 文档 | OpenAPI/Swagger | - |

### 2.2 项目结构

```
platform_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/                    # API 路由
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # 认证
│   │       ├── users.py        # 用户管理
│   │       ├── templates.py    # 模板管理
│   │       ├── materials.py    # 素材管理
│   │       ├── generation.py   # 内容生成
│   │       ├── distribution.py # 内容分发
│   │       ├── settings.py     # 系统设置
│   │       └── miniprogram.py  # 小程序
│   ├── core/                   # 核心组件
│   │   ├── config.py          # 配置
│   │   ├── database.py        # 数据库
│   │   ├── security.py        # 安全
│   │   └── exceptions.py      # 异常
│   ├── models/                 # 数据模型
│   ├── schemas/               # Pydantic 模型
│   ├── services/              # 业务逻辑
│   ├── adapters/             # AI 适配器
│   ├── tasks/                # Celery 任务
│   └── utils/                # 工具函数
├── alembic/                   # 数据库迁移
├── scripts/                  # 脚本
├── tests/                   # 测试
└── config/                  # 配置文件
```

## 三、功能模块

### 3.1 认证模块

#### 3.1.1 功能列表

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 账号密码登录 | userid+密码认证，签发 JWT双Token | P0 |
| Token 刷新 | refresh_token 刷新 access_token | P0 |
| 登录安全 | 失败锁定（5次/15分钟），JWT时效控制 | P1 |

#### 3.1.2 JWT双Token机制

**Access Token**：
- 有效期：24小时（可配置）
- 存储：前端内存或 localStorage
- 用途：API请求认证

**Refresh Token**：
- 有效期：7天
- 存储：前端 localStorage + 后端 `refresh_token` 表
- 用途：刷新 access_token
- 包含字段：jti（唯一标识）、user_type、userid

**Token刷新流程**：
1. 前端检测 access_token 即将过期
2. 使用 refresh_token 调用 `/api/v1/auth/refresh`
3. 后端验证 refresh_token 有效性（检查 jti 和 expires_at）
4. 签发新的 access_token
5. 前端更新存储的 access_token

#### 3.1.3 用户表结构（三表分离）

系统采用三表分离设计，通过 `UserBase` 抽象基类确保结构一致：

- **super_admin**：超级管理员表（owner_operator_id = NULL）
- **operator**：创作管理员表（owner_operator_id = NULL）
- **sub_user**：创作者表（owner_operator_id 必填）

**共享字段**（UserBase）：
- `userid`：用户登录ID（自动随机生成，格式：S_xxx / O_xxx / U_xxx）
- `nickname`：管理员备注名（仅管理员可见）
- `display_name`：用户自定义昵称（用户自己可见）
- `hashed_password`：密码哈希（bcrypt，rounds=12）

- `status`：online / offline / disabled
- `login_failure_count` / `locked_until`：登录安全控制
- `owner_operator_id`：所属创作管理员ID（数据隔离）
- `managed_by`：当前管理者ID（支持转移）

#### 3.1.4 API 接口

```
POST /api/v1/auth/login
  Request: { userid, password }
  Response: {
    access_token,
    refresh_token,
    token_type: "bearer",
    expires_in,
    refresh_expires_in,
    user: { id, userid, nickname, role }
  }

POST /api/v1/auth/refresh
  Request: { refresh_token }
  Response: {
    access_token,
    token_type: "bearer",
    expires_in
  }

POST /api/v1/auth/logout
  Headers: Authorization: Bearer {access_token}
  Response: { message: "已登出" }
```

#### 3.1.3 JWT Token 设计

| Token 类型 | 过期时间 | 用途 |
|-----------|---------|------|
| access_token | 30 分钟 | API 访问 |
| refresh_token | 7 天 | 刷新 access_token |

### 3.2 用户管理模块

#### 3.2.1 功能列表

| 功能 | 说明 | 角色 | 优先级 |
|------|------|------|--------|
| 管理员列表 | 超级管理员查看创作管理员 | 超级管理员 | P0 |
| 创建管理员 | 超级管理员创建创作管理员 | 超级管理员 | P0 |
| 编辑管理员 | 更新管理员信息 | 超级管理员 | P0 |
| 删除管理员 | 禁用管理员账号 | 超级管理员 | P0 |
| 创作者列表 | 创作管理员查看创作者 | 创作管理员 | P0 |
| 创建创作者 | 生成邀请码或直接创建 | 创作管理员 | P0 |
| 编辑创作者 | 更新创作者信息 | 创作管理员 | P0 |
| 删除创作者 | 禁用创作者账号 | 创作管理员 | P0 |
| 用户标签 | 用户分类标签管理 | 管理员 | P1 |

#### 3.2.2 API 接口

```
# 超级管理员 - 创作创作管理员
GET    /api/v1/users/admins
POST   /api/v1/users/admins
GET    /api/v1/users/admins/{id}
PUT    /api/v1/users/admins/{id}
DELETE /api/v1/users/admins/{id}

# 创作管理员 - 创作员管理
GET    /api/v1/users/subusers
POST   /api/v1/users/subusers
POST   /api/v1/users/subusers/invite-code  # 生成邀请码
GET    /api/v1/users/subusers/{id}
PUT    /api/v1/users/subusers/{id}
DELETE /api/v1/users/subusers/{id}

# 用户标签
GET    /api/v1/users/tags
POST   /api/v1/users/tags
PUT    /api/v1/users/tags/{id}
DELETE /api/v1/users/tags/{id}
```

### 3.3 模板管理模块

#### 3.3.1 功能列表

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 模板列表 | 分页、筛选、搜索 | P0 |
| 模板详情 | 查看模板完整内容 | P0 |
| 创建模板 | 包含变量定义、平台规则 | P0 |
| 编辑模板 | 修改模板内容 | P0 |
| 删除模板 | 软删除 | P0 |
| 复制模板 | 基于现有模板创建 | P1 |
| 模板分类 | 平台、类型二级分类 | P0 |
| 模板标签 | 自定义标签 | P1 |

#### 3.3.2 模板数据结构

```python
class Template:
    id: int
    name: str                    # 模板名称
    description: str             # 描述
    content_type: str            # text / image_text / video_text
    prompt_template: str         # Prompt 模板（支持变量占位符 {变量名}）
    variables_json: dict         # 变量定义
    style_reference: str         # 风格参考
    platform_rules_json: dict    # 平台适配规则
    default_image_config: dict    # 图片默认配置
    default_video_config: dict   # 视频默认配置
    platform_id: int            # 所属平台
    status: str                  # enabled / disabled
    created_by: int             # 创建者
    owner_admin_id: int         # 所属创作管理员
```

#### 3.3.3 API 接口

```
GET    /api/v1/templates
POST   /api/v1/templates
GET    /api/v1/templates/{id}
PUT    /api/v1/templates/{id}
DELETE /api/v1/templates/{id}
POST   /api/v1/templates/{id}/copy

GET    /api/v1/templates/platforms
POST   /api/v1/templates/platforms
PUT    /api/v1/templates/platforms/{id}
DELETE /api/v1/templates/platforms/{id}

GET    /api/v1/templates/tags
POST   /api/v1/templates/tags
PUT    /api/v1/templates/tags/{id}
DELETE /api/v1/templates/tags/{id}
```

### 3.4 素材管理模块

#### 3.4.1 功能列表

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 素材列表 | 分页、筛选、搜索 | P0 |
| 素材详情 | 查看素材及附件 | P0 |
| 上传素材 | 文本/图片/视频 | P0 |
| 编辑素材 | 修改素材信息 | P0 |
| 删除素材 | 软删除 | P0 |
| 收藏素材 | 收藏/取消收藏 | P1 |
| 素材分类 | 分类管理 | P0 |
| 素材标签 | 标签管理 | P1 |

#### 3.4.2 素材数据结构

```python
class Material:
    id: int
    title: str                  # 素材标题
    text_content: str            # 文本内容
    source_type: str             # upload / link / description
    source_url: str             # 来源链接
    content_type: str           # text / image_text / video_text / mix
    image_count: int            # 图片数量
    video_count: int            # 视频数量
    attachments: List[MaterialAttachment]  # 附件列表
    category_id: int           # 分类
    tags: List[Tag]            # 标签
    is_favorite: bool          # 是否收藏
    created_by: int
    owner_admin_id: int
```

#### 3.4.3 API 接口

```
GET    /api/v1/materials
POST   /api/v1/materials
GET    /api/v1/materials/{id}
PUT    /api/v1/materials/{id}
DELETE /api/v1/materials/{id}
POST   /api/v1/materials/{id}/copy
POST   /api/v1/materials/{id}/favorite
DELETE /api/v1/materials/{id}/favorite

GET    /api/v1/materials/categories
POST   /api/v1/materials/categories
PUT    /api/v1/materials/categories/{id}
DELETE /api/v1/materials/categories/{id}

GET    /api/v1/materials/tags
POST   /api/v1/materials/tags
PUT    /api/v1/materials/tags/{id}
DELETE /api/v1/materials/tags/{id}
```

### 3.5 内容生成模块

#### 3.5.1 功能列表

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 创建生成任务 | 7步骤创建 | P0 |
| 任务列表 | 查看所有任务 | P0 |
| 任务详情 | 包含子任务列表 | P0 |
| 子任务详情 | 单条生成结果 | P0 |
| 暂停任务 | 暂停进行中的任务 | P1 |
| 继续任务 | 继续暂停的任务 | P1 |
| 取消任务 | 取消整个任务 | P1 |
| 重新生成 | 重试失败项 | P0 |
| 实时进度 | WebSocket 推送 | P0 |

#### 3.5.2 任务数据结构

```python
class GenerationTask:
    id: int
    material_id: int            # 素材
    template_ids: List[int]     # 模板列表
    model_selection_mode: str    # auto / manual
    model_platform: str         # 选定平台
    model_id: str               # 选定模型
    max_concurrency: int        # 最大并发数
    variable_values: dict       # 变量值
    dedup_rules: dict          # 去重规则
    subuser_ids: List[int]     # 目标创作者
    image_config: dict         # 图片配置
    video_config: dict         # 视频配置
    status: str                # pending / processing / completed / failed / cancelled
    total_count: int           # 子任务总数
    completed_count: int       # 已完成数
    failed_count: int          # 失败数
    paused_count: int          # 暂停数
    created_by: int
    owner_admin_id: int

class GenerationItem:
    id: int
    task_id: int               # 所属任务
    sub_user_id: int           # 目标创作者
    template_id: int          # 使用模板
    model_platform: str
    model_id: str
    generated_title: str       # 生成标题
    generated_text: str       # 生成正文
    generated_image_urls: List[str]  # 生成图片
    generated_video_url: str  # 生成视频
    status: str               # queued / generating / completed / failed / paused
    retry_count: int          # 重试次数
    error_message: str         # 错误信息
    distribution_status: str  # draft / ready / distributed
```

#### 3.5.3 API 接口

```
POST   /api/v1/generation/tasks
GET    /api/v1/generation/tasks
GET    /api/v1/generation/tasks/{id}
POST   /api/v1/generation/tasks/{id}/cancel
POST   /api/v1/generation/tasks/{id}/pause
POST   /api/v1/generation/tasks/{id}/resume
POST   /api/v1/generation/tasks/{id}/retry

GET    /api/v1/generation/tasks/{id}/items
GET    /api/v1/generation/items/{id}
POST   /api/v1/generation/items/{id}/retry

WS     /api/v1/ws/generation/{task_id}
```

### 3.6 内容分发模块

#### 3.6.1 功能列表

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 批量分发 | 将生成内容分发给创作者 | P0 |
| 分发记录 | 查看分发历史 | P0 |
| 确认发布 | 创作者确认内容已发布 | P0 |
| 分发统计 | 分发状态统计 | P1 |

#### 3.6.2 API 接口

```
POST   /api/v1/distribution
GET    /api/v1/distribution
GET    /api/v1/distribution/my           # 创作者内容
POST   /api/v1/distribution/{id}/confirm
```

### 3.7 系统设置模块

#### 3.7.1 功能列表

| 功能 | 说明 | 角色 |
|------|------|------|
| 个人设置 | 修改昵称、密码 | 所有用户 |
| 模型配置 | 管理 AI 模型 | 超级管理员 |
| 并发配置 | 各平台最大并发 | 超级管理员 |
| 清理规则 | 过期内容清理 | 超级管理员 |

#### 3.7.2 API 接口

```
GET    /api/v1/user/profile
PUT    /api/v1/user/profile
POST   /api/v1/user/change-password
GET    /api/v1/user/wechat-status
POST   /api/v1/user/unbind-wechat

GET    /api/v1/settings/models
POST   /api/v1/settings/models
PUT    /api/v1/settings/models/{id}
DELETE /api/v1/settings/models/{id}
POST   /api/v1/settings/models/{id}/set-default

GET    /api/v1/settings
PUT    /api/v1/settings
```

### 3.8 创意种子库模块

#### 3.8.1 功能列表

| 功能 | 说明 | 角色 | 优先级 |
|------|------|------|--------|
| 种子列表 | 分页、筛选、搜索 | 创作管理员 | P0 |
| 种子详情 | 查看种子完整内容 | 创作管理员 | P0 |
| 创建种子 | 自定义创意种子 | 创作管理员 | P0 |
| 编辑种子 | 更新种子内容 | 创作管理员 | P0 |
| 删除种子 | 删除自定义种子 | 创作管理员 | P0 |
| 系统种子 | 使用预置种子 | 创作管理员 | P0 |
| 种子分组 | 按类型分组查询 | 创作管理员 | P0 |
| 使用统计 | 记录使用次数 | 系统 | P1 |

#### 3.8.2 种子数据结构

```python
class CreativeSeed:
    id: int
    name: str                      # 种子名称
    seed_type: str                 # opening / emotion / ending
    template: str                  # JSON数组格式的模板示例
    description: str               # 使用说明
    forbidden_patterns: str       # JSON数组，禁止使用的模式
    example_phrases: str          # JSON数组，典型表达示例
    avoid_phrases: str            # JSON数组，避免的表达
    category: str                  # 适用品类
    status: str                    # enabled / disabled
    is_system: bool               # 是否系统预置
    owner_operator_id: int        # 所属创作管理员（NULL为系统种子）
    use_count: int                # 使用次数
    success_rate: float           # 成功率
```

#### 3.8.3 API 接口

```
GET    /api/v1/creative-seeds/types          # 获取种子类型枚举
GET    /api/v1/creative-seeds/grouped        # 分组查询（用于下拉选择）
GET    /api/v1/creative-seeds                # 列表查询
GET    /api/v1/creative-seeds/{id}           # 详情
POST   /api/v1/creative-seeds                # 创建
PUT    /api/v1/creative-seeds/{id}           # 更新
DELETE /api/v1/creative-seeds/{id}           # 删除
POST   /api/v1/creative-seeds/{id}/increment-use  # 增加使用次数
```

#### 3.8.4 业务逻辑

**种子组合机制**：
- 每次生成任务从三种类型中各选一个种子组合
- 组合格式：`开头模式 + 情感基调 + 结尾模式`
- 支持指定种子ID或自动随机选择

**差异化保障**：
- 系统预置7种开头、7种情感、6种结尾
- 理论组合数：7 × 7 × 6 = 294 种
- 每次生成使用不同组合，避免内容趋同

**去重重试优化**：
- 去重失败时自动切换种子组合
- 记录已使用种子ID，避免重复
- 最多重试3次，每次使用新组合

---

## 四、AI 模型适配器

### 4.1 支持平台

| 平台 | 标识 | 模型类型 |
|------|------|---------|
| 阿里云百炼 | bailian | LLM, Image, Video |
| 腾讯元宝 | yuanbao | LLM |
| 月之暗面 | moonshot | LLM |
| 智谱AI | zhipu | LLM, Image |
| 字节豆包 | doubao | LLM, Image |
| 即梦 | jimeng | Image, Video |
| 可灵 | kling | Video |

### 4.2 适配器接口

```python
class BaseModelAdapter:
    async def generate_text(
        self,
        prompt: str,
        **kwargs
    ) -> str: ...

    async def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> ImageResult: ...

    async def generate_video(
        self,
        prompt: str,
        **kwargs
    ) -> VideoResult: ...

    def check_rate_limit(self) -> bool: ...
```

## 五、Celery 异步任务

### 5.1 任务队列

| 队列名 | 用途 | 并发数 |
|--------|------|--------|
| generation_queue | 内容生成任务 | 可配置 |
| cleanup_queue | 过期清理任务 | 1 |

### 5.2 重试策略

```python
# 指数退避重试
autoretry_for=(RateLimitError, APIError)
retry_backoff=True
retry_backoff_max=600
retry_kwargs={'max_retries': 3}
```

## 六、数据模型

详见 [数据库设计文档](data-model-analysis.md)

## 七、环境变量

详见 [环境配置指南](env-config-guide.md)

## 八、部署要求

### 8.1 基础环境

- Linux (Ubuntu 20.04+ / CentOS 8+)
- Docker 20.10+
- Docker Compose 2.0+

### 8.2 资源配置

| 服务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| API | 2 核 | 2 GB | 建议 4 核 4 GB |
| Celery Worker | 4 核 | 4 GB | 根据并发需求调整 |
| MySQL | 2 核 | 2 GB | 建议 4 核 8 GB |
| Redis | 1 核 | 1 GB | 建议 2 核 2 GB |

### 8.3 网络要求

- API 服务端口: 8000
- MySQL 端口: 3306
- Redis 端口: 6379
- 前端 Web 端口: 8080
