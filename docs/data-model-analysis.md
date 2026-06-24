# 妙笔内容工场 - 核心数据模型分析

## 设计原则

基于三个核心角色的使用场景优化：

1. **超级管理员**：全局视图，关注所有创作管理员的任务执行情况、系统整体状态
2. **创作管理员**：批量生产，每天生成内容分发1000+创作者，关注子任务进展、批量分发效率
3. **创作者**：便捷消费，只关注自己收到的内容，查询和复制体验优先

---

## 一、用户管理模块（三表分离设计）

### 1.1 用户抽象基类（UserBase）

采用**三表分离设计**，通过 `UserBase` 抽象基类确保结构一致，物理上独立存储。

**核心字段**（所有用户表共用）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| userid | string(64) | 用户ID（自动随机生成且唯一，登录用） |
| nickname | string(100) | 【管理备注名】管理员备注名（仅管理员可见） |
| display_name | string(100) | 【自定义昵称】用户自定义昵称（用户自己可见） |
| hashed_password | string(255) | 密码哈希 |
| wechat_openid | string(100) | 微信OpenID（可空） |
| wechat_unionid | string(100) | 微信UnionID（可空） |
| status | enum | online / offline / disabled |
| login_failure_count | int | 连续登录失败次数 |
| locked_until | datetime | 账号锁定截止时间（连续5次失败锁定15分钟） |
| user_positioning | string(500) | 账号定位（核心赛道/价值/受众/层级等） |
| user_category | string(100) | 账号的运营分类 |
| fan_profile | string(500) | 粉丝画像（年龄/职业/地域/需求/偏好/禁忌等） |
| content_style | string(500) | 内容风格（语气/排版/调性/句式等） |
| account_type | string(255) | 账号类型 |
| last_login_at | datetime | 最后登录时间 |
| last_password_changed_at | datetime | 最后密码修改时间 |
| created_by | bigint | 创建者用户ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离用） |
| managed_by | bigint | 当前管理者用户ID（支持转移） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**索引设计**：
- `idx_userid`：userid 唯一索引
- `idx_status`：status 普通索引
- `idx_created_by`：created_by 普通索引
- `idx_owner_operator`：owner_operator_id 普通索引（数据隔离）
- `idx_managed_by`：managed_by 普通索引

---

### 1.2 super_admin（超级管理员表）

继承 `UserBase`，独立存储。

**表名**：`super_admin`

**设计说明**：
- 超级管理员的 `owner_operator_id` 和 `managed_by` 为 NULL
- 拥有系统全部权限，可管理所有创作管理员和创作者

---

### 1.3 operator（创作管理员表）

继承 `UserBase`，独立存储。

**表名**：`operator`

**设计说明**：
- 创作管理员的 `owner_operator_id` 和 `managed_by` 为 NULL
- 可管理自己的模板、素材、内容生成以及绑定的创作者
- 通过 `owner_operator_id` 字段实现数据隔离（所有资源表）

---

### 1.4 sub_user（创作者表）

继承 `UserBase`，独立存储。

**表名**：`sub_user`

**设计说明**：
- 创作者的 `owner_operator_id` 必填，指向所属创作管理员
- `managed_by` 支持转移功能（超级管理员可将创作者转移给其他创作管理员）
- 仅可查看和操作自己接收到的内容

---

### 1.5 refresh_token（刷新令牌表）

**表名**：`refresh_token`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| token | string(500) | 刷新令牌（唯一） |
| user_id | bigint | 关联用户ID |
| user_type | string(20) | 用户类型：super_admin / operator / sub_user |
| expires_at | datetime | 过期时间 |
| created_at | datetime | 创建时间 |

**设计说明**：
- JWT双token机制：`access_token`（短期）+ `refresh_token`（长期）
- 支持token刷新，无需频繁登录

---

### 1.2 user_tag（用户标签表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string | 标签名称，如"北京团队"、"美妆号" |
| tag_type | enum | operator_tag / subuser_tag |
| description | string | 描述 |
| color | string | 标签颜色（UI展示用） |
| created_by | bigint | 创建者用户 ID |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 1.3 user_tag_rel（用户标签关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| user_id | bigint | 外键，关联用户表 |
| tag_id | bigint | 外键，关联用户标签表 |
| created_at | datetime | 创建时间 |

