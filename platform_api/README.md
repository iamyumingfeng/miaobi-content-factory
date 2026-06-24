# 妙笔内容工场 - 后端 API 服务

基于 FastAPI 的妙笔内容工场后端服务。

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 框架 | FastAPI 0.104+ |
| ORM | SQLAlchemy 2.0 (异步) |
| 数据库 | MySQL 8.0+ (aiomysql) |
| 认证 | JWT (python-jose) |
| 密码 | passlib[bcrypt] |
| 异步任务 | Celery 5.3+ + Redis |
| 实时通信 | WebSocket |
| 迁移 | Alembic |
| 对象存储 | 腾讯云 COS |

## 项目结构

```
platform_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 主入口
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py          # 认证 API
│   │       ├── users.py         # 用户管理 API
│   │       ├── templates.py     # 模板管理 API
│   │       ├── materials.py     # 素材管理 API
│   │       ├── generation.py   # 内容生成 API
│   │       ├── distribution.py # 内容分发 API
│   │       ├── notifications.py# 通知 API
│   │       ├── settings.py      # 系统设置 API
│   │       └── miniprogram.py  # 小程序 API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── security.py         # 安全工具（JWT、密码）
│   │   └── exceptions.py       # 自定义异常
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # 统一用户模型
│   │   ├── template.py        # 模板模型
│   │   ├── material.py        # 素材模型
│   │   ├── generation.py      # 生成任务模型
│   │   ├── distribution.py     # 分发模型
│   │   └── system.py          # 系统配置模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py          # 通用 Schema
│   │   ├── auth.py            # 认证 Schema
│   │   └── *.py               # 各模块 Schema
│   ├── services/              # 业务逻辑层
│   ├── adapters/              # AI 模型适配器
│   ├── tasks/                 # Celery 异步任务
│   └── utils/
│       ├── deps.py            # 依赖注入
│       └── response.py         # 响应工具
├── alembic/
│   ├── versions/              # 迁移版本
│   └── env.py
├── scripts/
│   └── init_db.py             # 数据库初始化
├── tests/
├── config/
│   └── init_data.yaml         # 初始化数据配置
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
cd platform_api
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis、API 密钥等
```

### 3. 初始化数据库

```bash
# 方式一：使用初始化脚本（推荐首次使用）
python scripts/deploy/all.py

# 方式二：使用 Alembic 迁移
alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 FastAPI 主入口
python main.py
```

### 5. 启动 Celery Worker（异步任务）

```bash
celery -A app.tasks.celery_app worker --loglevel=info

# 启动 Beat（定时任务调度）
celery -A app.tasks.celery_app beat --loglevel=info
```

### 6. 访问 API

- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

## 默认账号

初始化数据库后会创建默认超级管理员：

| 字段 | 值 |
|------|-----|
| 用户ID | admin |
| 密码 | admin123 |

⚠️ **重要**: 请在首次登录后立即修改默认密码！

## 核心数据模型

### 用户体系（按角色分表，物理隔离）

| 表名 | 说明 |
|------|------|
| `super_admin` | 超级管理员表 |
| `operator` | 运营管理员表 |
| `sub_user` | 子用户表 |
| `all_user` | 统一用户视图（用于认证） |

### 业务数据

| 表名 | 说明 |
|------|------|
| `template` | 模板表 |
| `template_platform` | 模板平台表 |
| `template_tag` | 模板标签表 |
| `material` | 素材表 |
| `material_attachment` | 素材附件表 |
| `generation_task` | 生成任务表 |
| `generation_item` | 生成子任务表 |
| `distribution` | 分发记录表 |
| `notification` | 通知表 |
| `model_config` | 模型配置表 |

## API 模块

### 认证模块 (`/api/v1/auth`)
- `POST /login` - 账号密码登录
- `POST /wechat/qr` - 获取微信登录二维码
- `GET /wechat/qr/{state}` - 查询微信扫码状态
- `POST /bind-wechat` - 绑定微信
- `POST /unbind-wechat` - 解绑微信
- `POST /logout` - 退出登录

### 用户管理模块 (`/api/v1/users`)
- 超级管理员：管理运营管理员
- 运营管理员：管理子用户
- 用户标签管理

### 模板管理模块 (`/api/v1/templates`)
- 模板 CRUD、复制、启用/禁用
- 模板平台管理
- 模板标签管理

### 素材管理模块 (`/api/v1/materials`)
- 素材上传、CRUD、收藏
- 素材分类、标签管理

### 内容生成模块 (`/api/v1/generation`)
- 创建生成任务
- 任务列表/详情查询
- 子任务管理
- 暂停/继续/重试
- WebSocket 实时进度推送

### 内容分发模块 (`/api/v1/distribution`)
- 批量分发
- 分发记录查询
- 确认发布

### 系统设置模块 (`/api/v1/settings`)
- 个人设置
- 模型配置管理（超级管理员）

## AI 模型适配器

支持以下模型平台的适配：

| 平台 | 说明 |
|------|------|
| 百炼 (bailian) | 阿里云百炼 |
| 元宝 (yuanbao) | 腾讯元宝 |
| 月之暗面 (moonshot) | Moonshot |
| 智谱AI (zhipu) | 智谱 GLM |
| 豆包 (doubao) | 字节豆包 |
| 即梦 (jimeng) | 即梦图片生成 |
| 可灵 (kling) | 可灵视频生成 |

### 使用示例

```python
from app.adapters.factory import ModelAdapterFactory

# 创建适配器
factory = ModelAdapterFactory()
adapter = factory.create_adapter("bailian", "qwen-vl-max")

# 生成文本
result = await adapter.generate_text(
    prompt="请生成一篇关于春天的文案",
    parameters={"temperature": 0.7}
)

# 生成图片
image_result = await adapter.generate_image(
    prompt="一只可爱的猫咪",
    parameters={"size": "1024x1024"}
)
```

## 环境变量配置

主要环境变量见 `.env.example` 文件：

```env
# 数据库
DATABASE_URL=mysql+aiomysql://user:password@host:3306/dbname

# Redis
REDIS_URL=redis://:password@host:6379/0

# 安全
SECRET_KEY=your-super-secret-key

# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# COS
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_BUCKET=your-bucket
COS_REGION=ap-guangzhou
```

## 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 升级
alembic upgrade head

# 降级
alembic downgrade -1

# 查看当前版本
alembic current
```

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=app tests/
```

## 故障排查

### 数据库连接失败
```bash
# 检查数据库服务
mysql -h localhost -u aigc_user -p

# 检查连接配置
python -c "from app.core.database import engine; print(engine.url)"
```

### Redis 连接失败
```bash
# 检查 Redis 服务
redis-cli -h localhost -p 6379

# 测试连接
python -c "import redis; r = redis.from_url('redis://:password@localhost:6379/0'); print(r.ping())"
```

### Celery 任务不执行
```bash
# 检查 Worker 状态
celery -A app.tasks.celery_app inspect active

# 查看任务队列
celery -A app.tasks.celery_app inspect active_queues
```

## 相关文档

- [API 设计文档](../docs/api-design.md)
- [数据库设计文档](../docs/data-model-analysis.md)
- [后端服务详细 PRD](../docs/backend-prd.md)
- [Docker 部署指南](../docs/docker-guide.md)

## 许可证

Copyright © 2025
