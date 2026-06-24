# Docker部署指南

> 妙笔内容工场 - Docker系统测试与部署指南

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [服务说明](#服务说明)
- [环境配置](#环境配置)
- [开发模式](#开发模式)
- [测试模式](#测试模式)
- [生产模式](#生产模式)
- [常用命令](#常用命令)
- [故障排查](#故障排查)

## 概述

本项目使用 Docker Compose 进行多容器编排，包含以下服务：

- **mysql**: MySQL 8.0 数据库
- **redis**: Redis 7 缓存/消息队列
- **api**: FastAPI 后端服务
- **web**: Vue 3 + Nginx 前端服务
- **celery-worker**: Celery 异步任务工作进程
- **celery-beat**: Celery 定时任务调度器
- **flower**: Celery 监控面板
- **phpmyadmin**: 数据库管理面板 (可选)

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 20GB 可用磁盘空间

### 检查Docker版本

```bash
docker --version
docker-compose --version
```

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd auto_aigc_factory
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
nano .env
```

### 3. 使用部署脚本启动服务

```bash
# 开发环境（默认）
./scripts/deploy-docker.sh

# 测试环境
./scripts/deploy-docker.sh -e test

# 生产环境
./scripts/deploy-docker.sh -e production
```

**部署脚本选项：**

| 选项 | 说明 |
|------|------|
| `-e, --env ENV` | 部署环境 (development\|test\|production) |
| `-m, --mode MODE` | 部署模式 (up\|down\|restart\|rebuild) |
| `-s, --skip-build` | 跳过镜像构建 |
| `-i, --skip-init` | 跳过数据初始化 |

**重要说明：**
- 首次启动时，API 服务会自动执行数据库迁移和初始化
- 数据初始化: 从 `platform_api/config/init_data.yaml` 加载配置
- 默认账号: `admin / admin123`
- 等待 API 服务就绪可能需要 30-60 秒

### 5. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端Web | http://localhost:8080 | Web管理后台 |
| 后端API | http://localhost:8000 | API服务 |
| API文档 | http://localhost:8000/docs | Swagger文档 |

### 6. 停止服务

```bash
# 停止服务但保留数据
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除所有（包括数据卷）
docker-compose down -v
```

## 服务说明

### MySQL 数据库

- **镜像**: `mysql:8.0`
- **端口**: `3306` (可通过 `.env` 修改)
- **数据卷**: `mysql-data`
- **字符集**: `utf8mb4`

### Redis 缓存

- **镜像**: `redis:7-alpine`
- **端口**: `6379` (可通过 `.env` 修改)
- **数据卷**: `redis-data`
- **持久化**: AOF模式

### 后端API (FastAPI)

- **Dockerfile**: `platform_api/Dockerfile`
- **端口**: `8000` (可通过 `.env` 修改)
- **多阶段构建**:
  - `development`: 开发模式，支持热重载
  - `production`: 生产模式，4worker进程

### 前端Web (Vue 3)

- **Dockerfile**: `platform_web/Dockerfile`
- **端口**: `8080` (可通过 `.env` 修改)
- **多阶段构建**:
  - `development`: 开发模式，Vite dev server
  - `production`: 生产模式，Nginx服务静态文件

### Celery Worker

- **镜像**: 基于后端API镜像
- **并发数**: 默认为4 (可通过 `.env` 修改)
- **队列**: Redis

### Flower 监控

- **端口**: `5555` (可通过 `.env` 修改)
- **功能**: 查看Celery任务状态、工作进程、失败任务等

## 环境配置

### 基本配置

在 `.env` 文件中配置以下关键项：

```env
# 数据库
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_secure_root_password

# Redis
REDIS_PASSWORD=your_redis_password

# 安全密钥 (生产环境必须修改)
SECRET_KEY=your-super-secret-key-change-in-production

# CORS (根据实际域名修改)
CORS_ORIGINS=["https://your-domain.com"]
```

### 模式切换

通过环境变量切换构建目标：

```env
# 后端模式: development 或 production
API_TARGET=development

# 前端模式: development 或 production
WEB_TARGET=development
```

## 开发模式

### 启动开发环境

```bash
# 使用默认配置（开发模式）
docker-compose up -d

# 查看实时日志
docker-compose logs -f api web
```

### 代码热重载

- 后端: 修改 `platform_api/` 下的Python文件会自动重载
- 前端: 修改 `platform_web/` 下的Vue/TS文件会自动刷新

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec api bash

# 进入前端容器
docker-compose exec web sh

# 进入数据库
docker-compose exec mysql mysql -u aigc_user -p aigc_platform

# 进入Redis
docker-compose exec redis redis-cli -a redis_password123
```

## 测试模式

### E2E测试环境

项目提供了专门的测试环境配置 `docker-compose.test.yml`：

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行E2E测试
docker-compose -f docker-compose.test.yml run playwright

# 查看测试报告
open platform_web/playwright-report/index.html
```

### 测试环境特点

- 使用tmpfs加速数据库和Redis
- 数据不持久化（每次启动都是干净状态）
- 独立的网络命名空间
- 预设测试账号和Mock数据

## 生产模式

### 生产环境配置

1. 修改 `.env` 文件：

```env
ENVIRONMENT=production
DEBUG=false
API_TARGET=production
WEB_TARGET=production
```

2. 创建生产环境专用的 `docker-compose.prod.yml`：

```yaml
version: '3.8'
services:
  api:
    build:
      target: production
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    restart: always

  web:
    build:
      target: production
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    restart: always
```

3. 启动生产环境：

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 生产环境安全建议

- [ ] 修改所有默认密码
- [ ] 使用强SECRET_KEY
- [ ] 配置HTTPS (使用Traefik或Nginx)
- [ ] 启用防火墙限制端口访问
- [ ] 配置定期备份
- [ ] 使用私有镜像仓库
- [ ] 启用日志收集和监控

## 数据库管理

### 自动初始化

API 服务启动时会自动执行以下操作：
1. 等待数据库连接就绪
2. 运行 Alembic 数据库迁移
3. 从 `config/init_data.yaml` 初始化数据（超级管理员、模型配置、标签等）

### 手动初始化

如需手动重新初始化数据：

```bash
# 初始化所有数据（幂等操作，不会重复创建已存在的数据）
docker-compose exec api python scripts/init_all.py

# 仅初始化模型配置
docker-compose exec api python scripts/init_model_configs.py

# 重置超级管理员密码
docker-compose exec api python scripts/reset_admin_password.py admin newpassword123
```

### 配置初始化数据

编辑 `platform_api/config/init_data.yaml` 文件来自定义初始化数据：

```yaml
super_admin:
  userid: admin
  password: admin123456
  nickname: 超级管理员

model_configs:
  - platform: bailian
    model_id: qwen-vl-max
    model_name: 通义千问-VL-Max
    model_type: multimodal
    # ... 更多配置
```

### 使用 Makefile 快捷命令

项目提供了方便的 Makefile 命令：

```bash
# 查看所有可用命令
make help

# 启动开发环境
make dev

# 运行数据库迁移
make db-migrate

# 初始化数据
make db-init

# 重置超级管理员密码
make db-reset-admin-password userid=admin password=newpass123

# 查看日志
make logs
make logs-api
```

## 常用命令

### 服务管理

```bash
# 使用部署脚本管理服务
./scripts/deploy-docker.sh -m up        # 启动服务
./scripts/deploy-docker.sh -m down      # 停止服务
./scripts/deploy-docker.sh -m restart  # 重启服务
./scripts/deploy-docker.sh -m rebuild  # 重新构建并启动

# 直接使用 docker-compose
docker-compose up -d
docker-compose stop
docker-compose restart
docker-compose ps
docker-compose stats
```

### 日志管理

```bash
# 使用 Makefile 查看日志
make logs          # 所有服务日志
make logs-api      # API 服务日志
make logs-web      # Web 服务日志
make logs celery    # Celery 日志

# 直接使用 docker-compose
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs --tail=100 api
```

### 构建管理

```bash
# 重新构建（使用脚本）
./scripts/deploy-docker.sh -m rebuild

# 直接构建
docker-compose build
docker-compose build --no-cache
docker-compose pull
```

### 数据管理

```bash
# 备份数据库
docker exec aigc-platform-mysql mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" aigc_platform > backup.sql

# 恢复数据库
docker exec -T aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" aigc_platform < backup.sql

# 使用 Makefile 备份
make db-backup
```

### 平滑升级

```bash
# 使用升级脚本
./scripts/upgrade.sh              # Docker 部署升级
./scripts/upgrade.sh -n            # 跳过备份快速升级
```

**升级脚本选项：**

| 选项 | 说明 |
|------|------|
| `-b, --backup` | 升级前备份（默认开启） |
| `-n, --no-backup` | 跳过备份 |
| `-c, --continue` | 升级失败时继续 |

### 清理命令

```bash
# 使用 Makefile
make clean              # 清理未使用资源
make clean-all          # 完全重置（慎用！）

# 直接使用 docker
docker image prune
docker container prune
docker volume prune
docker system prune -a
docker-compose down -v --rmi all
```

## 故障排查

### 服务无法启动

```bash
# 查看具体服务日志
docker-compose logs api

# 检查端口占用
lsof -i :8000
lsof -i :8080

# 检查磁盘空间
df -h

# 检查Docker服务状态
systemctl status docker
```

### 数据库连接失败

```bash
# 确认MySQL容器正在运行
docker-compose ps mysql

# 检查MySQL日志
docker-compose logs mysql

# 手动连接测试
docker-compose exec mysql mysql -u aigc_user -p

# 检查环境变量
docker-compose config | grep MYSQL
```

### 前端无法访问后端API

```bash
# 确认后端服务健康
curl http://localhost:8000/health

# 检查CORS配置
docker-compose exec api env | grep CORS

# 查看Nginx配置（生产模式）
docker-compose exec web cat /etc/nginx/conf.d/default.conf

# 检查前端环境变量
docker-compose exec web env | grep VITE
```

### Celery任务不执行

```bash
# 查看Celery worker日志
make logs-celery
docker-compose logs celery-worker

# 检查Redis连接
docker exec aigc-platform-redis redis-cli ping

# 查看Flower监控面板
open http://localhost:5555

# 检查任务队列
docker exec aigc-platform-api python -c "
from app.tasks.celery_app import celery_app
print(celery_app.control.inspect().active())
"
```

### 性能问题

```bash
# 查看资源使用
docker-compose stats

# 检查慢查询（MySQL）
docker exec aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SHOW PROCESSLIST;"

# 检查Redis内存使用
docker exec aigc-platform-redis redis-cli info memory
```

### 升级失败回滚

```bash
# 查看备份目录
ls -la backups/

# 选择最新的备份恢复
BACKUP_DIR="backups/20250101_120000"

# 恢复数据库
docker exec -T aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" aigc_platform < "$BACKUP_DIR/database.sql"

# 恢复 .env 文件
cp "$BACKUP_DIR/.env" .env

# 重启服务
./scripts/deploy-docker.sh -m restart
```

## 获取帮助

- 查看项目文档: `docs/` 目录
- 查看API文档: http://localhost:8000/docs
- 提交Issue: GitHub Issues
- 联系技术支持

## 更新日志

### v1.1.0 (2025-04-21)
- 新增部署脚本 `scripts/deploy-docker.sh`，支持一键部署
  - 支持开发/测试/生产环境切换
  - 支持跳过构建和跳过初始化选项
  - 自动等待 MySQL 和 API 服务就绪
- 新增平滑升级脚本 `scripts/upgrade.sh`
  - 支持 Docker 部署升级
  - 自动备份数据库和配置文件
  - 支持升级失败回滚

### v1.0.0 (2025-04-08)
- 初始版本
- 支持开发、测试、生产三种模式
- 完整的Docker Compose编排
- E2E测试环境支持