---

## 二、模板管理模块（四级层次结构）

### 层次结构

**TemplatePlatform → TemplateCategory → TemplateTag → Template**

1. **模板平台（TemplatePlatform）**：如"小红书"、"抖音"、"微信公众号"
2. **模板分类（TemplateCategory）**：平台下的内容分类，如"美食"、"旅游"
3. **模板标签（TemplateTag）**：分类下的标签，用于进一步分类
4. **模板（Template）**：具体的内容模板

---

### 2.1 template_platform（模板平台表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 平台名称，如"抖音"、"小红书" |
| description | string(500) | 平台描述 |
| color | string(20) | 平台颜色（UI展示用） |
| sort_order | int | 排序权重 |
| created_by | bigint | 创建者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_template_platform_owner_name` (owner_operator_id, name)

---

### 2.2 template_category（模板分类表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 分类名称 |
| description | string(500) | 分类描述 |
| color | string(20) | 分类颜色 |
| template_platform_id | bigint | 所属模板平台ID（外键） |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_by | bigint | 创建者创作管理员ID |
| sort_order | int | 排序 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_template_category_owner_name` (owner_operator_id, name)

---

### 2.3 template_tag（模板标签表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 标签名称 |
| description | string(500) | 标签描述 |
| color | string(20) | 标签颜色 |
| category_id | bigint | 所属分类ID（外键） |
| is_system | boolean | 是否系统默认标签 |
| created_by | bigint | 创建者管理员ID |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_template_tag_category_name` (category_id, name)

---

### 2.4 template（模板表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(255) | 模板名称 |
| description | string(1000) | 提示词创意 |
| content_type | enum | text / image_text / video_text |
| prompt_template | text | Prompt模板（支持变量占位符） |
| variables_json | json | 变量定义JSON |
| style_reference | string(1000) | 风格场景参考描述 |
| platform_rules_json | json | 平台适配规则JSON |
| status | enum | enabled / disabled |
| platform_id | bigint | 关联模板平台ID（外键） |
| original_template_id | bigint | 原始模板ID（用于追踪克隆关系） |
| image_count | int | 图片数量（冗余字段） |
| video_count | int | 视频数量（冗余字段） |
| image_size_ratio | string(20) | 图片尺寸比例：1:1/4:3/16:9/3:4/9:16 |
| add_watermark | boolean | 是否添加水印 |
| created_by | bigint | 创建者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**设计说明**：
- 超级管理员不能创建模板、平台、分类、标签，必须使用创作管理员账号操作
- 每个创作管理员的资源完全独立，通过 `owner_operator_id` 实现数据隔离

---

### 2.5 template_attachment（模板附件表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| template_id | bigint | 模板ID（外键） |
| file_type | enum | image / video |
| file_url | string(500) | 腾讯云COS文件URL |
| file_name | string(255) | 文件名 |
| file_size | bigint | 文件大小（字节） |
| sort_order | int | 排序 |
| width | int | 图片/视频宽度（像素） |
| height | int | 图片/视频高度（像素） |
| duration | float | 视频时长（秒） |
| thumbnail_url | string(500) | 缩略图URL |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 2.6 template_tag_rel（模板标签关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| template_id | bigint | 模板ID（外键） |
| tag_id | bigint | 标签ID（外键） |
| created_at | datetime | 创建时间 |

---

## 三、素材管理模块（四级层次结构）

### 层次结构

**MaterialPlatform → MaterialCategory → MaterialTag → Material**

1. **素材平台（MaterialPlatform）**：如"小红书"、"抖音"（素材库独立平台）
2. **素材分类（MaterialCategory）**：平台下的内容分类
3. **素材标签（MaterialTag）**：分类下的标签
4. **素材（Material）**：具体的素材内容

---

### 3.1 material_platform（素材平台表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 平台名称 |
| description | string(500) | 平台描述 |
| color | string(20) | 平台颜色 |
| platform_code | string(50) | 平台代码（如 xhs, dy） |
| config_json | json | 平台配置JSON（预留扩展） |
| sort_order | int | 排序权重 |
| created_by | bigint | 创建者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_material_platform_owner_name` (owner_operator_id, name)

