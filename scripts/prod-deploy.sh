#!/bin/bash
#
# 妙笔内容工场 - 生产环境部署脚本
# 支持一键部署和一键升级
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

# 检测 Docker Compose 命令（v1 或 v2）
detect_docker_compose() {
    if docker compose version &>/dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose &>/dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        echo -e "${RED}[ERROR]${NC} Docker Compose 未安装"
        echo ""
        echo "请运行以下脚本安装："
        echo "  ./scripts/upgrade-docker-compose.sh"
        exit 1
    fi
    export DOCKER_COMPOSE
}

detect_docker_compose

# 打印消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${CYAN}==>${NC} $1"; }

# 显示帮助
show_help() {
    echo "妙笔内容工场 - 生产环境部署脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  deploy              首次部署（初始化数据）"
    echo "  upgrade             升级部署（保留数据）"
    echo "  rollback            回滚到上一版本"
    echo "  backup              手动备份数据"
    echo "  status              查看服务状态"
    echo "  logs                查看服务日志"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -n, --no-backup     升级时不备份（危险）"
    echo "  -v, --verbose       显示详细输出"
    echo "  --skip-pull         跳过代码拉取"
    echo ""
    echo "示例:"
    echo "  $0 deploy           # 首次部署"
    echo "  $0 upgrade          # 升级部署"
    echo "  $0 rollback         # 回滚版本"
    echo "  $0 backup           # 手动备份"
    echo ""
}

# 默认配置
COMMAND=""
DO_BACKUP=true
VERBOSE=false
SKIP_PULL=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        deploy|upgrade|rollback|backup|status|logs) COMMAND="$1"; shift ;;
        -n|--no-backup) DO_BACKUP=false; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        --skip-pull) SKIP_PULL=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

# 验证命令
if [ -z "$COMMAND" ]; then
    print_error "请指定命令"
    show_help
    exit 1
fi

# ========================================
# 检查环境配置
# ========================================
check_env_config() {
    print_step "检查环境配置..."
    
    if [ ! -f .env ]; then
        print_error ".env 文件不存在！"
        print_info "请先创建 .env 配置文件："
        echo "  cp .env.prod.example .env"
        echo "  vi .env  # 编辑配置文件"
        echo ""
        print_warning "必须修改以下配置项："
        echo "  - MYSQL_PASSWORD（数据库密码）"
        echo "  - MYSQL_ROOT_PASSWORD（数据库 root 密码）"
        echo "  - REDIS_PASSWORD（Redis 密码）"
        echo "  - SECRET_KEY（JWT 密钥）"
        echo "  - CORS_ORIGINS（允许的域名）"
        echo "  - VITE_API_BASE_URL（API 地址）"
        echo ""
        exit 1
    fi
    
    # 加载环境变量
    set -a
    source .env
    set +a
    
    # 检查必要配置项
    MISSING_CONFIG=false
    
    check_config() {
        if [ -z "${!1}" ] || [[ "${!1}" == *"CHANGE_ME"* ]] || [[ "${!1}" == *"your-"* ]]; then
            print_warning "$1 未配置或使用默认值"
            MISSING_CONFIG=true
        fi
    }
    
    check_config "MYSQL_PASSWORD"
    check_config "MYSQL_ROOT_PASSWORD"
    check_config "REDIS_PASSWORD"
    check_config "SECRET_KEY"
    check_config "CORS_ORIGINS"
    check_config "VITE_API_BASE_URL"
    
    if [ "$MISSING_CONFIG" = true ]; then
        print_error "存在未配置的必要项，请检查 .env 文件"
        exit 1
    fi
    
    print_success "环境配置检查完成"
}

