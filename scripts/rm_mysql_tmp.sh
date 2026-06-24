#!/bin/bash
#
# 妙笔内容工场 - 清理 MySQL 临时文件
#
# 当 MySQL 容器无法启动（权限错误）时运行此脚本
# 删除有问题的临时文件（这些是 MySQL 运行时临时创建的，可以安全删除）
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "==> 清理 MySQL 临时文件..."

# 先停止 MySQL 容器（如果在运行）
if docker ps --format '{{.Names}}' | grep -q 'miaobi-aigc-factory-mysql'; then
    echo "    停止 MySQL 容器..."
    docker stop miaobi-aigc-factory-mysql >/dev/null 2>&1 || true
fi

# 清理临时文件
echo "    删除 #innodb_redo 临时文件..."
sudo rm -rf data/mysql/#innodb_redo/*_tmp 2>/dev/null || true

echo "    删除 #innodb_temp 临时文件..."
sudo rm -rf data/mysql/#innodb_temp/* 2>/dev/null || true

echo "    删除 ibtmp1..."
sudo rm -f data/mysql/ibtmp1 2>/dev/null || true

echo "    删除 mysql.sock..."
sudo rm -f data/mysql/mysql.sock 2>/dev/null || true

echo "    删除 auto.cnf（重启时自动生成）..."
sudo rm -f data/mysql/auto.cnf 2>/dev/null || true

# 修复权限
echo "    修复目录权限..."
sudo chmod -R 777 data/mysql 2>/dev/null || true

echo "==> 清理完成！请重新启动服务："