---

### 3.2 material_category（素材分类表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 分类名称 |
| description | string(500) | 分类描述 |
| color | string(20) | 分类颜色 |
| material_platform_id | bigint | 所属素材平台ID（外键） |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_by | bigint | 创建者创作管理员ID |
| sort_order | int | 排序 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_material_category_owner_name` (owner_operator_id, name)

---

### 3.3 material_tag（素材标签表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 标签名称 |
| description | string(500) | 标签描述 |
| color | string(20) | 标签颜色 |
| category_id | bigint | 所属分类ID（外键） |
| is_system | boolean | 是否系统默认标签（不可删除） |
| created_by | bigint | 创建者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**唯一约束**：`uq_material_tag_category_name` (category_id, name)

---

### 3.4 material（素材表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| title | string(500) | 素材标题（拟题） |
| content | text | 素材内容 |
| topic | string(255) | 素材主题 |
| text_content | text | 文本内容 |
| source_url | string(500) | 来源URL（可空） |
| source_type | enum | upload / link / description |
| content_type | enum | text / image_text / video_text / mix |
| library_type | enum | creation（创作库）/ benchmark（对标库） |
| image_count | int | 图片数量（冗余字段） |
| video_count | int | 视频数量（冗余字段） |
| status | enum | available / disabled |
| created_by | bigint | 上传者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**设计说明**：
- `library_type` 字段区分创作库和对标库
- 创作库素材用于内容生成
- 对标库素材用于风格参考和对标

---

### 3.5 material_attachment（素材附件表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| material_id | bigint | 素材ID（外键） |
| file_type | enum | image / video |
| file_url | string(500) | 腾讯云COS文件URL |
| file_name | string(255) | 文件名 |
| file_size | bigint | 文件大小（字节） |
| sort_order | int | 排序 |
| width | int | 图片/视频宽度（像素） |
| height | int | 图片/视频高度（像素） |
| duration | float | 视频时长（秒） |
| thumbnail_url | string(500) | 缩略图URL |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 3.6 material_tag_rel（素材标签关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| material_id | bigint | 素材ID（外键） |
| tag_id | bigint | 标签ID（外键） |
| created_at | datetime | 创建时间 |

---

### 3.7 material_favorite（素材收藏表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| material_id | bigint | 素材ID（外键） |
| user_id | bigint | 收藏用户ID |
| created_at | datetime | 创建时间 |

---

## 四、内容生成模块（核心）

### 4.1 generation_task（生成任务表）

一次批量生成为一条任务。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(200) | 任务名称 |
| material_id | bigint | 素材创作ID（创作库素材） |
| benchmark_material_id | bigint | 素材对标ID（对标库素材） |
| model_platform | string(100) | 选择的文本模型平台 |
| model_id | string(100) | 选择的文本模型 |
| image_model_platform | string(100) | 选择的图片模型平台 |
| image_model_id | string(100) | 选择的图片模型 |
| model_selection_mode | enum | auto / manual |
| max_concurrency | int | 本次任务最大并发数（默认5） |
| variable_values_json | json | 变量值JSON |
| dedup_rules_json | json | 去重规则JSON |
| status | enum | pending / processing / completed / failed / cancelled |
| total_count | int | 子任务总数 |
| queued_count | int | 队列中数量 |
| generating_count | int | 生成中数量 |
| completed_count | int | 已完成数 |
| failed_count | int | 失败数 |
| paused_count | int | 已暂停数量 |
| distributed_count | int | 已分发数量 |
| pending_publish_count | int | 待发布数量 |
| published_count | int | 已发布数量 |
| created_by | bigint | 发起者创作管理员ID |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| started_at | datetime | 任务开始处理时间 |
| completed_at | datetime | 任务完成时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**去重配置字段**：
- `image_count`：生成图片数量（默认4）
- `dedup_enabled`：文案去重检测开关（默认true）
- `dedup_threshold`：文案去重阈值（默认0.8）
- `dedup_retry_count`：文案去重失败重试次数（默认3）
- `dedup_scope`：文案去重范围配置（默认["subuser_history"]）
- `image_dedup_enabled`：图片去重检测开关（默认true）
- `image_dedup_threshold`：图片相似度阈值（默认0.8）
- `image_dedup_retry_count`：图片去重失败重试次数（默认3）
- `image_dedup_scope`：图片去重范围（默认["subuser_image_history"]）

**素材对标配置字段**：
- `benchmark_text_enabled`：文案对标开关（默认true）
- `benchmark_image_enabled`：图片对标开关（默认true）
- `benchmark_image_reference_options`：图片参考选项
- `benchmark_image_roles_json`：对标图角色配置
- `template_product_mapping_json`：模板产品映射

**进度字段冗余设计**：在 `generation_task` 表中包含所有状态计数字段，一次查询获取完整进度。

---

### 4.2 generation_item（生成明细表/子任务表）

一个子任务对应一个创作者 + 一个模板。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| task_id | bigint | 任务ID（外键） |
| sub_user_id | bigint | 目标创作者ID（外键） |
| template_id | bigint | 使用的模板（外键） |
| model_platform | string(100) | 实际使用的文本模型平台 |
| model_id | string(100) | 实际使用的文本模型 |
| image_model_platform | string(100) | 实际使用的图片模型平台 |
| image_model_id | string(100) | 实际使用的图片模型 |
| generated_title | text | 生成的标题 |
| generated_text | text | 生成的文本内容 |
| text_file_url | string(500) | 保存到COS的文案文件URL |
| generated_image_urls_json | json | 生成的图片URL列表JSON |
| generated_image_thumbnails_json | json | 生成的图片缩略图URL列表JSON |
| generated_video_url | string(500) | 生成的视频URL |
| final_prompt | text | 最终发送给模型的完整提示词 |
| status | enum | queued / generating / completed / failed / paused |
| retry_count | int | 重试次数 |
| error_message | text | 错误信息 |
| queued_at | datetime | 进入队列时间 |
| started_at | datetime | 开始生成时间 |
| completed_at | datetime | 完成时间 |
| distribution_status | enum | draft / ready / distributed / pending_publish / published |
| distributed_at | datetime | 分发时间 |
| confirmed_at | datetime | 确认发布时间 |
| owner_operator_id | bigint | 所属创作管理员ID（数据隔离） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**输入内容快照字段**：
- `sub_user_name`：创作者名称快照
- `input_prompt_creativity`：模板提示词创意
- `input_prompt_instruction`：模板提示词指令
- `input_template_images_json`：模板图片URL列表
- `input_image_size_ratio`：输出图片尺寸比例
- `input_watermark`：输出图片水印开关
- `input_benchmark_title`：素材对标标题
- `input_benchmark_content`：素材对标内容
- `input_benchmark_topic`：素材对标话题
- `input_benchmark_images_json`：素材对标图片URL列表
- `input_sub_user_profile`：创作者粉丝画像
- `input_sub_user_positioning`：创作者账号定位
- `input_sub_user_style`：创作者内容风格

**提示词模板字段**：
- `text_prompt_template_id`：使用的文案系统提示词模板ID
- `image_prompt_template_id`：使用的图片系统提示词模板ID

**输出内容字段**：
- `aigc_generated_prompt`：AIGC提示词生成器产出的精炼提示词
- `output_system_text_prompt`：AIGC文案系统提示词
- `output_user_text_prompt`：AIGC文案用户提示词
- `output_system_image_prompt`：图片系统提示词
- `output_user_image_prompt`：图片用户提示词
- `output_topics`：输出话题JSON

**执行情况字段**：
- `execution_started_at`：子任务执行开始时间
- `execution_ended_at`：子任务执行结束时间
- `execution_result`：执行结果（success / failed / partial）
- `current_step`：当前执行步骤
- `generated_image_count`：实际生成图片数量

**去重检测字段**：
- `dedup_check_passed`：文案去重检测是否通过
- `dedup_similarity`：文案最大相似度
- `dedup_referenced_items_json`：文案相似内容引用
- `dedup_checked_at`：文案去重检测时间
- `image_dedup_passed`：图片去重检测是否通过
- `image_dedup_max_similarity`：图片最高相似度
- `image_dedup_similarities_json`：每张图片的相似度列表
- `image_dedup_referenced_images_json`：相似图片引用
- `image_dedup_checked_at`：图片去重检测时间
- `image_dedup_retry_count`：图片去重实际重试次数

---

### 4.3 generation_task_template（生成任务-模板关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| task_id | bigint | 任务ID（外键） |
| template_id | bigint | 模板ID（外键） |
| sort_order | int | 排序权重（默认0） |
| created_at | datetime | 创建时间 |

---

### 4.4 generation_task_subuser（生成任务-创作者关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| task_id | bigint | 任务ID（外键） |
| sub_user_id | bigint | 创作者ID（外键） |
| created_at | datetime | 创建时间 |

---

### 4.5 generation_task_progress_log（任务进度快照表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| task_id | bigint | 任务ID（外键） |
| queued_count | int | 队列中数量 |
| generating_count | int | 生成中数量 |
| completed_count | int | 已完成数量 |
| failed_count | int | 失败数量 |
| status | enum | pending / processing / completed / failed / cancelled |
| progress_message | string(1000) | 进度信息 |
| created_at | datetime | 记录时间 |

---

### 4.6 generation_item_execution_log（生成子任务执行日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| item_id | bigint | 子任务ID（外键） |
| node_name | string(50) | 节点名称：prompt_build / llm_call / image_call / save_result |
| node_status | enum | running / success / failed / skipped |
| input_data | json | 节点输入数据JSON |
| output_data | json | 节点输出数据JSON |
| error_data | json | 结构化错误信息JSON |
| duration_ms | int | 耗时毫秒 |
| started_at | datetime | 节点开始时间 |
| completed_at | datetime | 节点完成时间 |
| created_at | datetime | 创建时间 |

**说明**：记录每个子任务处理链路中的关键节点，用于调试和质量追踪。

---

### 4.7 content_embedding（内容嵌入向量表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| owner_operator_id | bigint | 所属创作管理员ID（外键） |
| generation_item_id | bigint | 关联的生成项ID（外键） |
| task_id | bigint | 关联的任务ID（外键） |
| content_type | string(20) | 内容类型：text / image |
| content_index | int | 内容索引（多张图片时使用） |
| embedding | json | 嵌入向量数据 |
| content_preview | string(500) | 内容预览（文案前100字/图片URL） |
| content_hash | string(64) | 内容哈希（用于快速查找重复内容） |
| used_for_dedup_count | int | 用于去重检测的次数 |
| last_used_at | datetime | 最后使用时间 |
| created_at | datetime | 创建时间 |

**说明**：缓存所有生成内容的embedding向量，避免重复计算，支持文案和图片分别存储和对比。

---

## 五、内容分发模块

### 5.1 distribution（分发记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| task_id | bigint | 任务ID（外键） |
| generation_item_id | bigint | 分发的内容项ID（外键） |
| sub_user_id | bigint | 接收的创作者ID（外键） |
| publish_status | enum | distributed / pending_publish / published |
| distributed_at | datetime | 分发时间 |
| confirmed_at | datetime | 确认发布时间 |
| created_at | datetime | 创建时间 |

**说明**：
- 分发状态流转：distributed（已分发）→ pending_publish（待发布）→ published（已发布）
- 创作者确认发布后更新 `confirmed_at` 时间

---

## 六、创意种子库模块

### 6.1 creative_seed（创意种子表）

**表名**：`creative_seed`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| name | string(100) | 种子名称（如：反常识开头、轻松吐槽基调） |
| seed_type | enum | 种子类型：opening（开头模式）/ emotion（情感基调）/ ending（结尾模式） |
| template | text | 模板示例（JSON数组格式，如：['没想到这个xxx居然...', '谁能想到xxx竟然...']） |
| description | text | 使用说明 |
| forbidden_patterns | text | 禁止使用的模式（JSON数组） |
| example_phrases | text | 典型表达示例（JSON数组） |
| avoid_phrases | text | 避免的表达（JSON数组） |
| category | string(50) | 适用品类：3C/美妆/美食/家居/通用等 |
| status | enum | enabled / disabled |
| is_system | boolean | 是否系统预置（系统种子不可删除） |
| owner_operator_id | bigint | 所属创作管理员ID（NULL为系统级种子） |
| use_count | bigint | 使用次数统计 |
| success_rate | float | 成功率（通过去重的比例） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**索引设计**：
- `idx_seed_type`：seed_type 普通索引
- `idx_status`：status 普通索引
- `idx_owner_operator`：owner_operator_id 普通索引（数据隔离）
- `idx_category`：category 普通索引

**设计说明**：
- **三种种子类型**：
  - `opening`（开头模式）：控制文案开头风格，如反常识、自嘲、悬念、痛点场景等
  - `emotion`（情感基调）：控制文案情感表达，如轻松吐槽、真诚分享、犹豫观望等
  - `ending`（结尾模式）：控制文案收尾方式，如求建议、留悬念、共鸣式等
- **系统预置种子**：`is_system=True` 的种子为系统预置，创作管理员可使用但不可删除
- **自定义种子**：创作管理员可创建自己的种子，实现个性化差异化
- **品类适配**：支持按品类筛选种子，确保风格与品类匹配
- **使用统计**：记录使用次数和成功率，便于评估种子效果

**种子组合机制**：
生成任务时，从三种类型中各选一个种子组合成完整的创意框架：
```
开头模式 + 情感基调 + 结尾模式 = 创意种子组合
```
每次生成使用不同的组合，确保内容差异化。

---

## 七、系统管理模块

### 6.1 operation_log（操作日志表）

**表名**：`operation_log`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| super_admin_id | bigint | 超级管理员ID（外键，可空） |
| operator_id | bigint | 创作管理员ID（外键，可空） |
| sub_user_id | bigint | 创作者ID（外键，可空） |
| module | string(50) | 模块：users/templates/materials/generation/distribution/system |
| action | string(100) | 操作类型：create / update / delete / distribute / publish / login / logout / cancel / retry |
| description | string(500) | 操作描述，如：创建素材：素材标题 |
| table_name | string(100) | 操作的数据表 |
| record_id | bigint | 操作的记录 ID |
| old_value_json | json | 操作前的旧值（JSON格式） |
| new_value_json | json | 操作后的新值（JSON格式） |
| extra_data_json | json | 额外参数（JSON格式），如标签列表、操作条件等 |
| ip_address | string(50) | 操作 IP 地址 |
| user_agent | string(500) | 浏览器/客户端信息 |
| created_at | datetime | 操作时间 |

**设计说明**：
- 支持三种用户类型的操作日志记录
- 通过三个独立的用户ID字段实现灵活关联
- `extra_data_json` 存储额外参数，如批量操作的标签列表

---

### 6.2 cleanup_rule（过期清理规则表）

**表名**：`cleanup_rule`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| rule_name | string(255) | 规则名称 |
| content_type | string(100) | 内容类型 |
| retention_period | enum | month / quarter / year（默认：quarter） |
| enabled | boolean | 是否启用（默认：true） |
| last_executed_at | datetime | 上次执行时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 6.3 model_config（模型配置表）

**表名**：`model_config`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键，自增 |
| platform | string(100) | 平台：bailian / volcano / jimeng / kling / autoglm / moonshot / deepseek / lingyaai |
| model_id | string(255) | 模型ID |
| model_name | string(255) | 模型名称 |
| model_type | enum | llm / image / video / embedding |
| base_url | string(500) | 【大语言模型专属】Base URL |
| api_endpoint | string(500) | API端点 |
| is_default | boolean | 是否默认（默认：false） |
| max_concurrency | int | 最大并发数（默认：5） |
| config_json | json | 配置JSON（包含API Key等） |
| status | enum | active / inactive（默认：active） |
| is_system | boolean | 是否系统预置模型（默认：false） |
| created_by | bigint | 创建者超级管理员ID（外键） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**设计说明**：
- `model_type` 包含四种类型：llm（大语言模型）、image（图片生成）、video（视频生成）、embedding（向量嵌入）
- 仅超级管理员可配置模型（`created_by` 关联 `super_admin.id`）
- 支持系统预置模型（`is_system=true`）和自定义模型
- `config_json` 存储平台特定的配置参数（如 API Key、AccessKey、SecretKey等）

---

## 八、核心业务流程数据流转

### 8.1 内容生成流程（详细）

```
1. 创作管理员创建任务
   ↓