# ========================================
# 检查系统资源
# ========================================
check_system_resources() {
    print_step "检查系统资源..."

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi

    # Docker Compose 已在脚本开头检测

    # 检查磁盘空间（至少需要 10GB）- 兼容 macOS 和 Linux
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS 使用 -bg
        AVAILABLE_SPACE=$(df -bg . 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo 20)
    else
        # Linux 使用 -Bg
        AVAILABLE_SPACE=$(df -Bg . 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo 20)
    fi
    # 如果获取失败或为空，使用默认值 20
    if [ -z "$AVAILABLE_SPACE" ] || ! echo "$AVAILABLE_SPACE" | grep -q '^[0-9]\+$'; then
        AVAILABLE_SPACE=20
    fi
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        print_warning "磁盘空间不足 10GB（当前: ${AVAILABLE_SPACE}GB）"
    fi

    # 检查内存（至少需要 3GB）
    TOTAL_MEM=$(free -g 2>/dev/null | awk '/^Mem:/ {print $2}' || echo 4)
    # 如果在 macOS 上 free 命令不可用，使用 sysctl 获取内存信息
    if [ -z "$TOTAL_MEM" ] || ! echo "$TOTAL_MEM" | grep -q '^[0-9]\+$'; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS: 获取内存大小（以 GB 为单位）
            TOTAL_MEM=$(sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo 4)
        else
            TOTAL_MEM=4
        fi
    fi
    # 确保值是有效数字
    if [ -z "$TOTAL_MEM" ] || ! echo "$TOTAL_MEM" | grep -q '^[0-9]\+$'; then
        TOTAL_MEM=4
    fi
    if [ "$TOTAL_MEM" -lt 3 ]; then
        print_error "内存不足 3GB（当前: ${TOTAL_MEM}GB），无法继续部署"
        exit 1
    elif [ "$TOTAL_MEM" -lt 8 ]; then
        print_warning "内存不足 8GB（当前: ${TOTAL_MEM}GB），已自动调整配置以适应"
        print_info "注意：性能可能会有所降低，建议升级到 8GB+ 内存"
    fi
    
    print_success "系统资源检查完成"
}

# ========================================
# 拉取最新代码
# ========================================
pull_latest_code() {
    if [ "$SKIP_PULL" = true ]; then
        print_info "跳过代码拉取"
        return
    fi
    
    if [ -d .git ]; then
        print_step "拉取最新代码..."
        
        # 检查当前分支
        CURRENT_BRANCH=$(git branch --show-current)
        print_info "当前分支: $CURRENT_BRANCH"
        
        # 拉取最新代码
        if git pull origin "$CURRENT_BRANCH"; then
            print_success "代码已更新"
        else
            print_warning "代码拉取失败，继续使用当前版本"
        fi
    else
        print_info "非 Git 项目，跳过代码拉取"
    fi
}

# ========================================
# 创建必要目录
# ========================================
create_directories() {
    print_step "创建必要目录..."

    mkdir -p data/cos
    mkdir -p data/mysql
    mkdir -p "${BACKUP_DIR:-data/backups}"
    mkdir -p data/logs/api
    mkdir -p data/logs/web
    mkdir -p data/logs/mysql
    mkdir -p data/logs/redis
    mkdir -p data/logs/celery
    mkdir -p data/logs/celery-beat

    # 清理 MySQL 临时文件（这些是运行时临时创建的，可以安全删除）
    print_info "清理 MySQL 临时文件..."
    rm -rf data/mysql/#innodb_redo/*_tmp 2>/dev/null || true
    rm -rf data/mysql/#innodb_temp/* 2>/dev/null || true
    rm -f data/mysql/ibtmp1 2>/dev/null || true
    rm -f data/mysql/mysql.sock 2>/dev/null || true
    rm -f data/mysql/auto.cnf 2>/dev/null || true

    # 设置MySQL目录权限，让容器内用户(UID 999)能写入
    chmod -R 777 data/mysql 2>/dev/null || true
    chmod -R 777 data/cos 2>/dev/null || true
    chmod -R 755 data/logs/ 2>/dev/null || true

    print_success "目录创建完成"
}

# ========================================
# 备份数据
# ========================================
backup_data() {
    if [ "$DO_BACKUP" = false ]; then
        print_info "跳过备份（危险操作）"
        return
    fi

    print_step "执行数据备份..."

    BACKUP_ROOT="${BACKUP_DIR:-data/backups}"
    BACKUP_DIR="$BACKUP_ROOT/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据库
    print_info "备份数据库..."
    if docker exec miaobi-aigc-factory-mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD}" \
        "${MYSQL_DATABASE:-aigc_platform}" > "$BACKUP_DIR/database.sql" 2>/dev/null; then
        print_success "数据库备份完成: $BACKUP_DIR/database.sql"
    else
        print_warning "数据库备份失败（可能服务未启动）"
    fi
    
    # 备份 .env 文件
    if [ -f .env ]; then
        cp .env "$BACKUP_DIR/.env"
        print_success ".env 文件已备份"
    fi

    # 注意：COS 数据存储在云端，无需本地备份
    
    print_success "备份完成，保存于: $BACKUP_DIR/"
    echo ""
}

