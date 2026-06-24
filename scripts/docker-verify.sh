#!/bin/bash
# ========================================
# Docker配置验证脚本
# ========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}妙笔内容工场 - Docker配置验证${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查Docker
echo -e "${YELLOW}[1/6] 检查 Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker 已安装: $(docker --version)${NC}"
else
    echo -e "${RED}✗ Docker 未安装${NC}"
fi

# 检查Docker Compose
echo -e "${YELLOW}[2/6] 检查 Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose 已安装: $(docker-compose --version)${NC}"
elif docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose (V2 已安装${NC}"
else
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
fi

# 检查配置文件
echo -e "${YELLOW}[3/6] 检查配置文件...${NC}"
files=(
    "docker/docker-compose.yml"
    "docker/docker-compose.dev.yml"
    "docker/docker-compose.test.yml"
    "platform_api/Dockerfile"
    "platform_web/Dockerfile"
    ".env.example"
    "Makefile"
    "docs/docker-guide.md"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file (缺失)${NC}"
        all_exist=false
    fi
done

# 检查目录结构
echo -e "${YELLOW}[4/6] 检查目录结构...${NC}"
dirs=(
    "data/cos"
    "data/mysql"
    "platform_web/conf.d"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir/${NC}"
    else
        echo -e "${YELLOW}○ $dir/ (将自动创建)${NC}"
        mkdir -p "$dir"
    fi
done

# 检查环境配置
echo -e "${YELLOW}[5/6] 检查环境配置...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
else
    echo -e "${YELLOW}○ .env 文件不存在，将从 .env.example 复制${NC}"
    cp .env.example .env
fi

# Nginx配置
echo -e "${YELLOW}[6/6] 检查Nginx配置...${NC}"
if [ -f "platform_web/nginx.conf" ] && [ -f "platform_web/conf.d/default.conf" ]; then
    echo -e "${GREEN}✓ Nginx配置已就绪${NC}"
else
    echo -e "${YELLOW}○ Nginx配置文件缺失${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
if [ "$all_exist" = true ]; then
    echo -e "${GREEN}✓ 所有配置文件已就绪!${NC}"
else
    echo -e "${YELLOW}△ 部分文件缺失，请检查${NC}"
fi
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "  1. 查看并编辑 .env 文件（如需要）"
echo "  2. 运行 'make dev' 启动开发环境"
echo "  3. 运行 'make help' 查看所有可用命令"
echo ""
echo -e "${YELLOW}服务访问:${NC}"
echo "  - 前端Web:  http://localhost:8080"
echo "  - 后端API:  http://localhost:8000"
echo "  - API文档:  http://localhost:8000/docs"
echo "  - Flower:   http://localhost:5555"
echo ""