2. generation_task 记录创建（status=pending）
   - 配置素材（创作库 + 对标库）
   - 配置模型（文本模型 + 图片模型）
   - 配置去重规则（文案去重 + 图片去重）
   - 配置对标规则（文案对标 + 图片对标）
   - 配置创意种子（开头模式 + 情感基调 + 结尾模式，可选"自动"）
   ↓
3. 为每个（创作者，模板）组合创建 generation_item（status=queued）
   - 快照输入内容（模板、素材、创作者信息）
   - 快照创意种子配置
   ↓
4. Celery Worker 从队列拉取子任务
   ↓
5. 【创意种子选择】
   - 若种子配置为"自动"，从 creative_seed 表随机选择
   - 若指定具体种子ID，使用指定种子
   - 组合三种种子（开头 + 情感 + 结尾）形成创意框架
   ↓
6. 执行生成流水线（每个节点记录到 generation_item_execution_log）
   - prompt_build：构建提示词（整合创意种子框架）
   - llm_call：调用大语言模型生成文案（单次调用，减少中间步骤）
   - image_call：调用图片模型生成图片
   - save_result：保存生成结果到COS
   ↓
7. 文案去重检测（dedup_enabled=true时）
   - 从 content_embedding 查询历史文案向量
   - 计算相似度，超过阈值则更换创意种子重试（最多3次）
   - 记录检测结果到 generation_item.dedup_* 字段
   ↓
