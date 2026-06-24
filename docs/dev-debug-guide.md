# 开发环境调试脚本

本文档提供开发环境的常用调试脚本和命令，帮助开发者快速排查问题和调试代码。

---

## 快速脚本参考

以下脚本已封装好常用调试操作，可直接执行：

| 脚本 | 用途 | 基本用法 |
|------|------|----------|
| `dev-rebuild.sh` | 一键重建镜像 | `./scripts/dev-rebuild.sh` |
| `dev-clean.sh` | 一键清理环境 | `./scripts/dev-clean.sh` |
| `dev-health-check.sh` | 一键健康检查 | `./scripts/dev-health-check.sh` |
| `dev-logs-all.sh` | 一键查看所有日志 | `./scripts/dev-logs-all.sh` |
| `dev-db-backup.sh` | 数据库备份 | `./scripts/dev-db-backup.sh` |
| `dev-db-restore.sh` | 数据库恢复 | `./scripts/dev-db-restore.sh <备份目录>` |
| `dev-monitor.sh` | 资源监控 | `./scripts/dev-monitor.sh` |

### 常用命令示例

```bash
# 无缓存重建所有镜像
./scripts/dev-rebuild.sh -n

# 清理所有资源（包括卷和镜像）
./scripts/dev-clean.sh -a

# 实时查看所有日志
./scripts/dev-logs-all.sh -f

# 查看特定服务最近 500 行日志
./scripts/dev-logs-all.sh -s api -n 500

# 备份所有数据库
./scripts/dev-db-backup.sh -a

# 恢复数据库
./scripts/dev-db-restore.sh backups/20260507_120000

# 实时监控资源（每 2 秒刷新）
./scripts/dev-monitor.sh -r 2

# 单次监控并退出
./scripts/dev-monitor.sh -o
```

---

## 一、Docker 环境调试

### 1.1 服务管理

#### 启动服务

```bash
# 启动开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 或使用部署脚本
./scripts/dev-deploy.sh docker
```

#### 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 停止特定服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml stop api
docker-compose -f docker-compose.yml -f docker-compose.dev.yml stop web
docker-compose -f docker-compose.yml -f docker-compose.dev.yml stop mysql
docker-compose -f docker-compose.yml -f docker-compose.dev.yml stop redis
```

#### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart

# 重启特定服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart api
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart web
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart celery-worker
```

### 1.2 镜像管理

#### 重新构建镜像

```bash
# 重新构建所有镜像
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# 重新构建特定服务镜像
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build api
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build web

# 无缓存重新构建（完全重建）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache

# 无缓存重新构建特定服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache api
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache web
```

#### 查看镜像信息

```bash
# 列出所有镜像
docker images | grep aigc-platform

# 查看镜像详细信息
docker inspect aigc-platform-api:latest
docker inspect aigc-platform-web:latest
```

#### 清理镜像

```bash
# 删除未使用的镜像
docker image prune

# 删除所有未使用的镜像（包括未被任何容器引用的镜像）
docker image prune -a

# 删除特定镜像
docker rmi aigc-platform-api:latest
docker rmi aigc-platform-web:latest
```

### 1.3 容器管理

#### 查看容器状态

```bash
# 查看所有容器状态
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# 查看所有容器（包括停止的）
docker ps -a | grep aigc-platform

# 查看容器详细信息
docker inspect aigc-platform-api
docker inspect aigc-platform-web
```

#### 进入容器

```bash
# 进入 API 容器
docker exec -it aigc-platform-api bash

# 进入 Web 容器
docker exec -it aigc-platform-web sh

# 进入 MySQL 容器
docker exec -it aigc-platform-mysql bash

# 进入 Redis 容器
docker exec -it aigc-platform-redis sh
```

#### 容器资源监控

```bash
# 查看容器资源使用情况
docker stats aigc-platform-api
docker stats aigc-platform-web
docker stats aigc-platform-mysql
docker stats aigc-platform-redis

# 查看所有容器资源使用
docker stats
```

### 1.4 日志查看

#### 查看服务日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker logs aigc-platform-api -f --tail 100
docker logs aigc-platform-web -f --tail 100
docker logs aigc-platform-mysql -f --tail 100
docker logs aigc-platform-redis -f --tail 100
docker logs aigc-platform-celery-worker -f --tail 100
docker logs aigc-platform-celery-beat -f --tail 100

# 查看最近 500 行日志
docker logs aigc-platform-api --tail 500

# 查看指定时间段的日志
docker logs aigc-platform-api --since 1h
docker logs aigc-platform-api --since "2024-01-01T00:00:00"
```

#### 日志文件位置

```bash
# 查看日志文件
ls -lh logs/

# API 日志
tail -f logs/api/app.log

# Web 日志（如果配置了）
tail -f logs/web/nginx.log
```

### 1.5 清理环境

#### 清理容器

```bash
# 停止并删除所有容器
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 停止并删除所有容器和网络
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

