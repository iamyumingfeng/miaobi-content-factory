# .env 配置详细说明

> 妙笔内容工场 - 环境变量配置完全指南

## 目录
- [快速开始](#快速开始)
- [配置分类说明](#配置分类说明)
- [每项配置详解](#每项配置详解)
- [推荐配置](#推荐配置)

---

## 快速开始

### 最小配置（本地开发测试用）

对于本地开发测试，**只需要修改以下几项**，其他都可以保持默认：

```env
# 1. 修改 SECRET_KEY（必须，安全考虑）
SECRET_KEY=your-random-secret-key-here-change-this

# 2. 如果想改数据库密码（可选，建议修改）
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_secure_root_password
REDIS_PASSWORD=your_redis_password

# 3. COS配置保持原样即可（不需要配置）
COS_SECRET_ID=your-cos-secret-id      # 保持不变
COS_SECRET_KEY=your-cos-secret-key    # 保持不变
COS_REGION=ap-guangzhou                # 保持不变
COS_BUCKET=your-bucket-name            # 保持不变

# 4. AI模型配置保持原样（开发测试不需要）
BAILIAN_API_KEY=your-bailian-api-key  # 保持不变
# ... 其他模型配置保持不变
```

### ✅ 验证配置是否就绪

配置完成后，运行：

```bash
# 1. 验证Docker配置
./scripts/docker-verify.sh

# 2. 启动服务
make dev

# 3. 查看服务状态
make status
```

---

## 配置分类说明

| 配置类型 | 是否必须修改 | 说明 |
|---------|------------|------|
| **通用配置** | 否 | 开发模式保持默认即可 |
| **数据库配置** | 推荐 | 建议修改密码，其他保持默认 |
| **Redis配置** | 推荐 | 建议修改密码，其他保持默认 |
| **后端API配置** | 部分 | 必须修改 SECRET_KEY |
| **前端Web配置** | 否 | 开发模式保持默认 |
| **Celery配置** | 否 | 根据服务器性能调整 |
| **COS配置** | ❌ 不需要 | 本地开发不需要配置 |
| **AI模型配置** | 可选 | 真正使用AI功能时才需要 |

---

## 每项配置详解

### 一、通用配置

```env
# 运行模式: development, production
ENVIRONMENT=development
DEBUG=true
```

**说明：**
- `ENVIRONMENT=development`：开发模式，显示详细错误信息
- `ENVIRONMENT=production`：生产模式，隐藏错误详情
- `DEBUG=true`：启用调试模式
- **本地开发：保持默认即可**

---

### 二、数据库配置 - MySQL

```env
MYSQL_HOST=mysql              # Docker服务名，不需要改
MYSQL_PORT=3306               # MySQL默认端口，不需要改
MYSQL_DATABASE=aigc_platform  # 数据库名，不需要改
MYSQL_USER=aigc_user          # 数据库用户名，不需要改
MYSQL_PASSWORD=aigc_password123      # ⚠️ 建议修改
MYSQL_ROOT_PASSWORD=rootpassword123  # ⚠️ 建议修改
```

**说明：**
- `MYSQL_HOST=mysql`：Docker内部服务名，在Docker网络中使用
- `MYSQL_PORT=3306`：容器内部端口，不需要改
- `MYSQL_PASSWORD`：普通用户密码，**建议修改为安全密码**
- `MYSQL_ROOT_PASSWORD`：root用户密码，**建议修改为安全密码**

**修改建议：**
```env
MYSQL_PASSWORD=my_secure_db_pass_2024
MYSQL_ROOT_PASSWORD=my_secure_root_pass_2024
```

---

### 三、缓存配置 - Redis

```env
REDIS_HOST=redis              # Docker服务名，不需要改
REDIS_PORT=6379               # Redis默认端口，不需要改
REDIS_PASSWORD=redis_password123  # ⚠️ 建议修改
REDIS_DB=0                    # Redis数据库编号，不需要改
```

**说明：**
- `REDIS_HOST=redis`：Docker内部服务名
- `REDIS_PASSWORD`：Redis密码，**建议修改**

**修改建议：**
```env
REDIS_PASSWORD=my_secure_redis_pass_2024
```

---

### 四、后端API配置

```env
API_PORT=8000                          # 后端端口，不需要改
API_TARGET=development                 # 开发模式，不需要改
SECRET_KEY=your-super-secret-key-change-in-production-1234567890  # ⚠️ 必须修改
JWT_ALGORITHM=HS256                    # JWT算法，不需要改
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30     # Access Token过期时间，不需要改
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7         # Refresh Token过期时间，不需要改

# CORS配置 (JSON数组格式)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

**说明：**
- `SECRET_KEY`：**必须修改**，用于JWT签名和加密，生产环境必须使用强随机密钥
- `CORS_ORIGINS`：允许跨域访问的前端地址，开发模式保持默认即可

**如何生成安全的 SECRET_KEY：**

```bash
# 方法1：使用Python生成
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 方法2：使用OpenSSL生成
openssl rand -base64 64

# 方法3：使用在线工具生成（不推荐生产环境）
```

**修改示例：**
```env
SECRET_KEY=k8xQZ7mP2wR9tN5yB3vE6cX4dV8fG1hJ2kL3nM5pQ7rS9tU1vW3xY5zA7bC9d
```

---

### 五、前端Web配置

```env
WEB_PORT=8080                          # 前端端口，不需要改
WEB_TARGET=development                 # 开发模式，不需要改
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**说明：**
- `WEB_PORT=8080`：前端访问端口，浏览器访问 http://localhost:8080
- `VITE_API_BASE_URL`：前端调用后端API的地址
- **本地开发：保持默认即可**

---

### 六、Celery配置

```env
CELERY_CONCURRENCY=4          # Celery并发数，根据CPU调整
FLOWER_PORT=5555              # Flower监控端口，不需要改
```

**说明：**
- `CELERY_CONCURRENCY=4`：同时运行的Celery Worker数量
  - 2核CPU：建议设为 2
  - 4核CPU：建议设为 4
  - 8核CPU：建议设为 6-8
- **本地开发：保持默认即可**

---

### 七、可选服务配置

```env
PHPMYADMIN_PORT=8081
```

**说明：**
- phpMyAdmin访问端口：http://localhost:8081
- **本地开发：保持默认即可**

---

### 八、对象存储配置 - 腾讯云COS

```env
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_REGION=ap-guangzhou
COS_BUCKET=your-bucket-name
COS_MOUNT_PATH=/app/cos
```

**⚠️ 重要说明：**
- **本地开发测试：完全不需要配置，保持原样即可**
- 项目使用Docker volume挂载本地目录模拟COS
- 只有真正部署到腾讯云服务器时才需要配置

**保持原样即可，不要修改：**
```env
COS_SECRET_ID=your-cos-secret-id      # ✅ 保持不变
COS_SECRET_KEY=your-cos-secret-key    # ✅ 保持不变
COS_REGION=ap-guangzhou                # ✅ 保持不变
COS_BUCKET=your-bucket-name            # ✅ 保持不变
```

---

### 九、AI模型配置

系统支持8个AI模型平台，分为两种认证方式：

#### 标准API Key认证（6个平台）

```env
# 阿里云百炼
BAILIAN_API_KEY=your-bailian-api-key
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com

# 火山引擎
VOLCANO_API_KEY=your-volcano-api-key
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com

# AutoGLM
AUTOGLM_API_KEY=your-autoglm-api-key

# 月之暗面
MOONSHOT_API_KEY=your-moonshot-api-key
MOONSHOT_BASE_URL=https://api.moonshot.cn

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 灵牙AI
LINGYAAI_API_KEY=your-lingyaai-api-key
```

#### AccessKey + SecretKey认证（2个平台）

```env
# 即梦（需要AccessKey和SecretKey）
JIMENG_ACCESS_KEY=your-jimeng-access-key
JIMENG_SECRET_KEY=your-jimeng-secret-key

# 可灵（需要AccessKey和SecretKey）
KLING_ACCESS_KEY=your-kling-access-key
KLING_SECRET_KEY=your-kling-secret-key
```

**说明：**
- **本地开发测试：完全不需要配置，保持原样即可**
- 只有真正使用AI生成功能时才需要配置对应平台的密钥
- 可以只配置其中一个或几个平台
- 即梦和可灵使用双密钥认证方式（AccessKey + SecretKey）

**保持原样即可：**
```env
BAILIAN_API_KEY=your-bailian-api-key      # ✅ 保持不变
VOLCANO_API_KEY=your-volcano-api-key      # ✅ 保持不变
# ... 其他都保持不变
```

---

## 推荐配置

### 本地开发测试推荐配置（最简版）

```env
# ========================================
# 通用配置
# ========================================
ENVIRONMENT=development
DEBUG=true

# ========================================
# 数据库配置 - MySQL
# ========================================
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=aigc_platform
MYSQL_USER=aigc_user
MYSQL_PASSWORD=aigc_password123          # 可选：修改为你喜欢的密码
MYSQL_ROOT_PASSWORD=rootpassword123      # 可选：修改为你喜欢的密码

# ========================================
# 缓存配置 - Redis
# ========================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password123          # 可选：修改为你喜欢的密码
REDIS_DB=0

# ========================================
# 后端API配置
# ========================================
API_PORT=8000
API_TARGET=development
SECRET_KEY=change-this-to-a-random-key-32-chars-minimum  # ⚠️ 必须修改
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# ========================================
# 前端Web配置
# ========================================
WEB_PORT=8080
WEB_TARGET=development
VITE_API_BASE_URL=http://localhost:8000/api/v1

# ========================================
# Celery配置
# ========================================
CELERY_CONCURRENCY=4
FLOWER_PORT=5555

# ========================================
# 可选服务配置
# ========================================
PHPMYADMIN_PORT=8081

# ========================================
# 对象存储配置 - 腾讯云COS（不需要配置）
# ========================================
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_REGION=ap-guangzhou
COS_BUCKET=your-bucket-name
COS_MOUNT_PATH=/app/cos

# ========================================
# AI模型配置（不需要配置）
# ========================================
# 标准API Key认证
BAILIAN_API_KEY=your-bailian-api-key
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com
VOLCANO_API_KEY=your-volcano-api-key
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com
AUTOGLM_API_KEY=your-autoglm-api-key
MOONSHOT_API_KEY=your-moonshot-api-key
MOONSHOT_BASE_URL=https://api.moonshot.cn
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
LINGYAAI_API_KEY=your-lingyaai-api-key

# AccessKey + SecretKey认证
JIMENG_ACCESS_KEY=your-jimeng-access-key
JIMENG_SECRET_KEY=your-jimeng-secret-key
KLING_ACCESS_KEY=your-kling-access-key
KLING_SECRET_KEY=your-kling-secret-key
```

---

## 启动验证

配置完成后，按以下步骤验证：

```bash
# 1. 验证Docker配置
./scripts/docker-verify.sh

# 2. 启动开发环境
make dev

# 3. 查看服务状态
make status

# 4. 查看日志（可选）
make logs
```

---

## 服务访问

启动成功后，可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端Web | http://localhost:8080 | Web管理后台 |
| 后端API | http://localhost:8000 | API服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| Flower监控 | http://localhost:5555 | Celery任务监控 |
| phpMyAdmin | http://localhost:8081 | 数据库管理（可选） |

---

## 常见问题

### Q1: 我需要配置COS吗？
**A:** 不需要。本地开发使用Docker volume挂载本地目录，完全不需要配置COS。

### Q2: 我需要配置AI模型API Key吗？
**A:** 不需要。只有真正使用AI生成功能时才需要配置，开发测试可以先不配。

### Q3: SECRET_KEY怎么生成？
**A:** 运行 `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` 生成一个随机密钥。

### Q4: 数据库密码必须改吗？
**A:** 本地开发不是必须的，但建议修改以养成好习惯。生产环境必须修改。

### Q5: 可以用其他端口吗？
**A:** 可以，但需要同时修改docker-compose.yml中的端口映射。建议先用默认端口测试。

---

## 下一步

配置完成后：

1. 运行 `make dev` 启动开发环境
2. 访问 http://localhost:8080 查看前端
3. 访问 http://localhost:8000/docs 查看API文档
4. 查看 [docker-guide.md](./docker-guide.md) 了解更多Docker使用方法
