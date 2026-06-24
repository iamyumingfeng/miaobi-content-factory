#!/bin/bash

# ========================================
# Docker 时区验证脚本
# ========================================
# 用于验证 Docker 容器时区配置是否正确
# 使用方法: ./scripts/verify_timezone.sh
# ========================================

echo "========================================"
echo "Docker 容器时区验证"
echo "========================================"
echo ""

# 获取当前系统时间
echo "1. 当前系统时间:"
echo "   $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# 检查容器时间
echo "2. 检查各容器时间:"
echo ""

# API 容器
echo "【API 容器】"
if docker ps | grep -q miaobi-aigc-factory-api; then
    echo "   容器时间: $(docker exec miaobi-aigc-factory-api date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "   时区文件: $(docker exec miaobi-aigc-factory-api cat /etc/localtime 2>/dev/null | head -c 50 || echo '未挂载')"
    echo "   TZ环境变量: $(docker exec miaobi-aigc-factory-api printenv TZ)"
else
    echo "   ⚠️  容器未运行"
fi
echo ""

# Celery Worker 容器
echo "【Celery Worker 容器】"
if docker ps | grep -q miaobi-aigc-factory-celery-worker; then
    echo "   容器时间: $(docker exec miaobi-aigc-factory-celery-worker date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "   TZ环境变量: $(docker exec miaobi-aigc-factory-celery-worker printenv TZ)"
else
    echo "   ⚠️  容器未运行"
fi
echo ""

# Celery Beat 容器
echo "【Celery Beat 容器】"
if docker ps | grep -q miaobi-aigc-factory-celery-beat; then
    echo "   容器时间: $(docker exec miaobi-aigc-factory-celery-beat date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "   TZ环境变量: $(docker exec miaobi-aigc-factory-celery-beat printenv TZ)"
else
    echo "   ⚠️  容器未运行"
fi
echo ""

# MySQL 容器
echo "【MySQL 容器】"
if docker ps | grep -q miaobi-aigc-factory-mysql; then
    echo "   容器时间: $(docker exec miaobi-aigc-factory-mysql date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "   TZ环境变量: $(docker exec miaobi-aigc-factory-mysql printenv TZ)"
else
    echo "   ⚠️  容器未运行"
fi
echo ""

echo "========================================"
echo "验证完成"
echo "========================================"
echo ""
echo "✅ 如果所有容器时间与系统时间一致，则时区配置正确"
echo "❌ 如果时间不一致，请检查："
echo "   1. 宿主机时区是否正确 (运行: timedatectl)"
echo "   2. /etc/localtime 文件是否存在"
echo "   3. 容器是否需要重建 (运行: docker-compose up -d --build)"
echo ""
