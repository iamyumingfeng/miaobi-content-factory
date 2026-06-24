#!/usr/bin/env python3
"""一键执行所有初始化"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("========================================")
    print("AIGC平台 - 一键初始化")
    print("========================================")
    print()

    scripts = [
        "01-init-db.py",
        "02-init-admin.py",
        "03-init-models.py",
        "04-init-data.py",
    ]

    for script in scripts:
        path = os.path.join(SCRIPT_DIR, script)
        result = subprocess.run([sys.executable, path])
        if result.returncode != 0:
            print(f"❌ {script} 执行失败")
            sys.exit(1)
        print()

    print("========================================")
    print("✅ 所有初始化完成!")
    print("========================================")


if __name__ == "__main__":
    main()
