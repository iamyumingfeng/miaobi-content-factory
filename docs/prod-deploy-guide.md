# 生产环境部署指南

## 一、部署概述

生产环境仅支持 **Docker 镜像部署**，确保环境一致性和部署可靠性。

### 部署方式

| 命令 | 说明 | 使用场景 |
|------|------|----------|
| `make prod-deploy` | 首次部署 | 第一次部署到生产环境 |
| `make prod-upgrade` | 升级部署 | 更新版本或修复问题 |
| `make prod-rollback` | 回滚版本 | 升级失败时回滚 |
| `make prod-backup` | 手动备份 | 定期数据备份 |
| `make prod-status` | 查看状态 | 检查服务运行状态 |
| `make prod-logs` | 查看日志 | 排查问题 |

---

## 二、前置要求

### 2.1 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 3 GB | 8 GB+ |
| 磁盘 | 50 GB | 100 GB+ SSD |
| 带宽 | 5 Mbps | 10 Mbps+ |

### 2.2 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Git（可选，用于拉取代码）

### 2.3 网络要求

- 开放端口：80（Web）、8000（API）、3306（MySQL）、6379（Redis）
- 配置域名解析（推荐）
- 配置 HTTPS（推荐）

---

## 三、首次部署

### 3.1 准备工作

#### 1. 下载代码

```bash
# 克隆项目
git clone <repository-url>
cd auto_aigc_factory

# 或直接下载代码包并解压
```

#### 2. 创建环境配置文件

```bash
# 复制生产环境配置模板
cp .env.prod.example .env

# 编辑配置文件
vi .env
```

#### 3. 配置必要参数

编辑 `.env` 文件，**必须修改**以下配置项：

```bash
# 数据库密码（使用强密码）
MYSQL_PASSWORD=your_strong_password_here
MYSQL_ROOT_PASSWORD=your_strong_root_password_here

# Redis 密码（使用强密码）
REDIS_PASSWORD=your_strong_redis_password_here

# JWT 密钥（随机生成）
# 生成方法: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_random_secret_key_here

# CORS 允许的域名
CORS_ORIGINS=["https://yourdomain.com"]

# API 地址
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1

# 腾讯云 COS 配置
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_BUCKET=your-bucket-name
COS_REGION=ap-guangzhou

# AI 模型 API Key（根据需要配置）
BAILIAN_API_KEY=your-bailian-api-key
VOLCANO_API_KEY=your-volcano-api-key
# ... 其他模型配置
```

### 3.2 执行部署

```bash
# 一键部署
make prod-deploy
```

部署脚本会自动完成：
1. ✅ 检查环境配置
2. ✅ 检查系统资源
3. ✅ 创建必要目录
4. ✅ 构建生产镜像
5. ✅ 启动所有服务
6. ✅ 等待服务就绪
7. ✅ 执行数据库迁移
8. ✅ 初始化数据

### 3.3 验证部署

```bash
# 查看服务状态
make prod-status

# 查看服务日志
make prod-logs

# 健康检查
curl http://localhost:8000/health
```

### 3.4 访问服务

部署完成后，可以访问：

- **前端 Web**: http://your-domain.com
- **后端 API**: http://your-domain.com:8000
- **API 文档**: http://your-domain.com:8000/docs
- **默认账号**: admin / admin123

⚠️ **重要**: 首次登录后立即修改默认密码！

---

## 四、升级部署

### 4.1 升级前准备

#### 1. 备份数据（自动）

升级脚本会自动备份：
- 数据库数据
- `.env` 配置文件
- COS 数据（如果存在）

备份文件保存在 `backups/` 目录。

#### 2. 通知用户

建议在低峰期进行升级，并提前通知用户。

### 4.2 执行升级

```bash
# 一键升级
make prod-upgrade
```

升级流程：
1. ✅ 检查环境配置
2. ✅ 备份数据库和配置
3. ✅ 拉取最新代码（如果使用 Git）
4. ✅ 重新构建镜像
5. ✅ 停止旧服务
6. ✅ 启动新服务
7. ✅ 执行数据库迁移
8. ✅ 健康检查

### 4.3 验证升级

```bash
# 查看服务状态
make prod-status

# 查看服务日志
make prod-logs

# 测试关键功能
# 1. 登录测试
# 2. API 调用测试
# 3. 核心业务流程测试
```

### 4.4 升级失败处理

如果升级失败，可以：

1. **查看日志排查问题**:
   ```bash
   make prod-logs
   ```

2. **回滚到上一版本**:
   ```bash
   make prod-rollback
   ```

---

## 五、回滚部署

### 5.1 自动回滚

如果升级失败，可以快速回滚：

```bash
# 回滚到上一版本
make prod-rollback
```

回滚流程：
1. 查找最近的备份
2. 确认回滚版本
3. 停止服务
4. 恢复数据库
5. 恢复配置文件
6. 恢复 COS 数据
7. 启动服务

