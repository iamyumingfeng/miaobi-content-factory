# 妙笔内容工场 · 新人上手指南（Onboarding Guide）

> 本指南由项目知识图谱（`.ua/knowledge-graph.json`，提交 `9bf7049`）自动生成，面向新加入团队的开发者。
> 图谱规模：404 节点 / 104 依赖边 / 14 架构分层 / 8 步导览。

---

## 一、项目概览（Project Overview）

| 项 | 内容 |
|---|---|
| 项目名称 | 妙笔内容工场（miaobi-content-factory） |
| 定位 | AI 内容生成 SaaS 平台，服务自媒体运营者与内容创作者，提供素材管理、AI 内容生成与批量分发 |
| 后端语言 | Python 3.11+（FastAPI / SQLAlchemy / Celery） |
| 前端语言 | TypeScript / Vue 3（Element Plus / Pinia / Vite） |
| 其他 | Shell 脚本、YAML（CI/部署）、MySQL 8.0、Redis、腾讯云 COS |
| 当前分支 | master（提交 9bf7049） |

**一句话理解**：管理员选素材 + 模板 + 模型，提交一个生成任务 → 系统按"创作者"拆成多个子任务 → Celery Worker 调用 AI 平台逐条生成 → 结果分发到各创作者 → 创作者复制/下载并确认发布。

---

## 二、架构分层（Architecture Layers）

知识图谱将 404 个节点归入 14 层，核心分层如下：

| 分层 | 节点数 | 职责 |
|---|---|---|
| 后端 - API 路由层 | 17 | `/api/v1` 下各业务域路由（认证、用户、模板、素材、生成、分发、系统设置等） |
| 后端 - 数据模型层 | 33 | SQLAlchemy ORM 模型 + Pydantic 校验模型（统一用户、模板、素材、任务、分发等核心表） |
| 后端 - 服务/核心层 | 32 | 业务服务（三阶段事务、模型适配器、去重、Embedding 保存）与核心基础设施（配置、安全、DB 会话） |
| 后端 - 异步任务层 | 6 | Celery Worker、定时任务，消费 Redis 队列处理生成子任务 |
| 后端 - 基础设施 | 143 | 配置、依赖、迁移、工具等非路由/服务类后端文件 |
| 前端 - 视图/组件层 | 40 | 页面视图与可复用组件（登录、仪表盘、模板库、素材库、内容生成等） |
| 前端 - API 客户端层 | 2 | 统一 API 客户端封装（axios + 类型定义） |
| 前端 - 状态管理层 | 2 | Pinia Store（按功能模块划分） |
| 前端 - 基础设施 | 55 | 路由、样式、工具、构建配置等 |
| 文档层 | 15 | PRD、API 设计、数据模型、UI 设计等 |
| 部署/运维层 | 24 | Docker、CI 脚本、Serverless Functions |
| 测试层 | 7 | 后端/前端测试 |
| 核心架构概念 | 4 | 三阶段事务、AI 模型适配器、Celery 异步、RBAC 多租户 |
| 其他/根目录 | 24 | README、LICENSE、package.json 等根级文件 |

---

## 三、关键概念（Key Concepts）

图谱识别出 4 个必须理解的核心架构概念：

1. **三阶段事务架构（Three-Phase Transaction）** — 复杂度高，重点掌握
   AI 生成流程被拆为三个独立阶段，各用独立 DB session：
   - 阶段1 读取数据（<1s）→ 立即关闭连接
   - 阶段2 AI 生成（30-90s，**无数据库连接**，纯计算）
   - 阶段3 保存结果（<1s）→ 立即关闭连接
   效果：连接持有时间从 ~100s 降到 <2s，彻底解决连接池耗尽与锁等待超时。

2. **AI 模型适配器（AI Model Adapter）** — 复杂度高，重点掌握
   采用策略模式，抽象基类 `BaseModelAdapter`，支持阿里百炼、火山引擎、即梦、可灵、DeepSeek 等多平台。新增平台需实现适配器接口，配置仅超级管理员可改。

3. **Celery 异步任务流（Celery Async）** — 复杂度高，重点掌握
   一条生成任务 → 按"创作者"拆为多个 `generation_item` 子任务 → 经 Redis 队列由 Worker 处理 → WebSocket 实时推送进度。支持失败重试（3 次失败转失败列表）、并发限流、自动模型切换。

4. **RBAC 与多租户隔离（RBAC）** — 复杂度高，重点掌握
   三角色：超级管理员 / 运营管理员 / 子用户。所有核心表含 `owner_admin_id` 字段实现数据隔离；登录连续 5 次失败锁定 15 分钟。

---

## 四、导览路线（Guided Tour）

按以下 8 步顺序阅读代码，逐步建立全局认知：

1. **项目入口与总览** — `README.md`、`package.json`：了解定位、技术栈与本地启动方式。
2. **后端应用入口** — `platform_api/app/main.py`：FastAPI 实例、路由挂载、CORS、WebSocket、生命周期钩子（连接池/Redis 启停）。
3. **API 路由层** — `platform_api/app/api/v1/`：版本化路由，按业务域拆分模块。
4. **数据模型层** — `platform_api/app/models/`：核心 ORM 表定义（`all_user`、`template`、`material`、`generation_task`、`generation_item`、`distribution`、`model_config`）。
5. **服务与核心层** — `platform_api/app/services/generation_phases.py`：三阶段事务核心实现，务必精读。
6. **异步任务层** — `platform_api/app/api/v1/scheduled_tasks.py` 及 Celery 配置：子任务调度与执行。
7. **前端应用结构** — `platform_web/src/main.ts`、`platform_web/src/api/`：Vue 应用入口、统一 API 客户端、Pinia Store、视图组件。
8. **文档与部署** — `docs/api-design.md`、`docker/`：接口契约与容器/CI 部署能力。

