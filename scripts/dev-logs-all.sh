#!/bin/bash
#
# 妙笔内容工场 - 一键查看所有日志
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 打印消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${CYAN}==>${NC} $1"; }

# 显示帮助
show_help() {
    echo "妙笔内容工场 - 一键查看所有日志"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -n, --lines N       显示最近 N 行日志（默认: 100）"
    echo "  -s, --service       查看特定服务日志（api|web|mysql|redis|celery）"
    echo "  -f, --follow        实时跟踪日志"
    echo ""
    echo "示例:"
    echo "  $0                  # 查看所有服务最近 100 行日志"
    echo "  $0 -n 500           # 查看所有服务最近 500 行日志"
    echo "  $0 -s api           # 查看 API 服务日志"
    echo "  $0 -f               # 实时跟踪所有日志"
    echo ""
}

# 默认配置
LINES=100
SERVICE="all"
FOLLOW=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -n|--lines) LINES="$2"; shift 2 ;;
        -s|--service) SERVICE="$2"; shift 2 ;;
        -f|--follow) FOLLOW=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

# 查看特定服务日志
if [ "$SERVICE" != "all" ]; then
    if [ "$FOLLOW" = true ]; then
        docker logs "miaobi-aigc-factory-$SERVICE" -f --tail $LINES
    else
        docker logs "miaobi-aigc-factory-$SERVICE" --tail $LINES
    fi
    exit 0
fi

# 查看所有服务日志
print_info "=========================================="
print_info "查看所有服务日志"
print_info "=========================================="
print_info "显示最近 $LINES 行"
print_info "=========================================="
echo ""

if [ "$FOLLOW" = true ]; then
    print_info "实时跟踪所有日志..."
    docker-compose -f docker/docker-compose.dev.yml logs -f --tail $LINES
else
    # API 日志
    print_step "=== API 日志 ==="
    docker logs miaobi-aigc-factory-api --tail $LINES 2>&1 | tail -20
    echo ""
    
    # Web 日志
    print_step "=== Web 日志 ==="
    docker logs miaobi-aigc-factory-web --tail $LINES 2>&1 | tail -20
    echo ""
    
    # MySQL 日志
    print_step "=== MySQL 日志 ==="
    docker logs miaobi-aigc-factory-mysql --tail $LINES 2>&1 | tail -20
    echo ""
    
    # Redis 日志
    print_step "=== Redis 日志 ==="
    docker logs miaobi-aigc-factory-redis --tail $LINES 2>&1 | tail -10
    echo ""
    
    # Celery Worker 日志
    print_step "=== Celery Worker 日志 ==="
    docker logs miaobi-aigc-factory-celery-worker --tail $LINES 2>&1 | tail -20
    echo ""
    
    # Celery Beat 日志
    print_step "=== Celery Beat 日志 ==="
    docker logs miaobi-aigc-factory-celery-beat --tail $LINES 2>&1 | tail -10
    echo ""
    
    print_success "=========================================="
    print_success "日志查看完成！"
    print_success "=========================================="
    echo ""
    print_info "查看完整日志:"
    echo "  ./scripts/dev-logs-all.sh -n 500"
    echo "  ./scripts/dev-logs-all.sh -s api -f"
    echo ""
fi