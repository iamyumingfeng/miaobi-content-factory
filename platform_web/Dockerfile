# ========================================
# 妙笔内容工场 - 前端Web Dockerfile
# ========================================

# 第一阶段：构建阶段
FROM node:20-slim AS builder

# 设置工作目录
WORKDIR /app

# 设置npm镜像源（可选，提高构建速度）
ENV npm_config_registry=https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 第二阶段：生产阶段 - 使用Nginx
FROM nginx:alpine AS production

# 设置标签
LABEL maintainer="AIGC Platform Team"
LABEL description="Miaobi Content Factory - Frontend"

# 设置时区
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]

# 第三阶段：开发阶段
FROM node:20-slim AS development

# 设置工作目录
WORKDIR /app

# 设置npm镜像源
ENV npm_config_registry=https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 暴露端口（Vite默认端口）
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# 启动开发服务器
CMD ["npm", "run", "dev"]