### 5.2 手动回滚

如果需要回滚到特定版本：

```bash
# 查看备份列表
ls -lt backups/

# 手动恢复数据库
docker exec -i aigc-platform-mysql mysql \
  -u root -p"${MYSQL_ROOT_PASSWORD}" \
  aigc_platform < backups/YYYYMMDD_HHMMSS/database.sql

# 重启服务
docker-compose restart
```

---

## 六、数据备份

### 6.1 自动备份

升级部署时会自动备份数据，备份文件保存在 `backups/` 目录：

```
backups/
├── 20260507_120000/
│   ├── database.sql       # 数据库备份
│   ├── .env              # 配置文件备份
│   └── cos_data.tar.gz   # COS 数据备份
├── 20260507_130000/
│   └── ...
```

### 6.2 手动备份

定期手动备份：

```bash
# 手动备份
make prod-backup
```

### 6.3 备份策略建议

- **每日备份**: 使用 cron 定时任务每日备份
- **保留策略**: 保留最近 7 天的备份
- **异地备份**: 定期将备份文件同步到其他服务器或对象存储

### 6.4 定时备份配置

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点备份）
0 2 * * * cd /path/to/auto_aigc_factory && make prod-backup >> logs/backup.log 2>&1
```

---

## 七、环境配置

### 7.1 配置文件说明

生产环境使用 `.env` 文件，包含所有生产环境配置。

### 7.2 必要配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `MYSQL_PASSWORD` | 数据库用户密码 | 强密码（16位+） |
| `MYSQL_ROOT_PASSWORD` | 数据库 root 密码 | 强密码（16位+） |
| `REDIS_PASSWORD` | Redis 密码 | 强密码（16位+） |
| `SECRET_KEY` | JWT 密钥 | 随机生成（32位+） |
| `CORS_ORIGINS` | 允许的域名 | `["https://yourdomain.com"]` |
| `VITE_API_BASE_URL` | API 地址 | `https://api.yourdomain.com/api/v1` |
| `COS_SECRET_ID` | 腾讯云 COS 密钥 ID | 从腾讯云控制台获取 |
| `COS_SECRET_KEY` | 腾讯云 COS 密钥 Key | 从腾讯云控制台获取 |
| `COS_BUCKET` | COS 存储桶名称 | `your-bucket-name` |
| `COS_REGION` | COS 地域 | `ap-guangzhou` |

### 7.3 AI 模型配置

根据实际使用的平台配置对应的 API Key：

```bash
# 阿里百炼
BAILIAN_API_KEY=your-bailian-api-key

# 火山引擎
VOLCANO_API_KEY=your-volcano-api-key

# 即梦
JIMENG_ACCESS_KEY=your-jimeng-access-key
JIMENG_SECRET_KEY=your-jimeng-secret-key

# 可灵
KLING_ACCESS_KEY=your-kling-access-key
KLING_SECRET_KEY=your-kling-secret-key

# AutoGLM
AUTOGLM_API_KEY=your-autoglm-api-key

# 月之暗面
MOONSHOT_API_KEY=your-moonshot-api-key

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key

# 灵牙 AI
LINGYAAI_API_KEY=your-lingyaai-api-key
```

---

## 八、监控与日志

### 8.1 服务监控

```bash
# 查看服务状态
make prod-status

# 查看资源使用
docker stats

# 查看容器状态
docker-compose ps
```

### 8.2 日志管理

#### 查看日志

```bash
# 查看所有服务日志
make prod-logs

# 查看特定服务日志
docker logs aigc-platform-api -f --tail 100
docker logs aigc-platform-web -f --tail 100
docker logs aigc-platform-mysql -f --tail 100
docker logs aigc-platform-celery-worker -f --tail 100
```

#### 日志文件位置

日志文件保存在 `logs/` 目录：

```
logs/
├── api/              # API 服务日志
├── web/              # Web 服务日志
├── mysql/            # MySQL 日志
├── redis/            # Redis 日志
├── celery/           # Celery Worker 日志
└── celery-beat/      # Celery Beat 日志
```

#### 日志轮转

生产环境配置了日志轮转，自动清理旧日志：

- 单个日志文件最大：200MB
- 保留日志文件数量：10 个

### 8.3 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# Web 健康检查
curl http://localhost:80/health

# 数据库连接检查
docker exec aigc-platform-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD}"
```

---

## 九、性能优化

### 9.1 资源配置

根据服务器配置调整 `docker-compose.prod.yml` 中的资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### 9.2 数据库优化

```bash
# 调整 MySQL 配置
# 编辑 docker-compose.prod.yml 中的 MySQL 命令参数
command:
  - --innodb_buffer_pool_size=2G
  - --max_connections=500