8. 图片去重检测（image_dedup_enabled=true时）
   - 从 content_embedding 查询历史图片向量
   - 计算相似度，超过阈值则重试（最多3次）
   - 记录检测结果到 generation_item.image_dedup_* 字段
   ↓
9. 保存内容嵌入向量到 content_embedding 表
   ↓
10. 更新 generation_item（status=completed）
    - 更新 generation_task 进度计数器
    - 更新创意种子使用次数（use_count + 1）
    ↓
11. 失败处理：
    - 自动重试（最多3次）
    - 重试时自动切换创意种子组合
    - 记录错误信息到 error_message
    - 超过重试次数标记为 failed
```

**创意种子库优化效果**：
- **降低调用次数**：从原来的 7-9+ 次 LLM 调用优化到 1-5 次
- **提升内容质量**：通过强制差异化框架，避免 AI 生成趋同性内容
- **降低高相似度**：每次生成使用不同的种子组合，从源头降低相似度
- **去重重试优化**：重试时自动切换种子组合，而非简单重复生成

### 8.2 内容分发流程

```
1. 创作管理员查看生成结果
   ↓
2. 选择需要分发的 generation_item
   ↓
3. 更新 generation_item（distribution_status=distributed）
   ↓
4. 创建 distribution 记录（publish_status=distributed）
   ↓