---

## 五、文件地图（File Map）

### 后端 `platform_api/`
| 路径 | 作用 |
|---|---|
| `app/main.py` | FastAPI 应用入口：路由挂载、CORS、WebSocket、生命周期钩子 |
| `app/api/v1/auth.py` | 认证路由：登录、登出、修改密码、个人设置 |
| `app/api/v1/generation.py` | 内容生成任务路由：创建任务、任务列表、任务详情 |
| `app/api/v1/materials.py` | 素材库路由：素材增删改查、分类、附件 |
| `app/api/v1/templates.py` | 模板库路由：模板管理、复制、禁用 |
| `app/api/v1/distribution.py` | 分发路由：分发记录与发布状态管理 |
| `app/api/v1/dashboard.py` | 仪表盘路由：统计卡片、趋势、最近任务 |
| `app/api/v1/trend_analysis.py` | 趋势分析路由 |
| `app/api/v1/creative_seeds.py` | 创作种子/灵感路由 |
| `app/api/v1/scheduled_tasks.py` | 定时任务路由 |
| `app/api/v1/task_queue.py` | 任务队列状态路由 |
| `app/api/v1/settings.py` / `platform_config.py` | 系统设置、模型配置路由 |
| `app/api/v1/dependencies.py` | 路由级依赖注入（鉴权、DB session） |
| `app/models/` | SQLAlchemy ORM 模型：统一用户、模板、素材、生成任务/子任务、分发、通知、模型配置 |
| `app/services/generation_phases.py` | **三阶段事务核心**：读取→生成→保存，各自独立 session |
| `app/services/generation_service.py` | 生成业务逻辑编排 |
| `app/services/dedup_service.py` | 重复数据删除规则 |
| `app/services/async_embedding_service.py` | 生成后异步写回向量/嵌入，不阻塞主事务 |
| `app/services/material_service.py` / `material_platform_service.py` | 素材与素材平台服务 |
| `app/services/auth_service.py` | 认证鉴权业务逻辑 |
| `app/services/dashboard_service.py` | 仪表盘统计聚合 |
| `app/services/scheduled_task_service.py` | 定时任务调度服务 |
| `app/core/database.py` / `security.py` | 数据库连接池管理、JWT/密码哈希/登录锁定 |
| `app/tasks/` | Celery Worker：消费 Redis 队列、执行子任务、推送进度 |

### 前端 `platform_web/`
| 路径 | 作用 |
|---|---|
| `src/main.ts` | 应用入口：挂载路由、Pinia、Element Plus、全局样式 |
| `src/api/` | 统一 API 客户端（axios 封装 + TS 类型定义 + 统一错误处理） |
| `src/store/` 或 `src/stores/` | Pinia 状态管理，按功能模块划分 Store |
| `src/views/` | 页面视图：登录、仪表盘、用户管理、模板库、素材库、内容生成、系统设置 |
| `src/components/` | 可复用组件（卡片、列表、弹窗、进度条等） |

### 文档与部署
| 路径 | 作用 |
|---|---|
| `docs/api-design.md` | 完整 RESTful API 与 WebSocket 契约、请求/响应示例、错误码 |
| `docs/data-model-analysis.md` | 优化后的表结构设计、多租户隔离方案 |
| `docs/web-ui-design.md` | Web UI 设计文档 |
| `docs/media-aigc-platform-prd.md` | 产品需求文档（角色、业务流程、功能清单） |
| `docker/` | 容器化构建与运行配置 |
| `scripts/` | 构建、部署、许可证检查等运维脚本 |
| `functions/` | Serverless Functions（边缘函数等） |

---

## 六、复杂度热点（Complexity Hotspots）

以下区域逻辑密集或处于架构关键位置，新人需谨慎改动、充分理解后再动手：

1. **三阶段事务架构（concept）** — 全局性能与稳定性的核心优化，改动须严格遵循"短事务、及时释放、AI 调用不占连接"原则。
2. **AI 模型适配器（concept）** — 多平台策略模式，新增/调整平台需实现 `BaseModelAdapter` 接口并配套并发与重试配置。
3. **Celery 异步任务流（concept）** — 子任务分解、并发限流、失败重试、自动模型切换的协同逻辑，易引入竞态。
4. **RBAC 与多租户隔离（concept）** — 任何数据访问都必须携带 `owner_admin_id` 过滤，避免越权。
5. **依赖枢纽节点** — 图谱中边数量最高的若干文件（如 `app/main.py`、`app/services/__init__.py`、各 ORM 基类）是架构关键节点，修改影响面广。

**开发规范速记**（详见项目 `CODEBUDDY.md` / `.codebuddy/` 规则）：
- 后端遵循三阶段事务架构，禁止在事务中执行耗时 AI 调用。
- AI 平台接入统一走 `BaseModelAdapter` 策略模式。
- 数据库变更必须配套 Alembic 迁移文件（含 `upgrade`/`downgrade`）。
- 前端任何可点击入口都必须有对应后端实现，禁止占位空函数。
- 提交信息遵循 `<type>(<scope>): <subject>` 规范；禁止强推 master/develop。

---

## 七、本地起步（Local Setup）

```bash
# 后端
cd platform_api
pip install -r requirements.txt
cp .env.example .env          # 配置 DB / Redis / COS / API Key
alembic upgrade head
celery -A app.tasks.celery_app worker --loglevel=info
uvicorn app.main:app --reload

# 前端
cd platform_web
npm install
npm run dev
```

---

*本指南基于提交 `9bf7049` 的知识图谱生成。代码演进后请重新运行 `/understand` 刷新图谱，再执行 `/understand-onboard` 更新本指南。*
