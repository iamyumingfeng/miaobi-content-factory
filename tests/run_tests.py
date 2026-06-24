"""
测试运行脚本 (run_tests.py)

运行定时任务的所有测试。

Author: Claude Code
Date: 2025
"""

import subprocess
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "platform_api"))

def run_tests():
    """运行所有测试"""
    
    print("=" * 80)
    print("开始运行定时任务测试")
    print("=" * 80)
    print()
    
    # 测试文件列表
    test_files = [
        "tests/test_scheduled_task_api.py",
        "tests/test_scheduled_task_validation.py",
        "tests/test_scheduled_task_scheduler.py",
    ]
    
    # 运行 pytest
    cmd = [
        "pytest",
        "-v",  # 详细输出
        "-s",  # 显示标准输出
        "--tb=short",  # 简短的错误追踪
        "--asyncio-mode=auto",  # 自动检测 asyncio 模式
        *test_files,
    ]
    
    print(f"运行命令: {' '.join(cmd)}")
    print()
    
    # 执行测试
    result = subprocess.run(cmd, capture_output=False)
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 测试失败！")
    print("=" * 80)
    
    return result.returncode


def run_specific_test(test_file):
    """运行特定测试文件"""
    
    print(f"运行测试: {test_file}")
    print()
    
    cmd = [
        "pytest",
        "-v",
        "-s",
        "--tb=short",
        "--asyncio-mode=auto",
        test_file,
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    return result.returncode


if __name__ == "__main__":
    # 可以指定运行特定测试文件
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        exit_code = run_specific_test(test_file)
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)