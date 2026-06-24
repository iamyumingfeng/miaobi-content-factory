#!/bin/bash
#
# 妙笔内容工场 - 开发环境部署脚本
# 支持 Docker 镜像部署
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
    echo "妙笔内容工场 - 开发环境部署脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  docker              Docker 镜像部署（推荐）"
    echo "  status              查看服务状态"
    echo "  logs                查看服务日志"
    echo "  stop                停止服务"
    echo "  restart             重启服务"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -s, --skip-init     跳过数据初始化"
    echo "  -v, --verbose       显示详细输出"
    echo ""
    echo "示例:"
    echo "  $0 docker           # Docker 部署（一键启动）"
    echo "  $0 status           # 查看状态"
    echo "  $0 logs             # 查看日志"
    echo ""
}

# 默认配置
COMMAND=""
SKIP_INIT=false
VERBOSE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        docker|status|logs|stop|restart) COMMAND="$1"; shift ;;
        -s|--skip-init) SKIP_INIT=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        *) print_error "未知参数: $1"; show_help; exit 1 ;;
    esac
done

# 验证命令
if [ -z "$COMMAND" ]; then
    print_error "请指定命令: docker/status/logs/stop/restart"
    show_help
    exit 1
fi

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
# Docker 部署
# ========================================
deploy_docker() {
    print_info "=========================================="
    print_info "开发环境 - Docker 部署"
    print_info "=========================================="
    echo ""

    # 设置项目名称（优先使用 .env 文件中的配置）
    if [ -z "$COMPOSE_PROJECT_NAME" ]; then
        export COMPOSE_PROJECT_NAME=miaobi-aigc-factory
    fi
    print_info "项目名称: $COMPOSE_PROJECT_NAME"

    # 检查系统资源
    print_step "[0/6] 检查系统资源..."

    # 检查内存（至少需要 3GB）- 兼容 macOS 和 Linux
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
        print_warning "内存不足 3GB（当前: ${TOTAL_MEM}GB）"
        print_info "注意：性能可能会有所降低，建议至少 4GB 内存"
    fi
    print_success "系统资源检查完成"

    # 强制清理旧容器
    print_step "[1/6] 清理旧容器..."
    force_cleanup_containers

    # 创建必要目录
    print_step "[2/6] 创建必要目录..."
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

    # 配置环境变量
    print_step "[3/6] 配置环境变量..."
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success ".env 文件已创建"
        fi
    else
        print_info ".env 文件已存在"
    fi

    # 加载环境变量（用于显示默认账号）
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi

    # 构建并启动服务
    print_step "[4/6] 构建并启动服务..."

    if [ "$VERBOSE" = true ]; then
        $DOCKER_COMPOSE -f docker/docker-compose.dev.yml up -d --build
    else
        $DOCKER_COMPOSE -f docker/docker-compose.dev.yml up -d --build 2>&1 | grep -E "(Building|Starting|Up|Creating|ERROR)" || true
    fi

    print_success "服务启动完成"
    
    # 等待服务就绪
    print_step "[5/6] 等待服务就绪..."
    print_info "这可能需要 60-120 秒..."

    # 等待 MySQL
    print_info "等待 MySQL 服务..."
    for i in {1..60}; do
        if docker exec miaobi-aigc-factory-mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword123}" --silent 2>/dev/null; then
            print_success "MySQL 已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "MySQL 启动超时"
            print_info "请检查日志: docker logs miaobi-aigc-factory-mysql"
        elif [ $((i % 10)) -eq 0 ]; then
            print_info "仍在等待 MySQL... (${i}/60)"
        fi
        sleep 2
    done

    # 等待 API
    print_info "等待 API 服务..."
    for i in {1..60}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API 已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            print_warning "API 启动超时，请检查日志"
        elif [ $((i % 10)) -eq 0 ]; then
            print_info "仍在等待 API... (${i}/60)"
        fi
        sleep 2
    done

    # 初始化数据
    if [ "$SKIP_INIT" = false ]; then
        print_step "[6/6] 初始化数据..."
        if docker exec miaobi-aigc-factory-api python scripts/init_all.py > /dev/null 2>&1; then
            print_success "数据初始化完成"
        else
            print_warning "数据初始化可能失败，请检查日志"
        fi
    else
        print_info "[6/6] 跳过数据初始化"
    fi
    
    # 打印部署完成信息
    print_success "=========================================="
    print_success "开发环境 Docker 部署完成！"
    print_success "=========================================="
    echo ""
    print_info "访问地址:"
    echo "  前端: http://localhost"
    echo "  后端: http://localhost:8000"
    echo "  文档: http://localhost:8000/docs"
    echo ""
    # 从环境变量读取默认账号
    SUPER_ADMIN_USERID=${INITIAL_SUPER_ADMIN_USERID:-admin}
    SUPER_ADMIN_PASSWORD=${INITIAL_SUPER_ADMIN_PASSWORD:-admin123}
    OPERATOR_ADMIN_USERID=${INITIAL_OPERATOR_ADMIN_USERID:-operator}
    OPERATOR_ADMIN_PASSWORD=${INITIAL_OPERATOR_ADMIN_PASSWORD:-operator123}

    print_info "默认超级管理员账号: ${SUPER_ADMIN_USERID} / ${SUPER_ADMIN_PASSWORD}"
    print_info "默认运营管理员账号: ${OPERATOR_ADMIN_USERID} / ${OPERATOR_ADMIN_PASSWORD}"
    print_warning "请在首次登录后修改默认密码！"
    echo ""
}

# ========================================
# 查看服务状态
# ========================================
show_status() {
    print_step "服务状态..."
    
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -q "miaobi-aigc-factory"; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "miaobi-aigc-factory"
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
    else
        print_warning "未发现运行中的 Docker 服务"
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
    echo "  6. 所有日志"
    echo ""
    read -p "请输入选项 (1-6): " choice
    
    case $choice in
        1) docker logs miaobi-aigc-factory-api -f --tail 100 ;;
        2) docker logs miaobi-aigc-factory-web -f --tail 100 ;;
        3) docker logs miaobi-aigc-factory-mysql -f --tail 100 ;;
        4) docker logs miaobi-aigc-factory-redis -f --tail 100 ;;
        5) docker logs miaobi-aigc-factory-celery-worker -f --tail 100 ;;
        6) $DOCKER_COMPOSE -f docker/docker-compose.dev.yml logs -f --tail 50 ;;
        *) print_error "无效选项"; exit 1 ;;
    esac
}

# ========================================
# 停止服务
# ========================================
stop_services() {
    print_step "停止服务..."
    
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "miaobi-aigc-factory"; then
        $DOCKER_COMPOSE -f docker/docker-compose.dev.yml down
        print_success "Docker 服务已停止"
    else
        print_warning "未发现运行中的 Docker 服务"
        print_info "手动停止命令: pkill -f uvicorn"
    fi
}

# ========================================
# 重启服务
# ========================================
restart_services() {
    print_step "重启服务..."
    
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "miaobi-aigc-factory"; then
        $DOCKER_COMPOSE -f docker/docker-compose.dev.yml restart
        print_success "Docker 服务已重启"
    else
        print_warning "未发现运行中的 Docker 服务"
    fi
}

# ========================================
# 执行命令
# ========================================
case $COMMAND in
    docker)
        deploy_docker
        ;;
    
    status)
        show_status
        ;;
    
    logs)
        show_logs
        ;;
    
    stop)
        stop_services
        ;;
    
    restart)
        restart_services
        ;;
    
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac