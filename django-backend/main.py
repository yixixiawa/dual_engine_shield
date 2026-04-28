#!/usr/bin/env python
"""
Dual Shield 后端服务启动脚本

使用方法:
  python main.py              # 默认启动在 localhost:8080
  python main.py 0.0.0.0 8080 # 启动在 0.0.0.0:8080
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.core.management.commands.runserver import Command


def setup_django():
    """初始化 Django 设置"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')
    django.setup()


def print_banner(host, port):
    """打印服务启动信息"""
    banner = f"""
    ╔════════════════════════════════════════╗
    ║     Dual Shield Backend Server         ║
    ║                                        ║
    ║  🚀 Server running at:                 ║
    ║     http://{host}:{port}              ║
    ║                                        ║
    ║  📡 API Endpoints:                     ║
    ║     • Health Check: /api/health/       ║
    ║     • Phishing Detection: /api/detect/ ║
    ║     • Code Detection: /api/detect/code/║
    ║                                        ║
    ║  ⏹️  Press CTRL+C to stop               ║
    ╚════════════════════════════════════════╝
    """
    print(banner)


def main():
    """主启动函数"""
    # 解析命令行参数
    if len(sys.argv) == 1:
        # 默认参数
        host = 'localhost'
        port = '8080'
    elif len(sys.argv) == 2:
        # 只指定端口
        host = 'localhost'
        port = sys.argv[1]
    elif len(sys.argv) == 3:
        # 指定 host 和 port
        host = sys.argv[1]
        port = sys.argv[2]
    else:
        print("用法错误！")
        print(__doc__)
        sys.exit(1)

    # 初始化 Django
    setup_django()

    # 准备 Django 命令参数
    runserver_args = [f'{host}:{port}']
    
    # 执行 Django runserver 命令
    # 仅在主进程中打印 banner（避免 StatReloader 重复执行）
    if os.environ.get('RUN_MAIN') == 'true':
        print_banner(host, port)
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', *runserver_args])
    except KeyboardInterrupt:
        print("\n\n✋ 服务已停止")
        sys.exit(0)


if __name__ == '__main__':
    main()
