#!/bin/bash
# ==============================================================================
# 妙笔内容工场 - 后端启动脚本
#
# 此脚本在启动API服务前自动执行：
# 1. 等待数据库连接
# 2. 数据库迁移 (alembic upgrade head) - 每次都执行（幂等操作）
# 3. 初始化数据 (python scripts/init_all.py) - 仅首次部署执行一次
# 4. 启动API服务
#
# 使用方法：
#   ./scripts/start.sh [development|production]
# ==============================================================================

set -e

# 颜色输出
COLOR_RESET="\033[0m"
COLOR_INFO="\033[36m"
COLOR_SUCCESS="\033[32m"
COLOR_WARNING="\033[33m"
COLOR_ERROR="\033[31m"

# 确定运行模式
MODE="${1:-development}"

# 数据初始化标记文件（用于判断是否已初始化过）
INIT_MARKER_FILE="/tmp/.data_initialized"

echo -e "${COLOR_INFO}========================================${COLOR_RESET}"
echo -e "${COLOR_INFO}妙笔内容工场 - 后端启动${COLOR_RESET}"
echo -e "${COLOR_INFO}========================================${COLOR_RESET}"
echo -e "运行模式: ${COLOR_SUCCESS}${MODE}${COLOR_RESET}"
echo ""

# 等待数据库就绪
echo -e "${COLOR_INFO}[1/4] 等待数据库连接...${COLOR_RESET}"
python << 'EOF'
import asyncio
import time
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, async_engine

async def wait_for_db():
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
                print("数据库连接成功！")
                return True
        except Exception as e:
            retry_count += 1
            print(f"等待数据库... ({retry_count}/{max_retries})")
            time.sleep(2)
    print("数据库连接超时")
    return False

async def main():
    result = await wait_for_db()
    # 显式关闭连接池，防止垃圾回收时报错
    engine = async_engine()  # async_engine 是函数，需要调用获取 engine
    await engine.dispose()
    return result

asyncio.run(main())
EOF

echo ""

# 运行数据库迁移（每次都执行，幂等操作）
echo -e "${COLOR_INFO}[2/4] 运行数据库迁移...${COLOR_RESET}"
alembic upgrade head
echo -e "${COLOR_SUCCESS}数据库迁移完成${COLOR_RESET}"
echo ""

# 初始化数据（仅首次执行）
echo -e "${COLOR_INFO}[3/4] 初始化数据...${COLOR_RESET}"
if [ -f "$INIT_MARKER_FILE" ]; then
    echo -e "${COLOR_WARNING}跳过数据初始化：已在首次部署时执行过${COLOR_RESET}"
    echo -e "${COLOR_WARNING}如需重新初始化，请删除文件: $INIT_MARKER_FILE${COLOR_RESET}"
    echo -e "${COLOR_WARNING}或手动运行: docker exec <container> python scripts/init_all.py${COLOR_RESET}"
else
    if [ -f "scripts/init_all.py" ] && [ -f "config/init_data.yaml" ]; then
        python scripts/init_all.py && touch "$INIT_MARKER_FILE" || echo -e "${COLOR_WARNING}数据初始化脚本执行完成${COLOR_RESET}"
    else
        echo -e "${COLOR_WARNING}跳过数据初始化：缺少 init_all.py 或 init_data.yaml${COLOR_RESET}"
    fi
fi
echo ""

# 启动API服务
echo -e "${COLOR_INFO}[4/4] 启动API服务...${COLOR_RESET}"
echo -e "${COLOR_SUCCESS}========================================${COLOR_RESET}"

if [ "$MODE" = "production" ]; then
    echo -e "生产模式: 使用 4 workers"
    echo -e "${COLOR_SUCCESS}========================================${COLOR_RESET}"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
else
    echo -e "开发模式: 启用热重载"
    echo -e "${COLOR_SUCCESS}========================================${COLOR_RESET}"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
