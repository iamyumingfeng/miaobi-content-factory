# 开发环境部署指南

## 一、Docker 部署（推荐）

### 2.1 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 3GB 可用内存（推荐 4GB+）
- 至少 10GB 可用磁盘空间

### 2.2 一键部署

```bash
# 克隆项目（如果还没有）
git clone <repository-url>
cd auto_aigc_factory

# Docker 一键部署
make dev-deploy-docker
```

部署脚本会自动完成：
1. 创建必要目录
2. 配置环境变量（从 `.env.example` 复制）
3. 构建 Docker 镜像
4. 启动所有服务
5. 等待服务就绪
6. 初始化数据

### 2.3 访问服务

部署完成后，可以访问：

- **前端 Web**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

### 2.4 常用命令

```bash
# 查看服务状态
make dev-status

# 查看服务日志
make dev-logs

# 停止服务
make dev-stop

# 重启服务
make dev-restart
```

### 2.5 服务管理

#### 查看特定服务日志

```bash
# API 日志
docker logs aigc-platform-api -f --tail 100

# Web 日志
docker logs aigc-platform-web -f --tail 100

# MySQL 日志
docker logs aigc-platform-mysql -f --tail 100

# Redis 日志
docker logs aigc-platform-redis -f --tail 100

# Celery Worker 日志
docker logs aigc-platform-celery-worker -f --tail 100
```

#### 进入容器调试

```bash
# 进入 API 容器
docker exec -it aigc-platform-api bash

# 进入 Web 容器
docker exec -it aigc-platform-web sh

# 进入 MySQL 容器
docker exec -it aigc-platform-mysql bash
```

---

## 二、环境变量配置

### 4.1 配置文件

开发环境使用 `.env` 文件，首次部署会从 `.env.example` 自动复制。

### 4.2 必要配置项

```bash
# 数据库配置
MYSQL_HOST=mysql              # Docker 容器服务名
MYSQL_PORT=3306
MYSQL_DATABASE=aigc_platform
MYSQL_USER=aigc_user
MYSQL_PASSWORD=aigc_password123
MYSQL_ROOT_PASSWORD=rootpassword123

# Redis 配置
REDIS_HOST=redis              # Docker 容器服务名
REDIS_PORT=6379
REDIS_PASSWORD=redis_password123

# JWT 配置
SECRET_KEY=2f1b1054c4d9ac3977211c17bbad57983516cd939ce6d7c1361abb7680e6f17b
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# 前端配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 4.3 AI 模型配置（可选）

如果需要测试 AI 模型功能，需要配置对应的 API Key：

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

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key
```

---

## 三、常见问题

### 3.1 Docker 部署问题

#### Q: 端口被占用怎么办？

A: 修改 `.env` 文件中的端口配置：

```bash
WEB_PORT=8080      # 默认 80
API_PORT=8001      # 默认 8000
MYSQL_PORT=3307    # 默认 3306
REDIS_PORT=6380    # 默认 6379
```

#### Q: 服务启动失败怎么办？

A: 查看日志排查问题：

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs

# 查看特定服务日志
docker logs aigc-platform-api
docker logs aigc-platform-mysql
```

#### Q: 如何清理环境重新部署？

A: 运行清理命令：

```bash
# 停止并删除容器、网络、卷
make clean

# 重新部署
make dev-deploy-docker
```

### 3.2 其他问题

#### Q: 如何修改默认密码？

A: 登录后在个人设置中修改密码。

#### Q: 如何查看 API 文档？

A: 访问 http://localhost:8000/docs 查看 Swagger UI 文档。

#### Q: 如何调试代码？

A:
- Docker 部署：使用 `docker exec -it aigc-platform-api bash` 进入容器
- 代码调试：在 IDE 中配置远程调试或使用 `pdb` 进行调试

#### Q: MySQL 启动超时怎么办？

A:
1. 已优化配置降低内存要求：innodb_buffer_pool_size=256M, max_connections=100
2. 延长等待时间至 120 秒
3. 查看日志：`docker logs aigc-platform-mysql`
4. 检查服务器内存是否足够

#### Q: 服务启动慢怎么办？

A:
1. 确保 Docker 有足够资源
2. 首次启动会构建镜像，需要耐心等待
3. 后续启动会更快
4. 查看服务状态：`make dev-status`

---

## 四、开发建议

### 4.1 推荐开发流程

1. **首次开发**: 使用 Docker 部署快速体验
2. **日常开发**: 使用 Docker 部署方便调试
3. **代码提交**: 确保代码通过测试和 lint 检查

### 4.2 IDE 配置建议

#### VS Code

推荐安装扩展：
- Python
- Pylance
- ESLint
- Vetur
- Docker

#### PyCharm

配置 Python 解释器：
1. 打开 `platform_api` 目录
2. 配置虚拟环境：`platform_api/venv/bin/python`

### 4.3 代码规范

- 后端：遵循 PEP 8 规范
- 前端：遵循 Vue 3 + TypeScript 规范
- 提交前：运行 `npm run lint` 和 `pytest`

---

## 五、快速参考

### Docker 部署命令

```bash
make dev-deploy-docker    # 一键部署
make dev-status          # 查看状态
make dev-logs            # 查看日志
make dev-stop            # 停止服务
make dev-restart         # 重启服务
make clean               # 清理环境
```

### 服务访问地址

- **前端 Web**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 六、下一步

- 查看 [API 文档](api-design.md) 了解接口设计
- 查看 [数据模型](data-model-analysis.md) 了解数据库结构
- 查看 [生产环境部署指南](prod-deploy-guide.md) 了解生产部署
