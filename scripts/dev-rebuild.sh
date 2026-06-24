#!/bin/bash
#
# 妙笔内容工场 - 一键重新构建镜像
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
    echo "妙笔内容工场 - 一键重新构建镜像"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -n, --no-cache      无缓存重新构建（完全重建）"
    echo "  -s, --service       重新构建特定服务（api|web|all）"
    echo "  -v, --verbose       显示详细输出"
    echo ""
    echo "示例:"
    echo "  $0                  # 重新构建所有镜像"
    echo "  $0 -n               # 无缓存重新构建所有镜像"
    echo "  $0 -s api           # 重新构建 API 镜像"
    echo "  $0 -s web           # 重新构建 Web 镜像"
    echo ""
}

# 默认配置
NO_CACHE=false
SERVICE="all"
VERBOSE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -n|--no-cache) NO_CACHE=true; shift ;;
        -s|--service) SERVICE="$2"; shift 2 ;;
        -v|--verbose) VERBOSE=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

print_info "=========================================="
print_info "重新构建镜像"
print_info "=========================================="
print_info "无缓存: $([ "$NO_CACHE" = true ] && echo '是' || echo '否')"
print_info "服务: $SERVICE"
print_info "=========================================="
echo ""

# ========================================
# 强制清理所有相关容器
# ========================================
force_cleanup_containers() {
    print_step "[1/4] 强制清理旧容器..."

    # 停止并删除所有相关容器
    local containers=(
        "miaobi-aigc-factory-api"
        "miaobi-aigc-factory-web"
        "miaobi-aigc-factory-mysql"
        "miaobi-aigc-factory-redis"
        "miaobi-aigc-factory-celery-worker"
        "miaobi-aigc-factory-celery-beat"
    )

    local cleaned=false
    for container in "${containers[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            print_info "清理容器: ${container}"
            docker stop "${container}" 2>/dev/null || true
            docker rm -f "${container}" 2>/dev/null || true
            cleaned=true
        fi
    done

    # 清理相关网络
    if docker network ls --format "{{.Name}}" | grep -q "miaobi-aigc-factory-network"; then
        print_info "清理网络: miaobi-aigc-factory-network"
        docker network rm miaobi-aigc-factory-network 2>/dev/null || true
        cleaned=true
    fi

    if [ "$cleaned" = true ]; then
        print_success "旧容器和网络清理完成"
    else
        print_info "没有发现需要清理的旧容器"
    fi
}

# 强制清理
force_cleanup_containers

# 重新构建镜像
print_step "[2/4] 重新构建镜像..."

BUILD_CMD="$DOCKER_COMPOSE -f docker/docker-compose.dev.yml build"

if [ "$NO_CACHE" = true ]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

if [ "$SERVICE" != "all" ]; then
    BUILD_CMD="$BUILD_CMD $SERVICE"
fi

if [ "$VERBOSE" = true ]; then
    eval $BUILD_CMD
else
    eval $BUILD_CMD 2>&1 | grep -E "(Building|Step|Successfully|ERROR)" || true
fi

print_success "镜像构建完成"

# 启动服务
print_step "[3/4] 启动服务..."
$DOCKER_COMPOSE -f docker/docker-compose.dev.yml up -d
print_success "服务已启动"

# 等待服务就绪
print_step "[4/4] 等待服务就绪..."
print_info "这可能需要 30-60 秒..."
sleep 10

# 健康检查
print_info "服务状态:"
$DOCKER_COMPOSE -f docker/docker-compose.dev.yml ps

echo ""
print_success "=========================================="
print_success "镜像重新构建完成！"
print_success "=========================================="
echo ""
print_info "访问地址:"
echo "  前端: http://localhost"
echo "  后端: http://localhost:8000"
echo "  文档: http://localhost:8000/docs"
echo ""