# ========================================
# 强制清理所有相关容器
# ========================================
force_cleanup_containers() {
    print_step "强制清理旧容器..."

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

# ========================================
# 构建镜像
# ========================================
build_images() {
    print_step "构建生产镜像..."

    # 升级部署时使用 --no-cache 确保依赖更新
    local build_flags=""
    if [ "$COMMAND" = "upgrade" ] || [ "$COMMAND" = "deploy" ]; then
        build_flags="--no-cache"
        print_info "使用 --no-cache 构建以确保依赖更新"
    fi

    if [ "$VERBOSE" = true ]; then
        $DOCKER_COMPOSE -f docker/docker-compose.yml build $build_flags
    else
        $DOCKER_COMPOSE -f docker/docker-compose.yml build $build_flags 2>&1 | grep -E "(Building|Step|Successfully|ERROR|Downloading|Installing|aiomysql)" || true
    fi

    print_success "镜像构建完成"
}

# ========================================
# 启动服务
# ========================================
start_services() {
    print_step "启动生产服务..."

    # 设置项目名称（优先使用 .env 文件中的配置）
    if [ -z "$COMPOSE_PROJECT_NAME" ]; then
        export COMPOSE_PROJECT_NAME=miaobi-aigc-factory
    fi
    print_info "项目名称: $COMPOSE_PROJECT_NAME"

    # 使用生产环境配置
    export API_TARGET=production
    export WEB_TARGET=production

    # 强制清理旧容器
    force_cleanup_containers

    # 启动新服务
    if [ "$VERBOSE" = true ]; then
        $DOCKER_COMPOSE -f docker/docker-compose.yml up -d
    else
        $DOCKER_COMPOSE -f docker/docker-compose.yml up -d 2>&1 | grep -E "(Creating|Starting|Up|ERROR)" || true
    fi

    print_success "服务启动完成"
}

# ========================================
# 等待服务就绪
# ========================================
wait_for_services() {
    print_step "等待服务就绪..."
    print_info "这可能需要 60 秒..."
    
    # 等待 MySQL 就绪 - 延长等待时间适应低内存服务器
    print_info "等待 MySQL 服务..."
    for i in {1..60}; do
        if docker exec miaobi-aigc-factory-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD}" --silent 2>/dev/null; then
            print_success "MySQL 已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "MySQL 启动超时"
            print_info "请检查日志: docker logs miaobi-aigc-factory-mysql"
            exit 1
        fi
        if [ $((i % 10)) -eq 0 ]; then
            print_info "仍在等待 MySQL... (${i}/120)"
        fi
        sleep 2
    done
    
    # 等待 Redis 就绪
    print_info "等待 Redis 服务..."
    for i in {1..30}; do
        if docker exec miaobi-aigc-factory-redis redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q "PONG"; then
            print_success "Redis 已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Redis 启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待 API 就绪
    print_info "等待 API 服务..."
    for i in {1..60}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API 已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "API 启动超时"
            print_info "请检查日志: docker logs miaobi-aigc-factory-api"
            exit 1
        fi
        sleep 2
    done
    
    print_success "所有服务已就绪"
}

# ========================================
# 执行数据库迁移
# ========================================
run_db_migration() {
    print_step "执行数据库迁移..."
    
    if docker exec miaobi-aigc-factory-api alembic upgrade head 2>&1 | grep -q "Running upgrade"; then
        print_success "数据库迁移完成"
    else
        print_info "数据库迁移可能已完成或无需迁移"
    fi
}

# ========================================
# 初始化数据（首次部署）
# ========================================
init_data() {
    print_step "初始化数据..."
    
    if docker exec miaobi-aigc-factory-api python scripts/deploy/all.py 2>&1 | grep -q "完成"; then
        print_success "数据初始化完成"
    else
        print_warning "数据初始化可能失败，请检查日志"
    fi
}

# ========================================
# 查看服务状态
# ========================================
show_status() {
    print_step "服务状态..."
    
    $DOCKER_COMPOSE -f docker/docker-compose.yml ps
    
    echo ""
    print_info "健康检查:"
    
    # 检查 API
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API 服务正常"
    else
        print_error "API 服务异常"
    fi
    
    # 检查 Web
    if curl -sf http://localhost:80/health > /dev/null 2>&1; then
        print_success "Web 服务正常"
    else
        print_warning "Web 服务可能未配置健康检查"
    fi
}

# ========================================
# 查看服务日志
# ========================================
show_logs() {
    print_step "查看服务日志..."
    
    echo ""
    print_info "选择要查看的日志:"
    echo "  1. API 日志"
    echo "  2. Web 日志"
    echo "  3. MySQL 日志"
    echo "  4. Redis 日志"
    echo "  5. Celery Worker 日志"
    echo "  6. Celery Beat 日志"
    echo "  7. 所有日志"
    echo ""
    read -p "请输入选项 (1-7): " choice
    
    case $choice in
        1) docker logs miaobi-aigc-factory-api -f --tail 100 ;;
        2) docker logs miaobi-aigc-factory-web -f --tail 100 ;;
        3) docker logs miaobi-aigc-factory-mysql -f --tail 100 ;;
        4) docker logs miaobi-aigc-factory-redis -f --tail 100 ;;
        5) docker logs miaobi-aigc-factory-celery-worker -f --tail 100 ;;
        6) docker logs miaobi-aigc-factory-celery-beat -f --tail 100 ;;
        7) $DOCKER_COMPOSE -f docker/docker-compose.yml logs -f --tail 50 ;;
        *) print_error "无效选项"; exit 1 ;;
    esac
}