# 停止并删除所有容器、网络和卷（危险操作，会删除数据）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

#### 清理系统

```bash
# 清理未使用的容器、网络、镜像
docker system prune

# 清理所有未使用的资源（包括卷）
docker system prune -a --volumes

# 查看磁盘使用情况
docker system df
```

---

## 二、数据库调试

### 2.1 数据库连接

```bash
# 连接到 MySQL 容器
docker exec -it aigc-platform-mysql mysql -u root -p

# 连接到数据库（使用环境变量中的密码）
docker exec -it aigc-platform-mysql mysql -u aigc_user -paigc_password123 aigc_platform

# 从宿主机连接 MySQL
mysql -h 127.0.0.1 -P 3306 -u aigc_user -paigc_password123 aigc_platform
```

### 2.2 数据库迁移

```bash
# 查看当前迁移版本
docker exec aigc-platform-api alembic current

# 查看迁移历史
docker exec aigc-platform-api alembic history

# 升级到最新版本
docker exec aigc-platform-api alembic upgrade head

# 回退一个版本
docker exec aigc-platform-api alembic downgrade -1

# 回退到指定版本
docker exec aigc-platform-api alembic downgrade <revision>

# 生成新的迁移文件
docker exec aigc-platform-api alembic revision --autogenerate -m "description"
```

### 2.3 数据库备份与恢复

```bash
# 备份数据库
docker exec aigc-platform-mysql mysqldump -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" aigc_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker exec -i aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" aigc_platform < backup.sql

# 备份所有数据库
docker exec aigc-platform-mysql mysqldump -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" --all-databases > all_databases.sql
```

### 2.4 数据库查询

```bash
# 查看所有数据库
docker exec aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" -e "SHOW DATABASES;"

# 查看所有表
docker exec aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" aigc_platform -e "SHOW TABLES;"

# 查看表结构
docker exec aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" aigc_platform -e "DESCRIBE all_user;"

# 查看表数据
docker exec aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" aigc_platform -e "SELECT * FROM all_user LIMIT 10;"
```

---

## 三、Redis 调试

### 3.1 Redis 连接

```bash
# 连接到 Redis 容器
docker exec -it aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}"

# 从宿主机连接 Redis
redis-cli -h 127.0.0.1 -p 6379 -a "${REDIS_PASSWORD:-redis_password123}"
```

### 3.2 Redis 命令

```bash
# 查看所有键
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" KEYS "*"

# 查看键的数量
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" DBSIZE

# 查看内存使用
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" INFO memory

# 查看所有信息
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" INFO

# 清空数据库（危险操作）
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" FLUSHDB

# 清空所有数据库（危险操作）
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" FLUSHALL
```

### 3.3 Celery 队列查看

```bash
# 查看 Celery 队列长度
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" LLEN celery

# 查看 Celery 队列内容
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" LRANGE celery 0 -1

# 查看所有 Celery 相关键
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" KEYS "celery*"
```

---

## 四、API 调试

### 4.1 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 查看 API 版本信息
curl http://localhost:8000/api/v1/info

# 查看 OpenAPI 文档
curl http://localhost:8000/openapi.json
```

### 4.2 API 测试

```bash
# 登录测试
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 获取用户信息（需要 token）
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your-token>"

# 测试文件上传
curl -X POST http://localhost:8000/api/v1/materials/upload \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@/path/to/file.jpg"
```

### 4.3 性能测试

```bash
# 使用 ab 进行压力测试
ab -n 1000 -c 10 http://localhost:8000/health

# 使用 wrk 进行压力测试
wrk -t4 -c100 -d30s http://localhost:8000/health
```

---

## 五、前端调试

### 5.1 前端服务

```bash
# 进入前端容器
docker exec -it aigc-platform-web sh

# 查看前端日志
docker logs aigc-platform-web -f --tail 100

# 查看前端构建日志
docker logs aigc-platform-web 2>&1 | grep "build"

# 检查前端进程
docker exec aigc-platform-web ps aux
```

### 5.2 前端开发

```bash
# 进入前端容器并运行开发命令
docker exec -it aigc-platform-web sh
npm run dev

# 查看前端依赖
docker exec aigc-platform-web npm list

# 检查前端代码风格
docker exec aigc-platform-web npm run lint

# 构建生产版本
docker exec aigc-platform-web npm run build
```

---

## 六、网络调试

### 6.1 网络查看

```bash
# 查看所有网络
docker network ls

# 查看网络详细信息
docker network inspect aigc-platform-network

# 查看容器网络配置
docker inspect aigc-platform-api | grep -A 20 "NetworkSettings"
```

### 6.2 端口查看

```bash
# 查看端口映射
docker port aigc-platform-api
docker port aigc-platform-web
docker port aigc-platform-mysql
docker port aigc-platform-redis