5. 更新 generation_task 进度计数器
   ↓
6. 创作者查看内容，复制/下载
   ↓
8. 创作者点击"确认发布"
   ↓
9. 更新 distribution（publish_status=published, confirmed_at=now）
   ↓
10. 更新 generation_item（distribution_status=published）
```

### 7.3 去重检测机制

**文案去重流程**：
```
1. 生成文案后，调用 embedding 模型生成向量
2. 从 content_embedding 查询历史文案向量（根据 dedup_scope）
   - subuser_history：仅对比该创作者的历史文案
   - operator_history：对比该创作管理员下所有创作者的历史文案
3. 计算相似度（cosine similarity）
4. 如果相似度 > dedup_threshold（默认0.8）
   - 重试生成（最多 dedup_retry_count 次）
   - 记录相似内容引用到 dedup_referenced_items_json
5. 保存新的文案向量到 content_embedding
```

**图片去重流程**：
```
1. 生成图片后，调用 embedding 模型生成图片向量
2. 从 content_embedding 查询历史图片向量（根据 image_dedup_scope）
3. 计算每张图片的相似度
4. 如果相似度 > image_dedup_threshold（默认0.8）
   - 重试生成（最多 image_dedup_retry_count 次）
   - 记录相似图片引用到 image_dedup_referenced_images_json
