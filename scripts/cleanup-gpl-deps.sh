#!/bin/bash

# ========================================
# 清理GPL/AGPL许可证依赖脚本
# ========================================
# 用途: 移除具有传染性许可证的依赖,确保项目可以安全开源
# 使用: ./scripts/cleanup-gpl-deps.sh

set -e

echo "🧹 开始清理GPL/AGPL许可证依赖..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 切换到platform_api目录
cd "$(dirname "$0")/../platform_api"

# AGPL-3.0许可证依赖(最高风险)
AGPL_PACKAGES=(
    "PyMuPDF"
    "ultralytics"
    "ultralytics-thop"
)

# GPL-3.0许可证依赖(高风险)
GPL_PACKAGES=(
    "color-matcher"
    "igraph"
    "pymeshfix"
    "pymeshlab"
    "pybase16384"
)

# LGPL许可证依赖(中风险,可选清理)
LGPL_PACKAGES=(
    "chardet"
    "easydict"
    "frozendict"
    "psycopg2-binary"
    "psycopg2-pool"
    "svglib"
)

echo "📋 检查当前安装的GPL/AGPL依赖:"
echo ""

# 检查AGPL包
echo -e "${RED}AGPL-3.0 许可证依赖(最高风险):${NC}"
for pkg in "${AGPL_PACKAGES[@]}"; do
    if pip show "$pkg" &> /dev/null; then
        echo -e "  ${RED}❌ $pkg${NC} - 已安装"
    else
        echo -e "  ${GREEN}✅ $pkg${NC} - 未安装"
    fi
done

echo ""

# 检查GPL包
echo -e "${RED}GPL-3.0 许可证依赖(高风险):${NC}"
for pkg in "${GPL_PACKAGES[@]}"; do
    if pip show "$pkg" &> /dev/null; then
        echo -e "  ${RED}❌ $pkg${NC} - 已安装"
    else
        echo -e "  ${GREEN}✅ $pkg${NC} - 未安装"
    fi
done

echo ""

# 检查LGPL包
echo -e "${YELLOW}LGPL 许可证依赖(中风险):${NC}"
for pkg in "${LGPL_PACKAGES[@]}"; do
    if pip show "$pkg" &> /dev/null; then
        echo -e "  ${YELLOW}⚠️  $pkg${NC} - 已安装"
    else
        echo -e "  ${GREEN}✅ $pkg${NC} - 未安装"
    fi
done

echo ""
echo "========================================="
echo ""

# 确认卸载
read -p "是否卸载这些GPL/AGPL依赖? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消卸载"
    exit 1
fi

echo ""
echo "🗑️  开始卸载AGPL-3.0依赖..."

for pkg in "${AGPL_PACKAGES[@]}"; do
    if pip show "$pkg" &> /dev/null; then
        echo "  卸载 $pkg..."
        pip uninstall -y "$pkg" || echo -e "${YELLOW}⚠️  无法卸载 $pkg${NC}"
    fi
done

echo ""
echo "🗑️  开始卸载GPL-3.0依赖..."

for pkg in "${GPL_PACKAGES[@]}"; do
    if pip show "$pkg" &> /dev/null; then
        echo "  卸载 $pkg..."
        pip uninstall -y "$pkg" || echo -e "${YELLOW}⚠️  无法卸载 $pkg${NC}"
    fi
done

echo ""
echo "========================================="
echo -e "${GREEN}✅ GPL/AGPL依赖清理完成!${NC}"
echo ""

# 重新检查
echo "📋 重新检查剩余的GPL/AGPL依赖:"
echo ""

remaining_gpl=$(pip-licenses --from meta --format csv 2>/dev/null | grep -iE "GPL|AGPL" || true)

if [ -n "$remaining_gpl" ]; then
    echo -e "${YELLOW}⚠️  仍然存在GPL/AGPL依赖:${NC}"
    echo "$remaining_gpl"
    echo ""
    echo -e "${YELLOW}建议: 手动检查并卸载这些依赖${NC}"
else
    echo -e "${GREEN}✅ 所有GPL/AGPL依赖已清理完毕${NC}"
    echo ""
    echo -e "${GREEN}项目现在可以安全开源!${NC}"
fi

echo ""
echo "📝 后续步骤:"
echo "  1. 运行测试确保功能正常: pytest"
echo "  2. 重新生成许可证报告: pip-licenses --from meta --format json > licenses.json"
echo "  3. 更新文档,声明第三方依赖许可证"
echo ""
