#!/usr/bin/env python3
"""
TGmessage 命令行界面 - 摸鱼专用
在工作时快速查看 Telegram 未读消息
"""
import asyncio
import sys
from datetime import datetime
from typing import List

from TGmessage import (
    TelegramUnreadMessageAPI,
    get_unread_dialogs,
    get_unread_messages,
    send_message,
)
from TGmessage.models import UnreadMessage, DialogInfo


class CLI:
    """命令行界面"""
    
    def __init__(self):
        self.api = None
    
    async def __aenter__(self):
        self.api = TelegramUnreadMessageAPI()
        await self.api.connect()
        return self
    
    async def __aexit__(self, *args):
        if self.api:
            await self.api.disconnect()
    
    def clear_screen(self):
        """清屏"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """打印标题"""
        width = 60
        print("\n" + "=" * width)
        print(f"  {title}")
        print("=" * width + "\n")
    
    def print_dialog(self, dialog: DialogInfo, index: int = None):
        """打印对话信息"""
        prefix = f"{index}. " if index else "  "
        emoji = "👤" if dialog.is_user else "👥" if dialog.is_group else "📢"
        pin = "📌" if dialog.is_pinned else "  "
        
        print(f"{prefix}{pin}{emoji} {dialog.name}")
        print(f"     未读: {dialog.unread_count} 条", end="")
        
        if dialog.unread_mentions_count > 0:
            print(f" (@提及: {dialog.unread_mentions_count})", end="")
        
        if dialog.last_message_text:
            preview = dialog.last_message_text[:30].replace('\n', ' ')
            print(f"\n     最后: {preview}...")
        
        print()
    
    def print_message(self, msg: UnreadMessage, show_chat: bool = True):
        """打印消息"""
        time_str = msg.date.strftime("%H:%M")
        
        if show_chat:
            emoji = "👤" if msg.is_user else "👥" if msg.is_group else "📢"
            print(f"\n{emoji} [{msg.chat_name}]")
        
        print(f"  {time_str} {msg.sender_name}:")
        
        if msg.content:
            # 缩进消息内容
            for line in msg.content.split('\n')[:5]:  # 最多显示5行
                print(f"    {line}")
        
        if msg.has_media:
            print(f"    📎 [{msg.media_type}]")
    
    async def show_dialogs(self):
        """显示对话列表"""
        self.clear_screen()
        self.print_header("📬 有未读消息的对话")
        
        dialogs = await self.api.get_all_unread_dialogs()
        
        if not dialogs:
            print("  ✅ 没有未读消息\n")
            return
        
        for i, dialog in enumerate(dialogs, 1):
            self.print_dialog(dialog, i)
        
        print(f"  共 {len(dialogs)} 个对话有未读消息\n")
    
    async def show_all_messages(self, limit: int = 20):
        """显示所有未读消息"""
        self.clear_screen()
        self.print_header(f"📨 最近 {limit} 条未读消息")
        
        messages = await self.api.get_unread_messages(limit=limit)
        
        if not messages:
            print("  ✅ 没有未读消息\n")
            return
        
        current_chat = None
        for msg in messages:
            if current_chat != msg.chat_id:
                current_chat = msg.chat_id
                self.print_message(msg, show_chat=True)
            else:
                self.print_message(msg, show_chat=False)
        
        print(f"\n  共 {len(messages)} 条未读消息\n")
    
    async def show_chat_messages(self, dialog_name: str):
        """显示特定对话的未读消息"""
        self.clear_screen()
        self.print_header(f"💬 {dialog_name} 的未读消息")
        
        try:
            messages = await self.api.get_unread_messages(dialog=dialog_name)
            
            if not messages:
                print("  ✅ 没有未读消息\n")
                return
            
            for msg in messages:
                self.print_message(msg, show_chat=False)
            
            print(f"\n  共 {len(messages)} 条未读消息\n")
        
        except ValueError as e:
            print(f"  ❌ 错误: {e}\n")
    
    async def quick_reply(self, dialog_name: str, text: str):
        """快速回复"""
        try:
            msg_id = await self.api.send_message(dialog=dialog_name, text=text)
            print(f"\n  ✅ 消息已发送 (ID: {msg_id})\n")
        except Exception as e:
            print(f"\n  ❌ 发送失败: {e}\n")
    
    def show_menu(self):
        """显示菜单"""
        print("\n" + "-" * 60)
        print("  命令:")
        print("    1/d  - 查看对话列表")
        print("    2/m  - 查看所有未读消息")
        print("    3/c  - 查看指定对话的未读消息")
        print("    4/s  - 快速发送消息")
        print("    5/r  - 刷新")
        print("    q    - 退出")
        print("-" * 60)
    
    async def run(self):
        """运行主循环"""
        self.clear_screen()
        print("\n  🎉 欢迎使用 TGmessage 摸鱼工具\n")
        print("  提示: 在工作时快速查看 Telegram 消息\n")

        # 首次显示对话列表
        await self.show_dialogs()

        while True:
            self.show_menu()

            try:
                choice = input("\n  请选择: ").strip().lower()

                if choice in ['q', 'quit', 'exit']:
                    print("\n  👋 再见!\n")
                    break

                elif choice in ['1', 'd', 'dialogs']:
                    await self.show_dialogs()

                elif choice in ['2', 'm', 'messages']:
                    limit_input = input("  显示多少条消息? [20]: ").strip()
                    limit = int(limit_input) if limit_input else 20
                    await self.show_all_messages(limit)

                elif choice in ['3', 'c', 'chat']:
                    dialog = input("  输入对话名称/用户名/ID: ").strip()
                    if dialog:
                        await self.show_chat_messages(dialog)

                elif choice in ['4', 's', 'send']:
                    dialog = input("  发送给谁? (名称/用户名/ID): ").strip()
                    if dialog:
                        text = input("  消息内容: ").strip()
                        if text:
                            await self.quick_reply(dialog, text)

                elif choice in ['5', 'r', 'refresh']:
                    await self.show_dialogs()

                else:
                    print("\n  ❌ 无效的选择\n")

            except KeyboardInterrupt:
                print("\n\n  👋 再见!\n")
                break

            except Exception as e:
                print(f"\n  ❌ 错误: {e}\n")
                import traceback
                traceback.print_exc()


async def main():
    """主函数"""
    try:
        async with CLI() as cli:
            await cli.run()
    except KeyboardInterrupt:
        print("\n\n  👋 再见!\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