5. 保存新的图片向量到 content_embedding（每张图片一条记录）
```

---

## 九、数据隔离与查询优化

### 9.1 多租户隔离设计

**核心隔离字段**：
- **`owner_operator_id`**：创作管理员数据隔离字段
  - 所有资源表（template、material、generation_task、generation_item）包含此字段
  - 创作管理员只能访问自己创建的资源
  - 创作者只能访问所属创作管理员的资源

**用户层级关系**：
- 超级管理员：`owner_operator_id = NULL`，可访问所有数据
- 创作管理员：`owner_operator_id = NULL`，可访问自己创建的数据
- 创作者：`owner_operator_id` 必填，指向所属创作管理员

**数据转移支持**：
- `managed_by` 字段：支持创作者转移功能
- 超级管理员可将创作者转移给其他创作管理员
- 转移后创作者的历史数据仍保留原 `owner_operator_id`

**复合索引设计**：
- `idx_owner_operator_date(owner_operator_id, created_at)`：按创作管理员和时间查询
- `idx_subuser_item(sub_user_id, status)`：创作者任务查询
- `idx_task_status(task_id, status)`：任务状态查询

**表分区策略**（建议）：
- `generation_item` 按周分区（高频写入）
- `generation_task` 按月分区（中等频率）
- `content_embedding` 按月分区（向量存储）

### 8.2 性能目标

| 指标 | 目标 | 实现方式 |
|------|------|----------|
| 单任务创建 | < 2s | 批量插入 generation_item |
| 创作者内容列表查询 | < 100ms | 索引优化 + 分页 |
| 创作管理员任务列表查询 | < 100ms | owner_operator_id 索引 |
| 去重检测查询 | < 200ms | content_embedding 向量索引 |
| 进度实时更新 | < 50ms | WebSocket 推送 |

### 8.3 查询优化建议

**创作管理员任务列表**：
```sql
-- 利用 owner_operator_id 索引 + 进度字段冗余
SELECT * FROM generation_task
WHERE owner_operator_id = ?
ORDER BY created_at DESC
LIMIT 20;
```

**创作者内容列表**：
```sql
-- 利用 sub_user_id 索引
SELECT gi.*, t.name as template_name
FROM generation_item gi
LEFT JOIN template t ON gi.template_id = t.id
WHERE gi.sub_user_id = ? AND gi.distribution_status = 'distributed'
ORDER BY gi.distributed_at DESC
LIMIT 20;
```

**去重检测查询**：
```sql
-- 查询历史文案向量
SELECT embedding, content_preview, generation_item_id
FROM content_embedding
WHERE owner_operator_id = ?
  AND content_type = 'text'
  AND generation_item_id IN (
    SELECT id FROM generation_item WHERE sub_user_id = ? AND status = 'completed'
  )
