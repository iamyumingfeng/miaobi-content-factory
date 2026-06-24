"""
妙笔内容工场 - 入口文件

提供开发服务器启动入口。

Usage:
    python main.py          # 启动开发服务器
    uvicorn app.main:app    # 生产环境启动

Author: Claude Code
Date: 2025
"""

import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
