# Docker 配置目录

> 妙笔内容工场 - Docker 配置文件说明

## 目录结构

```
docker/
├── README.md                  # Docker 配置说明（本文件）
├── docker-compose.yml       # 生产环境 Docker Compose 配置
├── docker-compose.dev.yml   # 开发环境 Docker Compose 配置
├── docker-compose.test.yml  # 测试环境 Docker Compose 配置
└── .dockerignore           # Docker 构建忽略文件
```

## 相关文件

项目根目录的 Docker 相关文件：

```
项目根目录/
├── .env.example               # 环境变量示例
├── Makefile                   # 便捷命令管理
├── platform_api/
│   ├── Dockerfile             # 后端 API Dockerfile
│   └── .dockerignore
└── platform_web/
    ├── Dockerfile             # 前端 Web Dockerfile
    ├── .dockerignore
    ├── nginx.conf             # Nginx 主配置
    └── conf.d/
        └── default.conf       # Nginx 站点配置
```

## 快速开始

### 方式一：使用 Make（推荐）

```bash
# 初始化并启动开发环境
make dev-deploy-docker

# 查看服务状态
make dev-status

# 查看日志
make dev-logs

# 停止服务
make dev-stop
```

### 方式二：使用 Docker Compose 命令

```bash
# 复制环境变量
cp .env.example .env

# 启动所有服务（开发环境
docker-compose -f docker/docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker/docker-compose.dev.yml down
```

## 服务说明

### 后端 API (platform_api/Dockerfile)

- **基础镜像**: `python:3.11-slim-bookworm`
- **多阶段构建**:
  - `base`: 基础依赖层
  - `development`: 开发模式（热重载）
  - `production`: 生产模式（4 worker 进程）

### 前端 Web (platform_web/Dockerfile)

- **多阶段构建**:
  - `builder`: 基于 `node:20-slim`，构建 Vue 应用
  - `production`: 基于 `nginx:alpine`，生产模式
  - `development`: 基于 `node:20-slim`，开发模式（Vite dev server）

## 环境配置

### 基本配置

在 `.env` 文件中配置以下关键项：

```env
# 数据库
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_secure_root_password

# Redis
REDIS_PASSWORD=your_redis_password

# 安全密钥（生产环境必须修改）
SECRET_KEY=your-super-secret-key-change-in-production

# CORS（根据实际域名修改）
CORS_ORIGINS=["https://your-domain.com"]
```

### 模式切换

```env
# 后端模式: development 或 production
API_TARGET=development

# 前端模式: development 或 production
WEB_TARGET=development
```

## 初始化管理员账号配置

```env
# 超级管理员
INITIAL_SUPER_ADMIN_USERID=admin
INITIAL_SUPER_ADMIN_PASSWORD=admin123
INITIAL_SUPER_ADMIN_NICKNAME=超级管理员

# 运营管理员
INITIAL_OPERATOR_ADMIN_USERID=operator
INITIAL_OPERATOR_ADMIN_PASSWORD=operator123
INITIAL_OPERATOR_ADMIN_NICKNAME=默认运营管理员
```

## 常用命令

### 开发常用

```bash
# 启动开发环境
make dev-deploy-docker

# 查看日志
make dev-logs

# 进入容器
docker exec -it aigc-platform-api bash

# 重启服务
make dev-restart
```

### 数据库管理

```bash
# 进入数据库 Shell
docker exec -it aigc-platform-mysql mysql -u aigc_user -p

# 备份数据库
make prod-db-backup

# 运行迁移
docker exec -it aigc-platform-api alembic upgrade head

# 初始化数据
docker exec -it aigc-platform-api python3 scripts/init_all.py
```

### 清理命令

```bash
# 清理容器和网络
make dev-stop

# 完全清理（包括镜像和数据，谨慎使用）
# rm -rf data/mysql/*
```

## 服务访问

| 服务 | 本地地址 | 说明 |
|------|----------|------|
| 前端 Web | http://localhost:8080 (开发) / http://localhost (生产) | Web 管理后台 |
| 后端 API | http://localhost:8000 | RESTful API |
| API 文档 | http://localhost:8000/docs | Swagger UI |

## 目录说明

- `data/cos/`: COS 对象存储挂载目录
- `data/mysql/`: MySQL 数据持久化目录
- `logs/`: 服务日志目录
- `backups/`: 数据库备份目录（自动创建）

## 注意：数据库初始化

> **重要**：本项目不再使用 MySQL 初始化 SQL 脚本
> 
> 数据库表结构和初始数据通过以下方式创建：
> 
> 1. **Alembic 迁移**: `alembic upgrade head`
>    - 创建所有表结构
>    - 管理数据库版本控制
> 
> 2. **Python 初始化脚本**: `python3 scripts/init_all.py`
>    - 初始化管理员账号
>    - 初始化系统配置
>    - 初始化业务数据（模板平台、分类、标签等）

## 故障排查

### 服务无法启动

```bash
# 查看具体服务日志
docker-compose -f docker/docker-compose.dev.yml logs api

# 检查端口占用
lsof -i :8000
lsof -i :8080

# 检查磁盘空间
df -h
```

### 数据库连接失败

```bash
# 确认 MySQL 容器正在运行
docker-compose -f docker/docker-compose.dev.yml ps mysql

# 检查 MySQL 日志
docker logs aigc-platform-mysql

# 手动连接测试
docker exec -it aigc-platform-mysql mysql -u aigc_user -p
```

### Unknown column 错误

如果遇到 `Unknown column 'template_tag.is_system` 类似错误：

```bash
# 确认已运行最新的 Alembic 迁移
docker exec -it aigc-platform-api bash
alembic current
alembic upgrade head
```

## 详细文档

详细使用说明请参考：`docs/` 目录下的相关文档