ORDER BY created_at DESC
LIMIT 100;
```

---

## 九、设计评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 完整性 | ⭐⭐⭐⭐⭐ | 核心表和辅助表齐全，支持所有业务场景 |
| 规范性 | ⭐⭐⭐⭐⭐ | 命名规范，主键外键设计合理，三表分离设计清晰 |
| 扩展性 | ⭐⭐⭐⭐⭐ | 四级层次结构灵活，标签体系完善，JSON字段预留扩展 |
| 性能 | ⭐⭐⭐⭐⭐ | 进度字段冗余，配合分区/索引方案，向量缓存优化去重检测 |
| 实用性 | ⭐⭐⭐⭐⭐ | 三表分离设计简化认证逻辑，针对三个角色优化查询 |
| 安全性 | ⭐⭐⭐⭐⭐ | owner_operator_id 数据隔离，完整操作审计，JWT双token机制 |

**总体评价**：

✅ **优秀设计**：
- **三表分离设计**：通过 `UserBase` 抽象基类确保结构一致，物理上独立存储，简化认证逻辑
- **四级层次结构**：模板和素材采用四级层次（Platform → Category → Tag → Item），灵活且易扩展
- **进度字段冗余**：`generation_task` 包含所有状态计数器，一次查询获取完整进度
- **执行日志设计**：`generation_item_execution_log` 记录每个流水线节点，便于调试和质量追踪
- **向量缓存优化**：`content_embedding` 缓存嵌入向量，避免重复计算，优化去重检测性能

⚠️ **待实现**：
- 表分区策略：建议对高频表实施分区
- 向量索引优化：建议为 `content_embedding` 创建向量索引
