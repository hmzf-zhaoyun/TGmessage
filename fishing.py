#!/usr/bin/env python3
"""
TGmessage 摸鱼工具 - 简洁版
快速查看 Telegram 未读消息,适合在工作时使用
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from TGmessage import TelegramUnreadMessageAPI


class FishingTool:
    """摸鱼工具主类"""
    
    def __init__(self):
        self.api = None

    @asynccontextmanager
    async def _get_api(self):
        if self.api is not None:
            yield self.api
            return
        async with TelegramUnreadMessageAPI() as api:
            yield api
    
    def print_line(self, char="-", width=70):
        """打印分隔线"""
        print(char * width)
    
    def print_title(self, title: str):
        """打印标题"""
        self.print_line("=")
        print(f"  {title}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_line("=")
    
    async def quick_view(self):
        """快速查看模式 - 显示摘要"""
        async with self._get_api() as api:
            self.print_title("📱 Telegram 未读消息摘要")
            
            # 获取对话列表
            dialogs = await api.get_all_unread_dialogs()
            
            if not dialogs:
                print("\n  ✅ 没有未读消息,可以安心工作!\n")
                return
            
            # 统计
            total_count = sum(d.unread_count for d in dialogs)
            user_chats = [d for d in dialogs if d.is_user]
            group_chats = [d for d in dialogs if d.is_group]
            channel_chats = [d for d in dialogs if d.is_channel]
            
            print(f"\n  📊 统计:")
            print(f"     总未读: {total_count} 条消息")
            print(f"     私聊: {len(user_chats)} 个 ({sum(d.unread_count for d in user_chats)} 条)")
            print(f"     群组: {len(group_chats)} 个 ({sum(d.unread_count for d in group_chats)} 条)")
            print(f"     频道: {len(channel_chats)} 个 ({sum(d.unread_count for d in channel_chats)} 条)")
            
            # 私聊消息(重要)
            if user_chats:
                print(f"\n  👤 私聊消息 (重要):")
                for d in user_chats[:5]:
                    print(f"     • {d.name}: {d.unread_count} 条")
                    if d.last_message_text:
                        preview = d.last_message_text[:40].replace('\n', ' ')
                        print(f"       └─ {preview}...")
            
            # 群组消息
            if group_chats:
                print(f"\n  👥 群组消息:")
                for d in group_chats[:3]:
                    mentions = f" (@{d.unread_mentions_count})" if d.unread_mentions_count > 0 else ""
                    print(f"     • {d.name}: {d.unread_count} 条{mentions}")
            
            print()
    
    async def detailed_view(self, limit: int = 10):
        """详细查看模式 - 显示消息内容"""
        async with self._get_api() as api:
            self.print_title(f"📨 最近 {limit} 条未读消息")
            
            messages = await api.get_unread_messages(limit=limit)
            
            if not messages:
                print("\n  ✅ 没有未读消息\n")
                return
            
            current_chat = None
            msg_count = 0
            
            for msg in messages:
                # 新的对话,显示对话名
                if current_chat != msg.chat_id:
                    if current_chat is not None:
                        print()
                    
                    current_chat = msg.chat_id
                    emoji = "👤" if msg.is_user else "👥" if msg.is_group else "📢"
                    print(f"\n{emoji} [{msg.chat_name}]")
                    self.print_line("-", 70)
                
                # 显示消息
                time_str = msg.date.strftime("%H:%M")
                print(f"{time_str} {msg.sender_name}:")
                
                if msg.content:
                    lines = msg.content.split('\n')[:3]
                    for line in lines:
                        if len(line) > 60:
                            line = line[:57] + "..."
                        print(f"  {line}")
                
                if msg.has_media:
                    print(f"  📎 [{msg.media_type}]")
                
                msg_count += 1
            
            print(f"\n  显示了 {msg_count} 条消息\n")
    
    async def chat_view(self, dialog_name: str):
        """查看特定对话"""
        async with self._get_api() as api:
            self.print_title(f"💬 {dialog_name}")
            
            try:
                messages = await api.get_unread_messages(
                    dialog=dialog_name,
                    limit=api.config.max_unread_fetch
                )
                
                if not messages:
                    print("\n  ✅ 没有未读消息\n")
                    return
                
                for msg in messages:
                    time_str = msg.date.strftime("%m-%d %H:%M")
                    print(f"\n[{time_str}] {msg.sender_name}:")
                    
                    if msg.content:
                        for line in msg.content.split('\n'):
                            print(f"  {line}")
                    
                    if msg.has_media:
                        print(f"  📎 [{msg.media_type}]")

                max_message_id = max(msg.message_id for msg in messages)
                await api.mark_dialog_read(
                    dialog=dialog_name,
                    max_message_id=max_message_id
                )
                
                print(f"\n  共 {len(messages)} 条未读消息,已标记为已读\n")
            
            except ValueError as e:
                print(f"\n  ❌ 错误: {e}\n")
    
    async def send_quick_message(self, dialog: str, text: str):
        """快速发送消息"""
        async with self._get_api() as api:
            try:
                msg_id = await api.send_message(dialog=dialog, text=text)
                print(f"\n  ✅ 消息已发送给 {dialog} (ID: {msg_id})\n")
            except Exception as e:
                print(f"\n  ❌ 发送失败: {e}\n")
    
    async def interactive_mode(self):
        """交互模式"""
        async with TelegramUnreadMessageAPI() as api:
            self.api = api
            
            print("\n  🎣 TGmessage 摸鱼工具 - 交互模式")
            print("  输入 'help' 查看帮助\n")
            
            while True:
                try:
                    cmd = input("TG> ").strip()
                    
                    if not cmd:
                        continue
                    
                    parts = cmd.split(maxsplit=1)
                    action = parts[0].lower()
                    arg = parts[1] if len(parts) > 1 else None
                    
                    if action in ['q', 'quit', 'exit']:
                        print("\n  👋 再见!\n")
                        break
                    
                    elif action in ['h', 'help']:
                        self.show_help()
                    
                    elif action in ['s', 'summary']:
                        await self.quick_view()
                    
                    elif action in ['l', 'list']:
                        limit = int(arg) if arg and arg.isdigit() else 10
                        await self.detailed_view(limit)
                    
                    elif action in ['c', 'chat']:
                        if arg:
                            await self.chat_view(arg)
                        else:
                            print("  用法: chat <对话名称>")
                    
                    elif action in ['m', 'send']:
                        if arg:
                            parts2 = arg.split(maxsplit=1)
                            if len(parts2) == 2:
                                await self.send_quick_message(parts2[0], parts2[1])
                            else:
                                print("  用法: send <对话名称> <消息内容>")
                        else:
                            print("  用法: send <对话名称> <消息内容>")
                    
                    else:
                        print(f"  ❌ 未知命令: {action}")
                        print("  输入 'help' 查看帮助")
                
                except KeyboardInterrupt:
                    print("\n\n  👋 再见!\n")
                    break
                
                except Exception as e:
                    print(f"  ❌ 错误: {e}")

        self.api = None
    
    def show_help(self):
        """显示帮助"""
        print("\n  📖 命令列表:")
        print("     s, summary      - 查看摘要")
        print("     l, list [数量]  - 查看消息列表 (默认10条)")
        print("     c, chat <名称>  - 查看特定对话")
        print("     m, send <对话> <消息> - 发送消息")
        print("     h, help         - 显示帮助")
        print("     q, quit         - 退出")
        print()


def print_usage():
    """打印使用说明"""
    print("\n用法:")
    print("  python fishing.py                    # 快速查看摘要")
    print("  python fishing.py -l [数量]          # 查看消息列表")
    print("  python fishing.py -c <对话名称>      # 查看特定对话")
    print("  python fishing.py -i                 # 交互模式")
    print()


async def main():
    """主函数"""
    tool = FishingTool()
    
    if len(sys.argv) == 1:
        # 默认: 快速查看
        await tool.quick_view()
    
    elif sys.argv[1] in ['-h', '--help']:
        print_usage()
    
    elif sys.argv[1] in ['-l', '--list']:
        # 查看消息列表
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        await tool.detailed_view(limit)
    
    elif sys.argv[1] in ['-c', '--chat']:
        # 查看特定对话
        if len(sys.argv) > 2:
            await tool.chat_view(sys.argv[2])
        else:
            print("错误: 请指定对话名称")
            print_usage()
    
    elif sys.argv[1] in ['-i', '--interactive']:
        # 交互模式
        await tool.interactive_mode()
    
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