# ========================================
# 回滚到上一版本
# ========================================
rollback() {
    print_step "回滚到上一版本..."

    # 查找最近的备份
    BACKUP_ROOT="${BACKUP_DIR:-data/backups}"
    LATEST_BACKUP=$(ls -td "$BACKUP_ROOT"/*/ 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "未找到备份文件"
        exit 1
    fi
    
    print_info "最新备份: $LATEST_BACKUP"
    read -p "确认回滚到此版本? (y/N): " confirm
    
    if [ "$confirm" != "y" ]; then
        print_info "取消回滚"
        exit 0
    fi
    
    # 停止服务
    print_info "停止服务..."
    $DOCKER_COMPOSE -f docker/docker-compose.yml down

    # 恢复数据库
    print_info "恢复数据库..."
    $DOCKER_COMPOSE -f docker/docker-compose.yml up -d mysql
    sleep 10
    
    docker exec -i miaobi-aigc-factory-mysql mysql \
        -u root -p"${MYSQL_ROOT_PASSWORD}" \
        "${MYSQL_DATABASE:-aigc_platform}" < "$LATEST_BACKUP/database.sql"
    
    print_success "数据库已恢复"
    
    # 恢复 .env
    if [ -f "$LATEST_BACKUP/.env" ]; then
        cp "$LATEST_BACKUP/.env" .env
        print_success ".env 已恢复"
    fi

    # 注意：COS 数据存储在云端，无需本地恢复
    
    # 启动服务
    print_info "启动服务..."
    export API_TARGET=production
    export WEB_TARGET=production
    $DOCKER_COMPOSE -f docker/docker-compose.yml up -d
    
    print_success "回滚完成"
}

# ========================================
# 打印部署完成信息
# ========================================
print_deploy_info() {
    print_success "=========================================="
    print_success "妙笔内容工场 生产部署完成！"
    print_success "=========================================="
    echo ""
    print_info "访问地址:"
    echo "  前端 Web: http://${SERVER_DOMAIN:-localhost}:${WEB_PORT:-80}"
    echo "  后端 API: http://${SERVER_DOMAIN:-localhost}:${API_PORT:-8000}"
    echo "  API 文档: http://${SERVER_DOMAIN:-localhost}:${API_PORT:-8000}/docs"
    echo ""
    print_info "服务状态:"
    echo "  make prod-status"
    echo ""
    print_info "查看日志:"
    echo "  make prod-logs"
    echo ""
    # 从环境变量读取默认账号
    SUPER_ADMIN_USERID=${INITIAL_SUPER_ADMIN_USERID:-admin}
    SUPER_ADMIN_PASSWORD=${INITIAL_SUPER_ADMIN_PASSWORD:-admin123}
    OPERATOR_ADMIN_USERID=${INITIAL_OPERATOR_ADMIN_USERID:-operator}
    OPERATOR_ADMIN_PASSWORD=${INITIAL_OPERATOR_ADMIN_PASSWORD:-operator123}

    print_info "默认超级管理员账号: ${SUPER_ADMIN_USERID} / ${SUPER_ADMIN_PASSWORD}"
    print_info "默认运营管理员账号: ${OPERATOR_ADMIN_USERID} / ${OPERATOR_ADMIN_PASSWORD}"
    print_warning "请在首次登录后立即修改默认密码！"
    echo ""
}

# ========================================
# 执行命令
# ========================================
case $COMMAND in
    deploy)
        print_info "=========================================="
        print_info "AIGC 平台 - 生产环境首次部署"
        print_info "=========================================="
        echo ""
        
        check_env_config
        check_system_resources
        pull_latest_code
        create_directories
        build_images
        start_services
        wait_for_services
        run_db_migration
        init_data
        print_deploy_info
        ;;
    
    upgrade)
        print_info "=========================================="
        print_info "AIGC 平台 - 生产环境升级部署"
        print_info "=========================================="
        echo ""
        
        check_env_config
        check_system_resources
        backup_data
        pull_latest_code
        build_images
        start_services
        wait_for_services
        run_db_migration
        show_status
        print_deploy_info
        ;;
    
    rollback)
        rollback
        ;;
    
    backup)
        backup_data
        ;;
    
    status)
        show_status
        ;;
    
    logs)
        show_logs
        ;;
    
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac