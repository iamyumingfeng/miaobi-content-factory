#!/bin/bash
#
# 妙笔内容工场 - 资源监控
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
    echo "妙笔内容工场 - 资源监控"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -r, --refresh N     刷新间隔（秒，默认: 2）"
    echo "  -o, --once          只显示一次"
    echo "  -s, --service       监控特定服务（api|web|mysql|redis|celery）"
    echo ""
    echo "示例:"
    echo "  $0                  # 持续监控所有服务"
    echo "  $0 -o               # 显示一次"
    echo "  $0 -s api           # 监控 API 服务"
    echo "  $0 -r 5             # 每 5 秒刷新一次"
    echo ""
}

# 默认配置
REFRESH=2
ONCE=false
SERVICE="all"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -r|--refresh) REFRESH="$2"; shift 2 ;;
        -o|--once) ONCE=true; shift ;;
        -s|--service) SERVICE="$2"; shift 2 ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

# 监控函数
monitor() {
    while true; do
        clear
        print_info "=========================================="
        print_info "资源监控 - $(date '+%Y-%m-%d %H:%M:%S')"
        print_info "=========================================="
        echo ""
        
        if [ "$SERVICE" = "all" ]; then
            # 显示所有容器资源使用
            print_step "容器资源使用"
            echo ""
            docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" | grep miaobi-aigc-factory
            echo ""
            
            # 显示磁盘使用
            print_step "磁盘使用"
            echo ""
            df -h . | awk 'NR==1 || /^\// {printf "%-20s %10s %10s %10s %10s\n", $1, $2, $3, $4, $5}'
            echo ""
            
            # 显示内存使用 - 兼容 macOS 和 Linux
            print_step "系统内存"
            echo ""
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS: 使用 vm_stat 和 sysctl 获取内存信息
                MEM_TOTAL=$(sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1024/1024/1024)}')
                MEM_FREE=$(vm_stat 2>/dev/null | awk '/Pages free:/ {print int($3*4096/1024/1024/1024)}')
                MEM_USED=$((MEM_TOTAL - MEM_FREE))
                printf "%-10s %10s %10s %10s\n" " " "total" "used" "free"
                printf "%-10s %8sGB %8sGB %8sGB\n" "Mem:" "$MEM_TOTAL" "$MEM_USED" "$MEM_FREE"
            else
                # Linux: 使用 free 命令
                free -h 2>/dev/null | awk 'NR==1 || /^Mem/ {printf "%-10s %10s %10s %10s\n", $1, $2, $3, $4}' || echo "  无法获取内存信息"
            fi
            echo ""
            
            # 显示 Celery 队列
            print_step "Celery 队列"
            echo ""
            if docker ps --format "{{.Names}}" | grep -q "miaobi-aigc-factory-redis"; then
                QUEUE_LEN=$(docker exec miaobi-aigc-factory-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" LLEN celery 2>/dev/null || echo "N/A")
                echo "  队列长度: $QUEUE_LEN"
            else
                echo "  Redis 服务未运行"
            fi
            echo ""
        else
            # 显示特定服务资源使用
            print_step "$SERVICE 服务资源使用"
            echo ""
            docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" "miaobi-aigc-factory-$SERVICE"
            echo ""
        fi
        
        # 显示进程数
        print_step "容器进程数"
        echo ""
        docker ps --format "{{.Names}}" | grep miaobi-aigc-factory | while read container; do
            count=$(docker exec "$container" ps aux 2>/dev/null | wc -l || echo "N/A")
            printf "  %-30s %s\n" "$container" "$count"
        done
        echo ""
        
        if [ "$ONCE" = true ]; then
            break
        fi
        
        sleep $REFRESH
    done
}

# 检查 Docker 是否运行
if ! docker ps > /dev/null 2>&1; then
    print_error "Docker 未运行或无权限访问"
    exit 1
fi

monitor