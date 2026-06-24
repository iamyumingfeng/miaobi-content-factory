#!/bin/bash
#
# 妙笔内容工场 - 数据库备份
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
    echo "妙笔内容工场 - 数据库备份"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -o, --output DIR    备份输出目录（默认: backups/）"
    echo "  -a, --all           备份所有数据库"
    echo ""
    echo "示例:"
    echo "  $0                  # 备份 aigc_platform 数据库"
    echo "  $0 -a               # 备份所有数据库"
    echo "  $0 -o ./my-backups  # 备份到指定目录"
    echo ""
}

# 默认配置
OUTPUT_DIR="${BACKUP_DIR:-data/backups}"
BACKUP_ALL=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -a|--all) BACKUP_ALL=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

print_info "=========================================="
print_info "数据库备份"
print_info "=========================================="
print_info "输出目录: $OUTPUT_DIR"
print_info "备份范围: $([ "$BACKUP_ALL" = true ] && echo '所有数据库' || echo 'aigc_platform')"
print_info "=========================================="
echo ""

# 创建备份目录
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$OUTPUT_DIR/$BACKUP_DATE"
mkdir -p "$BACKUP_PATH"

print_step "[1/2] 开始备份..."

# 备份数据库
if [ "$BACKUP_ALL" = true ]; then
    print_info "备份所有数据库..."
    docker exec miaobi-aigc-factory-mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" \
        --all-databases > "$BACKUP_PATH/all_databases.sql" 2>/dev/null
    print_success "所有数据库备份完成: $BACKUP_PATH/all_databases.sql"
else
    print_info "备份 aigc_platform 数据库..."
    docker exec miaobi-aigc-factory-mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" \
        "${MYSQL_DATABASE:-aigc_platform}" > "$BACKUP_PATH/database.sql" 2>/dev/null
    print_success "数据库备份完成: $BACKUP_PATH/database.sql"
fi

# 备份配置文件
print_step "[2/2] 备份配置文件..."
if [ -f .env ]; then
    cp .env "$BACKUP_PATH/.env"
    print_success ".env 文件已备份"
fi

# 备份文件大小
BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
print_info "备份大小: $BACKUP_SIZE"

echo ""
print_success "=========================================="
print_success "数据库备份完成！"
print_success "=========================================="
echo ""
print_info "备份文件位置: $BACKUP_PATH/"
echo ""
print_info "恢复数据库:"
echo "  ./scripts/dev-db-restore.sh $BACKUP_PATH"
echo ""