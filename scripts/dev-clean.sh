#!/bin/bash
#
# 妙笔内容工场 - 一键清理环境
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 打印消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${CYAN}==>${NC} $1"; }

# 显示帮助
show_help() {
    echo "妙笔内容工场 - 一键清理环境"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -a, --all           清理所有资源（容器、网络、镜像、卷）"
    echo "  -v, --volumes       清理卷（会删除数据，危险操作）"
    echo "  -i, --images        清理镜像"
    echo "  -p, --prune         清理系统未使用资源"
    echo ""
    echo "示例:"
    echo "  $0                  # 停止并删除容器和网络"
    echo "  $0 -a               # 清理所有资源（包括数据）"
    echo "  $0 -i               # 清理容器、网络和镜像"
    echo "  $0 -p               # 清理系统未使用资源"
    echo ""
}

# 默认配置
CLEAN_ALL=false
CLEAN_VOLUMES=false
CLEAN_IMAGES=false
CLEAN_PRUNE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -a|--all) CLEAN_ALL=true; shift ;;
        -v|--volumes) CLEAN_VOLUMES=true; shift ;;
        -i|--images) CLEAN_IMAGES=true; shift ;;
        -p|--prune) CLEAN_PRUNE=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

print_warning "=========================================="
print_warning "清理环境"
print_warning "=========================================="
print_warning "此操作将停止并删除容器"
if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
    print_error "⚠️  警告：将删除所有数据（包括数据库）"
fi
print_warning "=========================================="
echo ""

read -p "确认继续? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    print_info "取消操作"
    exit 0
fi

echo ""

# 停止并删除容器和网络
print_step "[1/4] 停止并删除容器..."
$DOCKER_COMPOSE -f docker/docker-compose.dev.yml down --remove-orphans
print_success "容器已停止并删除"

# 清理卷
if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
    print_step "[2/4] 删除卷..."
    docker volume ls | grep miaobi-aigc-factory | awk '{print $2}' | xargs -r docker volume rm
    print_success "卷已删除"
else
    print_info "[2/4] 跳过卷删除"
fi

# 清理镜像
if [ "$CLEAN_IMAGES" = true ] || [ "$CLEAN_ALL" = true ]; then
    print_step "[3/4] 删除镜像..."
    docker images | grep miaobi-aigc-factory | awk '{print $3}' | xargs -r docker rmi -f
    print_success "镜像已删除"
else
    print_info "[3/4] 跳过镜像删除"
fi

# 清理系统未使用资源
if [ "$CLEAN_PRUNE" = true ]; then
    print_step "[4/4] 清理系统未使用资源..."
    docker system prune -f
    print_success "系统清理完成"
else
    print_info "[4/4] 跳过系统清理"
fi

echo ""
print_success "=========================================="
print_success "环境清理完成！"
print_success "=========================================="
echo ""

if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
    print_warning "数据已删除，重新部署时需要初始化数据"
    print_info "重新部署: make dev-deploy-docker"
else
    print_info "重新部署: make dev-deploy-docker"
fi

echo ""
