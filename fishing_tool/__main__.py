#!/usr/bin/env python3
"""
命令行入口模块
支持: python -m fishing_tool [options]
"""
import asyncio
import sys

from .core import FishingApp
from .ui import InteractiveShell


def print_usage():
    """打印使用说明"""
    print("\n用法:")
    print("  python -m fishing_tool                    # 快速查看摘要")
    print("  python -m fishing_tool -l [数量]          # 查看消息列表")
    print("  python -m fishing_tool -c <对话名称>      # 查看特定对话")
    print("  python -m fishing_tool -i                 # 交互模式")
    print()


async def main():
    """主函数"""
    app = FishingApp()
    
    if len(sys.argv) == 1:
        # 默认: 快速查看
        await app.run_summary_view()
    
    elif sys.argv[1] in ['-h', '--help']:
        print_usage()
    
    elif sys.argv[1] in ['-l', '--list']:
        # 查看消息列表
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        await app.run_recent_view(limit)
    
    elif sys.argv[1] in ['-c', '--chat']:
        # 查看特定对话
        if len(sys.argv) > 2:
            await app.run_dialog_view(sys.argv[2])
        else:
            print("错误: 请指定对话名称")
            print_usage()
    
    elif sys.argv[1] in ['-i', '--interactive']:
        # 交互模式
        shell = InteractiveShell(app)
        await shell.run()
    
    else:
        print(f"错误: 未知选项 {sys.argv[1]}")
        print_usage()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 再见!\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")

