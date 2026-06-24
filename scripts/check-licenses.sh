#!/bin/bash

# ========================================
# 许可证兼容性检查脚本
# ========================================
# 用途: 检查项目依赖的许可证是否与 MIT License 兼容
# 使用: ./scripts/check-licenses.sh

set -e

echo "🔍 开始检查许可证兼容性..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建临时文件
TEMP_FILE=$(mktemp)

# 检查 pip-licenses 是否安装
if ! command -v pip-licenses &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip-licenses 未安装,正在安装...${NC}"
    pip install pip-licenses
fi

# 生成许可证报告
echo "📋 生成许可证报告..."
pip-licenses --from meta --format csv > "$TEMP_FILE"

# 检查高风险许可证
echo ""
echo "🔍 检查高风险许可证..."

# GPL/AGPL 许可证(传染性,不兼容 MIT)
GPL_LICENSES=$(grep -i "GPL\|AGPL" "$TEMP_FILE" || true)

if [ -n "$GPL_LICENSES" ]; then
    echo -e "${RED}❌ 发现 GPL/AGPL 许可证依赖:${NC}"
    echo "$GPL_LICENSES"
    echo ""
    echo -e "${RED}⚠️  警告: GPL/AGPL 许可证具有传染性,可能导致整个项目被迫开源!${NC}"
    echo -e "${YELLOW}建议: 移除或替换这些依赖${NC}"
    rm "$TEMP_FILE"
    exit 1
fi

# LGPL 许可证(弱传染性,需谨慎)
LGPL_LICENSES=$(grep -i "LGPL" "$TEMP_FILE" || true)

if [ -n "$LGPL_LICENSES" ]; then
    echo -e "${YELLOW}⚠️  发现 LGPL 许可证依赖:${NC}"
    echo "$LGPL_LICENSES"
    echo ""
    echo -e "${YELLOW}注意: LGPL 许可证具有弱传染性,动态链接可能安全,静态链接需开源${NC}"
fi

# MPL/CDDL 许可证(弱传染性,需谨慎)
MPL_LICENSES=$(grep -i "MPL\|CDDL" "$TEMP_FILE" || true)

if [ -n "$MPL_LICENSES" ]; then
    echo -e "${YELLOW}⚠️  发现 MPL/CDDL 许可证依赖:${NC}"
    echo "$MPL_LICENSES"
    echo ""
    echo -e "${YELLOW}注意: MPL/CDDL 许可证具有文件级传染性,修改相关文件需开源${NC}"
fi

# 统计许可证类型
echo ""
echo "📊 许可证统计:"
echo ""

TOTAL=$(tail -n +2 "$TEMP_FILE" | wc -l | tr -d ' ')
MIT_COUNT=$(grep -i "MIT" "$TEMP_FILE" | wc -l | tr -d ' ')
APACHE_COUNT=$(grep -i "Apache" "$TEMP_FILE" | wc -l | tr -d ' ')
BSD_COUNT=$(grep -i "BSD" "$TEMP_FILE" | wc -l | tr -d ' ')
UNKNOWN_COUNT=$(grep "UNKNOWN" "$TEMP_FILE" | wc -l | tr -d ' ')

echo "总依赖数: $TOTAL"
echo -e "${GREEN}MIT License: $MIT_COUNT${NC}"
echo -e "${GREEN}Apache License: $APACHE_COUNT${NC}"
echo -e "${GREEN}BSD License: $BSD_COUNT${NC}"

if [ "$UNKNOWN_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}未知许可证: $UNKNOWN_COUNT${NC}"
fi

# 检查未知许可证
UNKNOWN_LICENSES=$(grep "UNKNOWN" "$TEMP_FILE" || true)

if [ -n "$UNKNOWN_LICENSES" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  发现未知许可证依赖:${NC}"
    echo "$UNKNOWN_LICENSES"
    echo ""
    echo -e "${YELLOW}建议: 手动检查这些依赖的许可证${NC}"
fi

# 生成详细报告
REPORT_FILE="licenses-report.txt"
echo ""
echo "📝 生成详细报告: $REPORT_FILE"
pip-licenses --from meta --format plain > "$REPORT_FILE"

# 最终结论
echo ""
echo "========================================="
if [ -z "$GPL_LICENSES" ] && [ -z "$LGPL_LICENSES" ] && [ -z "$MPL_LICENSES" ]; then
    echo -e "${GREEN}✅ 许可证检查通过!${NC}"
    echo -e "${GREEN}所有依赖许可证与 MIT License 兼容${NC}"
    rm "$TEMP_FILE"
    exit 0
else
    echo -e "${YELLOW}⚠️  许可证检查完成,但存在需要注意的依赖${NC}"
    echo -e "${YELLOW}请仔细评估上述标记的依赖${NC}"
    rm "$TEMP_FILE"
    exit 0
fi
