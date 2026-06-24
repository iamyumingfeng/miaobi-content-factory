# ========================================
# 妙笔内容工场 - 后端API Dockerfile
# ========================================

# 使用Docker官方镜像
FROM python:3.11-slim-bookworm AS base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

# 配置国内镜像源（解决网络连接问题）
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|http://security.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从base阶段构建，用于开发
FROM base AS development

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖 - 添加 --no-deps 并使用 --upgrade 避免哈希冲突
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 开发环境启动命令
CMD ["./scripts/start.sh", "development"]

# 从base阶段构建，用于生产
FROM base AS production

# 创建非root用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖 - 添加 --no-deps 并使用 --upgrade 避免哈希冲突
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY --chown=appuser:appgroup . .

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 生产环境启动命令
CMD ["./scripts/start.sh", "production"]