# 查看宿主机端口占用
netstat -tunlp | grep -E ':(80|8000|3306|6379)'
lsof -i :8000
```

### 6.3 网络连通性测试

```bash
# 从容器内部测试网络
docker exec aigc-platform-api ping mysql
docker exec aigc-platform-api ping redis
docker exec aigc-platform-api curl http://localhost:8000/health

# 从宿主机测试容器网络
curl http://localhost:8000/health
curl http://localhost:80
```

---

## 七、快速脚本

### 7.1 一键重启所有服务

```bash
#!/bin/bash
# 重启所有服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart
echo "所有服务已重启"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### 7.2 一键清理并重建

```bash
#!/bin/bash
# 停止所有服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
# 删除所有镜像
docker rmi $(docker images | grep aigc-platform | awk '{print $3}')
# 重新构建并启动
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
# 查看状态
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### 7.3 一键查看所有日志

```bash
#!/bin/bash
# 查看所有服务最近 100 行日志
echo "=== API 日志 ==="
docker logs aigc-platform-api --tail 100
echo ""
echo "=== Web 日志 ==="
docker logs aigc-platform-web --tail 100
echo ""
echo "=== MySQL 日志 ==="
docker logs aigc-platform-mysql --tail 100
echo ""
echo "=== Celery 日志 ==="
docker logs aigc-platform-celery-worker --tail 100
```

### 7.4 一键检查服务健康

```bash
#!/bin/bash
echo "=== 服务状态 ==="
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
echo ""
echo "=== API 健康检查 ==="
curl -sf http://localhost:8000/health && echo "✓ API 正常" || echo "✗ API 异常"
echo ""
echo "=== Web 健康检查 ==="
curl -sf http://localhost:80 > /dev/null && echo "✓ Web 正常" || echo "✗ Web 异常"
echo ""
echo "=== 数据库连接检查 ==="
docker exec aigc-platform-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" --silent && echo "✓ MySQL 正常" || echo "✗ MySQL 异常"
echo ""
echo "=== Redis 连接检查 ==="
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" ping | grep -q PONG && echo "✓ Redis 正常" || echo "✗ Redis 异常"
```

---

## 八、常见问题排查

### 8.1 服务无法启动

```bash
# 1. 查看容器日志
docker logs aigc-platform-api
docker logs aigc-platform-web

# 2. 检查端口占用
netstat -tunlp | grep -E ':(80|8000|3306|6379)'

# 3. 检查资源使用
docker stats

# 4. 检查磁盘空间
df -h
```

### 8.2 数据库连接失败

```bash
# 1. 检查 MySQL 容器状态
docker ps | grep mysql

# 2. 查看 MySQL 日志
docker logs aigc-platform-mysql

# 3. 测试数据库连接
docker exec aigc-platform-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}"

# 4. 检查数据库配置
cat .env | grep MYSQL
```

### 8.3 API 响应慢

```bash
# 1. 查看资源使用
docker stats aigc-platform-api

# 2. 查看 API 日志
docker logs aigc-platform-api --tail 500

# 3. 查看数据库慢查询
docker exec aigc-platform-mysql cat /var/log/mysql/slow.log

# 4. 查看 Redis 内存使用
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" INFO memory
```

### 8.4 Celery 任务不执行

```bash
# 1. 查看 Celery Worker 日志
docker logs aigc-platform-celery-worker -f --tail 100

# 2. 查看 Celery 队列
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" LLEN celery

# 3. 查看 Celery Beat 日志
docker logs aigc-platform-celery-beat -f --tail 100

# 4. 重启 Celery 服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart celery-worker celery-beat
```

---

## 九、调试工具推荐

### 9.1 Docker 工具

- **Docker Desktop**: Docker 官方 GUI 工具
- **Portainer**: Docker Web 管理界面
- **ctop**: 容器资源监控工具
- **lazydocker**: Docker 终端 UI

### 9.2 数据库工具

- **DBeaver**: 通用数据库管理工具
- **MySQL Workbench**: MySQL 官方工具
- **phpMyAdmin**: Web 数据库管理工具

### 9.3 Redis 工具

- **RedisInsight**: Redis 官方可视化工具
- **Another Redis Desktop Manager**: Redis 桌面管理工具

### 9.4 API 测试工具

- **Postman**: API 测试工具
- **Insomnia**: REST API 客户端
- **curl**: 命令行 HTTP 工具

---

## 十、快速参考

### Docker Compose 命令

```bash
# 启动服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 停止服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 重启服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart

# 查看状态
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# 构建镜像
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# 进入容器
docker exec -it aigc-platform-api bash
```

### 常用端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Web | 80 | 前端服务 |
| API | 8000 | 后端 API |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |

### 默认账号

- **用户名**: admin
- **密码**: admin123

---

## 十一、下一步

- 查看 [开发环境部署指南](dev-deploy-guide.md) 了解部署流程
- 查看 [API 文档](api-design.md) 了解接口设计
- 查看 [数据模型](data-model-analysis.md) 了解数据库结构