```

### 9.3 Celery 并发优化

```bash
# 调整 Celery 并发数
# 编辑 .env
CELERY_CONCURRENCY=8  # 根据 CPU 核心数调整
```

---

## 十、安全配置

### 10.1 密码安全

- ✅ 使用强密码（至少 16 位，包含大小写字母、数字、特殊字符）
- ✅ 定期更换密码（建议每 3 个月）
- ✅ 使用密码管理器生成和存储密码

### 10.2 网络安全

- ✅ 配置防火墙，只开放必要端口
- ✅ 使用 HTTPS（推荐配置 SSL 证书）
- ✅ 配置 CORS 白名单
- ✅ 定期更新系统和 Docker

### 10.3 数据安全

- ✅ 定期备份数据库
- ✅ 异地备份
- ✅ 敏感数据加密存储
- ✅ 限制数据库访问权限

---

## 十一、故障排查

### 11.1 服务无法启动

```bash
# 查看服务日志
docker-compose logs

# 检查端口占用
netstat -tunlp | grep -E ':(80|8000|3306|6379)'

# 检查资源使用
df -h
free -m
```

### 11.2 数据库连接失败

```bash
# 检查 MySQL 服务
docker exec aigc-platform-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD}"

# 检查数据库配置
cat .env | grep MYSQL

# 查看 MySQL 日志
docker logs aigc-platform-mysql
```

### 11.3 API 无法访问

```bash
# 检查 API 服务
curl http://localhost:8000/health

# 查看 API 日志
docker logs aigc-platform-api

# 检查端口映射
docker port aigc-platform-api
```

### 11.4 性能问题

```bash
# 查看资源使用
docker stats

# 查看慢查询日志
docker exec aigc-platform-mysql cat /var/log/mysql/slow.log

# 查看 Celery 任务队列
docker exec aigc-platform-redis redis-cli -a "${REDIS_PASSWORD}" llen celery
```

### 11.5 常见部署问题

#### 问题 1: pip 包哈希不匹配

**现象**:
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
```

**解决方案**:
已在 Dockerfile 中修复 - 在安装依赖前先升级 pip：
```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

#### 问题 2: MySQL 启动超时

**现象**:
```
[ERROR] MySQL 启动超时
```

**解决方案**:
1. 检查服务器内存是否足够（至少 4GB）
2. 已优化 MySQL 配置，降低内存要求：
   - `innodb_buffer_pool_size`: 2G → 1G
   - `max_connections`: 500 → 200
3. 延长等待时间到 240 秒
4. 查看 MySQL 日志排查具体问题:
   ```bash
   docker logs aigc-platform-mysql
   ```

#### 问题 3: 低内存服务器优化

**现象**: 服务器内存不足 8GB

**解决方案**:
已在 `docker-compose.prod.yml` 中优化资源配置：
- MySQL: 4G → 2G
- Redis: 2G → 1G
- API: 4G → 2G
- Celery Worker: 8G → 2G

部署脚本会自动检测内存并警告。

#### 问题 4: 容器无法启动

**现象**: 容器一直重启或退出

**排查步骤**:
```bash
# 查看容器状态
docker ps -a

# 查看具体容器日志
docker logs <container-name>

# 检查资源使用
docker stats

# 检查磁盘空间
df -h
```

---

## 十二、运维建议

### 12.1 定期维护

- **每日**: 检查服务状态、查看错误日志
- **每周**: 检查磁盘空间、清理旧日志
- **每月**: 更新系统补丁、检查备份完整性
- **每季度**: 更新密码、安全审计

### 12.2 监控告警

建议配置监控系统（如 Prometheus + Grafana）监控：
- 服务健康状态
- 资源使用率（CPU、内存、磁盘）
- API 响应时间
- 数据库连接数
- Celery 任务队列长度

### 12.3 文档记录

记录以下信息：
- 服务器配置和 IP 地址
- 域名和 SSL 证书信息
- 数据库和 Redis 密码（加密存储）
- 备份策略和恢复流程
- 故障处理记录

---

## 十三、快速参考

### 部署命令

```bash
make prod-deploy     # 首次部署
make prod-upgrade    # 升级部署
make prod-rollback   # 回滚版本
make prod-backup     # 手动备份
make prod-status     # 查看状态
make prod-logs       # 查看日志
```

### 服务管理

```bash
# 停止服务
docker-compose down

# 启动服务
docker-compose up -d

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f
```

### 数据库操作

```bash
# 数据库迁移
docker exec aigc-platform-api alembic upgrade head

# 数据库备份
docker exec aigc-platform-mysql mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" aigc_platform > backup.sql

# 数据库恢复
docker exec -i aigc-platform-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" aigc_platform < backup.sql
```

---

## 十四、下一步

- 查看 [API 文档](api-design.md) 了解接口设计
- 查看 [数据模型](data-model-analysis.md) 了解数据库结构
- 查看 [开发环境部署指南](dev-deploy-guide.md) 了解开发环境配置
