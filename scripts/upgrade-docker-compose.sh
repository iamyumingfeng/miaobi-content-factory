#!/bin/bash
#
# 妙笔内容工场 - 升级 Docker Compose 到 v2.x
#
# Docker Compose v2.x 支持 `name` 属性，用于区分多个系统部署
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "Docker Compose 升级脚本"
echo "=========================================="
echo ""

# 检查当前版本
print_info "检查当前 Docker Compose 版本..."
CURRENT_VERSION=$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
print_info "当前版本: $CURRENT_VERSION"

# 检查是否已经是 v2.x
if docker compose version 2>/dev/null | grep -q "v2"; then
    print_success "Docker Compose v2 已安装！"
    docker compose version
    print_info "您可以直接使用 'docker compose' 命令（注意没有中间的连字符）"
    exit 0
fi

echo ""
print_warning "Docker Compose v2 未安装，需要升级"
print_info "Docker Compose v2 是 Docker CLI 的插件，集成在 Docker 中"
echo ""

# 方法1: 安装 Docker Compose v2 作为 Docker 插件（推荐）
print_info "方法1: 安装 Docker Compose v2 插件（推荐）"
echo ""

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

print_info "检测到操作系统: $OS"

case $OS in
    ubuntu|debian)
        print_info "Ubuntu/Debian 系统，使用 apt 安装..."
        print_info "执行以下命令："
        echo ""
        echo "  # 更新 Docker 到最新版本（包含 Compose v2）"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
        echo ""
        echo "  # 或者仅安装 compose 插件"
        echo "  sudo apt-get install -y docker-compose-plugin"
        echo ""
        ;;
    centos|rhel|fedora)
        print_info "CentOS/RHEL/Fedora 系统，使用 yum/dnf 安装..."
        print_info "执行以下命令："
        echo ""
        echo "  # 更新 Docker 到最新版本（包含 Compose v2）"
        echo "  sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
        echo ""
        ;;
    *)
        print_warning "未知系统，请手动安装"
        ;;
esac

echo ""
print_info "方法2: 手动下载安装 Docker Compose v2"
echo ""
echo "  # 下载最新版本"
echo "  DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}"
echo "  mkdir -p \$DOCKER_CONFIG/cli-plugins"
echo "  curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o \$DOCKER_CONFIG/cli-plugins/docker-compose"
echo "  chmod +x \$DOCKER_CONFIG/cli-plugins/docker-compose"
echo ""
echo "  # 验证安装"
echo "  docker compose version"
echo ""

print_info "安装完成后，使用 'docker compose' 命令（注意没有连字符）"
print_info "例如: docker compose up -d（而不是 docker-compose up -d）"
echo ""

# 检查是否可以自动安装
read -p "是否尝试自动安装 Docker Compose v2? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        print_info "开始安装..."
        sudo apt-get update
        sudo apt-get install -y docker-compose-plugin
        print_success "安装完成！"
        docker compose version
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        print_info "开始安装..."
        sudo yum install -y docker-compose-plugin
        print_success "安装完成！"
        docker compose version
    else
        print_warning "无法自动安装，请按照上面的方法2手动安装"
    fi
fi

echo ""
print_info "=========================================="
print_info "升级完成后，部署命令需要改为："
print_info "=========================================="
echo ""
echo "  # 旧命令（v1.x）"
echo "  docker-compose -f docker/docker-compose.yml up -d"
echo ""
echo "  # 新命令（v2.x）"
echo "  docker compose -f docker/docker-compose.yml up -d"
echo ""
print_info "或者修改 Makefile 和部署脚本中的命令"