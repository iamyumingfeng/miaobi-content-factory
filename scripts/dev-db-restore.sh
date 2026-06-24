#!/bin/bash
#
# 妙笔内容工场 - 数据库恢复
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

# 显示帮助
show_help() {
    echo "妙笔内容工场 - 数据库恢复"
    echo ""
    echo "用法: $0 <备份目录>"
    echo ""
    echo "参数:"
    echo "  备份目录            包含备份文件的目录路径"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 backups/20260507_120000"
    echo "  $0 backups/20260507_120000/database.sql"
    echo ""
}

# 检查参数
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

BACKUP_PATH="$1"

# 检查备份文件
if [ -f "$BACKUP_PATH" ]; then
    BACKUP_FILE="$BACKUP_PATH"
    BACKUP_DIR=$(dirname "$BACKUP_PATH")
elif [ -d "$BACKUP_PATH" ]; then
    BACKUP_DIR="$BACKUP_PATH"
    if [ -f "$BACKUP_PATH/database.sql" ]; then
        BACKUP_FILE="$BACKUP_PATH/database.sql"
    elif [ -f "$BACKUP_PATH/all_databases.sql" ]; then
        BACKUP_FILE="$BACKUP_PATH/all_databases.sql"
    else
        print_error "未找到备份文件: $BACKUP_PATH/database.sql 或 $BACKUP_PATH/all_databases.sql"
        exit 1
    fi
else
    print_error "备份路径不存在: $BACKUP_PATH"
    exit 1
fi

print_warning "=========================================="
print_warning "数据库恢复"
print_warning "=========================================="
print_warning "备份文件: $BACKUP_FILE"
print_warning "⚠️  警告：此操作将覆盖现有数据"
print_warning "=========================================="
echo ""

read -p "确认继续? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    print_info "取消操作"
    exit 0
fi

echo ""

# 检查 MySQL 服务
print_step "[1/3] 检查 MySQL 服务..."
if ! docker ps --format "{{.Names}}" | grep -q "miaobi-aigc-factory-mysql"; then
    print_warning "MySQL 服务未运行，尝试启动..."
    docker-compose -f docker/docker-compose.dev.yml up -d mysql
    sleep 10
fi
print_success "MySQL 服务已就绪"

# 恢复数据库
print_step "[2/3] 恢复数据库..."
print_info "恢复文件: $BACKUP_FILE"

if [[ "$BACKUP_FILE" == *"all_databases.sql" ]]; then
    print_info "恢复所有数据库..."
    docker exec -i miaobi-aigc-factory-mysql mysql \
        -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" \
        < "$BACKUP_FILE"
else
    print_info "恢复 aigc_platform 数据库..."
    docker exec -i miaobi-aigc-factory-mysql mysql \
        -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" \
        "${MYSQL_DATABASE:-aigc_platform}" \
        < "$BACKUP_FILE"
fi

print_success "数据库恢复完成"

# 恢复配置文件
print_step "[3/3] 恢复配置文件..."
if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" .env
    print_success ".env 文件已恢复"
else
    print_info "未找到 .env 备份文件"
fi

echo ""
print_success "=========================================="
print_success "数据库恢复完成！"
print_success "=========================================="
echo ""
print_info "建议重启服务: docker-compose -f docker/docker-compose.dev.yml restart"
echo ""