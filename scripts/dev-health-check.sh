#!/bin/bash
#
# 妙笔内容工场 - 一键健康检查
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

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 打印消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${CYAN}==>${NC} $1"; }

print_info "=========================================="
print_info "服务健康检查"
print_info "=========================================="
echo ""

# 检查容器状态
print_step "容器状态检查"
echo ""
docker-compose -f docker/docker-compose.dev.yml ps 2>/dev/null || print_warning "未发现运行中的服务"
echo ""

# 检查 API
print_step "API 服务检查"
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    print_success "✓ API 服务正常"
    API_STATUS="✓"
else
    print_error "✗ API 服务异常"
    API_STATUS="✗"
fi

# 检查 Web
print_step "Web 服务检查"
if curl -sf http://localhost:80 > /dev/null 2>&1; then
    print_success "✓ Web 服务正常"
    WEB_STATUS="✓"
else
    print_warning "✗ Web 服务异常"
    WEB_STATUS="✗"
fi

# 检查 MySQL
print_step "MySQL 服务检查"
if docker exec miaobi-aigc-factory-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" --silent 2>/dev/null; then
    print_success "✓ MySQL 服务正常"
    MYSQL_STATUS="✓"
else
    print_error "✗ MySQL 服务异常"
    MYSQL_STATUS="✗"
fi

# 检查 Redis
print_step "Redis 服务检查"
if docker exec miaobi-aigc-factory-redis redis-cli -a "${REDIS_PASSWORD:-redis_password123}" ping 2>/dev/null | grep -q "PONG"; then
    print_success "✓ Redis 服务正常"
    REDIS_STATUS="✓"
else
    print_error "✗ Redis 服务异常"
    REDIS_STATUS="✗"
fi

# 检查 Celery
print_step "Celery 服务检查"
if docker ps --format "{{.Names}}" | grep -q "miaobi-aigc-factory-celery-worker"; then
    print_success "✓ Celery Worker 运行中"
    CELERY_STATUS="✓"
else
    print_warning "✗ Celery Worker 未运行"
    CELERY_STATUS="✗"
fi

echo ""
print_info "=========================================="
print_info "健康检查结果"
print_info "=========================================="
echo ""
echo "API:            $API_STATUS"
echo "Web:            $WEB_STATUS"
echo "MySQL:          $MYSQL_STATUS"
echo "Redis:          $REDIS_STATUS"
echo "Celery Worker:  $CELERY_STATUS"
echo ""

# 资源使用情况
print_step "资源使用情况"
echo ""
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep miaobi-aigc-factory
echo ""

# 磁盘使用情况
print_step "磁盘使用情况"
echo ""
df -h . | awk 'NR==1 || /^\// {print}'
echo ""

print_success "=========================================="
print_success "健康检查完成！"
print_success "=========================================="
echo ""
