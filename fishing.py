#!/usr/bin/env python3
"""
TGmessage 摸鱼工具 - 简洁版
快速查看 Telegram 未读消息,适合在工作时使用
"""
import asyncio
import sys
import shlex
import json
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from TGmessage import TelegramUnreadMessageAPI
from TGmessage.utils import find_dialog


class FishingTool:
    """摸鱼工具主类"""
    
    def __init__(self):
        self.api = None
        self.favorites_path = Path(__file__).resolve().parent / ".tgmessage_favorites.json"
        self.favorites = []
        self.current_dialog = None
        self._load_favorites()

    @asynccontextmanager
    async def _get_api(self):
        if self.api is not None:
            yield self.api
            return
        async with TelegramUnreadMessageAPI() as api:
            yield api

    def _load_favorites(self):
        if not self.favorites_path.exists():
            self.favorites = []
            return
        try:
            data = json.loads(self.favorites_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"收藏文件解析失败: {e}")
        if not isinstance(data, list):
            raise ValueError("收藏文件格式错误: 需要列表")

        favorites = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("收藏文件格式错误: 列表元素必须为对象")
            dialog_id = item.get("dialog_id")
            name = item.get("name")
            username = item.get("username")
            if not isinstance(dialog_id, int):
                raise ValueError("收藏文件格式错误: dialog_id 必须为整数")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("收藏文件格式错误: name 必须为非空字符串")
            if username is not None and not isinstance(username, str):
                raise ValueError("收藏文件格式错误: username 必须为字符串或 null")
            favorites.append({
                "dialog_id": dialog_id,
                "name": name,
                "username": username
            })

        self.favorites = favorites

    def _save_favorites(self):
        data = json.dumps(self.favorites, ensure_ascii=False, indent=2)
        self.favorites_path.write_text(data, encoding="utf-8")

    def _favorite_index_by_id(self, dialog_id: int):
        for i, fav in enumerate(self.favorites):
            if fav.get("dialog_id") == dialog_id:
                return i
        return None

    def _find_favorite_indices(self, identifier: str):
        identifier_str = identifier.strip()
        if identifier_str.startswith("@"):
            identifier_str = identifier_str[1:]
        identifier_str = identifier_str.lower()

        matches = []
        for i, fav in enumerate(self.favorites):
            if str(fav.get("dialog_id")) == identifier_str:
                matches.append(i)
                continue
            name = fav.get("name")
            if name and name.lower() == identifier_str:
                matches.append(i)
                continue
            username = fav.get("username")
            if username and username.lower() == identifier_str:
                matches.append(i)
        return matches

    def _format_dialog_info(self, dialog_info: dict) -> str:
        username = dialog_info.get("username")
        username_part = f" (@{username})" if username else ""
        return f"{dialog_info['name']}{username_part} [ID: {dialog_info['dialog_id']}]"

    def _print_send_usage(self, has_current: bool):
        if has_current:
            print("  用法: send <消息内容>  或  send <对话名称> <消息内容>")
            print("  示例: send 你好")
        else:
            print("  用法: send <对话名称> <消息内容>")
        print("  示例: send \"群组 名称\" 消息内容")
        print("        send 群组 名称 -- 消息内容")

    async def _resolve_dialog_info(self, identifier):
        if self.api is None:
            raise RuntimeError("API 未初始化")
        dialog = await find_dialog(self.api.client_wrapper.client, identifier)
        if dialog is None:
            raise ValueError(f"找不到对话: {identifier}")
        entity = dialog.entity
        username = getattr(entity, "username", None)
        return {
            "dialog_id": dialog.id,
            "name": dialog.name,
            "username": username
        }

    def list_stars(self):
        if not self.favorites:
            print("\n  暂无收藏对话\n")
            return
        print("\n  ⭐ 收藏对话:")
        current_id = self.current_dialog["dialog_id"] if self.current_dialog else None
        for i, fav in enumerate(self.favorites, 1):
            mark = "★" if current_id == fav.get("dialog_id") else " "
            print(f"  {i}. {mark} {self._format_dialog_info(fav)}")
        print()

    async def add_star(self, args):
        if not args:
            if not self.current_dialog:
                print("  用法: star <对话名称/用户名/ID>  (或先 use 进入对话)")
                return
            dialog_info = dict(self.current_dialog)
        else:
            identifier = " ".join(args)
            try:
                dialog_info = await self._resolve_dialog_info(identifier)
            except ValueError as e:
                print(f"  ❌ {e}")
                return

        index = self._favorite_index_by_id(dialog_info["dialog_id"])
        if index is None:
            self.favorites.append(dialog_info)
            self._save_favorites()
            print(f"  ✅ 已收藏: {self._format_dialog_info(dialog_info)}")
        else:
            self.favorites[index] = dialog_info
            self._save_favorites()
            print(f"  ✅ 收藏已更新: {self._format_dialog_info(dialog_info)}")

    async def remove_star(self, args):
        if not args:
            if not self.current_dialog:
                print("  用法: unstar <序号|对话名称/用户名/ID>  (或先 use 进入对话)")
                return
            target_id = self.current_dialog["dialog_id"]
            index = self._favorite_index_by_id(target_id)
            if index is None:
                print("  ❌ 当前对话不在收藏中")
                return
            removed = self.favorites.pop(index)
            self._save_favorites()
            print(f"  ✅ 已取消收藏: {self._format_dialog_info(removed)}")
            return

        index = None
        if len(args) == 1 and args[0].isdigit():
            idx = int(args[0])
            if 1 <= idx <= len(self.favorites):
                index = idx - 1
            else:
                print("  ❌ 序号超出范围")
                return
        else:
            identifier = " ".join(args)
            matches = self._find_favorite_indices(identifier)
            if len(matches) == 1:
                index = matches[0]
            elif len(matches) > 1:
                print("  ❌ 匹配到多个收藏,请使用序号")
                return
            else:
                try:
                    dialog_info = await self._resolve_dialog_info(identifier)
                except ValueError as e:
                    print(f"  ❌ {e}")
                    return
                index = self._favorite_index_by_id(dialog_info["dialog_id"])
                if index is None:
                    print("  ❌ 未找到对应的收藏")
                    return

        removed = self.favorites.pop(index)
        self._save_favorites()
        print(f"  ✅ 已取消收藏: {self._format_dialog_info(removed)}")

    async def use_dialog(self, args):
        if not args:
            print("  用法: use <序号|对话名称/用户名/ID>")
            return

        dialog_info = None
        if len(args) == 1 and args[0].isdigit():
            idx = int(args[0])
            if 1 <= idx <= len(self.favorites):
                identifier = self.favorites[idx - 1]["dialog_id"]
                try:
                    dialog_info = await self._resolve_dialog_info(identifier)
                except ValueError as e:
                    print(f"  ❌ {e}")
                    return
            else:
                print("  ❌ 序号超出范围")
                return

        if dialog_info is None:
            identifier = " ".join(args)
            try:
                dialog_info = await self._resolve_dialog_info(identifier)
            except ValueError as e:
                print(f"  ❌ {e}")
                return

        self.current_dialog = dialog_info
        index = self._favorite_index_by_id(dialog_info["dialog_id"])
        if index is not None:
            self.favorites[index] = dialog_info
            self._save_favorites()
        print(f"  ✅ 已进入对话: {self._format_dialog_info(dialog_info)}")

    def leave_dialog(self):
        if not self.current_dialog:
            print("  当前未进入任何对话")
            return
        dialog_info = self.current_dialog
        self.current_dialog = None
        print(f"  ✅ 已退出对话: {self._format_dialog_info(dialog_info)}")
    
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
    
    async def chat_view(self, dialog_identifier, dialog_label: str = None):
        """查看特定对话"""
        async with self._get_api() as api:
            title = dialog_label or str(dialog_identifier)
            self.print_title(f"💬 {title}")
            
            try:
                messages = await api.get_unread_messages(
                    dialog=dialog_identifier,
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
                    dialog=dialog_identifier,
                    max_message_id=max_message_id
                )
                
                print(f"\n  共 {len(messages)} 条未读消息,已标记为已读\n")
            
            except ValueError as e:
                print(f"\n  ❌ 错误: {e}\n")
    
    async def send_quick_message(self, dialog, text: str, dialog_label: str = None):
        """快速发送消息(带消息遗漏补偿)"""
        async with self._get_api() as api:
            try:
                # 获取对话ID(用于消息追踪)
                dialog_id = None
                if isinstance(dialog, int):
                    dialog_id = dialog
                else:
                    # 需要先解析对话以获取ID
                    from TGmessage.utils import find_dialog
                    dialog_obj = await find_dialog(api.client_wrapper.client, dialog)
                    if dialog_obj:
                        dialog_id = dialog_obj.id

                # 检查是否有遗漏的消息(发送前)
                missed_messages = []
                if dialog_id and hasattr(api.message_fetcher, 'tracker') and api.message_fetcher.tracker:
                    tracker = api.message_fetcher.tracker
                    last_read_id = tracker.get_last_read_message_id(dialog_id)

                    if last_read_id:
                        # 获取从上次已读到现在的所有消息
                        try:
                            all_messages = await api.get_unread_messages(dialog=dialog)
                            if all_messages:
                                # 过滤出可能遗漏的消息(ID大于上次已读ID)
                                missed_messages = [
                                    msg for msg in all_messages
                                    if msg.message_id > last_read_id
                                ]
                        except Exception as e:
                            print(f"  ⚠️  检查遗漏消息时出错: {e}")

                # 发送消息
                msg_id = await api.send_message(dialog=dialog, text=text)
                target = dialog_label or str(dialog)
                print(f"\n  ✅ 消息已发送给 {target} (ID: {msg_id})")

                # 如果有遗漏的消息,显示提示
                if missed_messages:
                    print(f"  📬 检测到 {len(missed_messages)} 条中间消息:")
                    for msg in missed_messages[:3]:  # 最多显示3条
                        time_str = msg.date.strftime("%H:%M")
                        preview = msg.content[:30].replace('\n', ' ') if msg.content else '[无文本]'
                        print(f"     • [{time_str}] {msg.sender_name}: {preview}...")
                    if len(missed_messages) > 3:
                        print(f"     • ... 还有 {len(missed_messages) - 3} 条消息")
                    print(f"  💡 使用 'chat' 命令查看完整对话")

                print()

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
                    
                    try:
                        tokens = shlex.split(cmd)
                    except ValueError as e:
                        print(f"  ❌ 参数解析失败: {e}")
                        continue

                    if not tokens:
                        continue

                    action = tokens[0].lower()
                    args = tokens[1:]
                    
                    if action in ['q', 'quit', 'exit']:
                        print("\n  👋 再见!\n")
                        break
                    
                    elif action in ['h', 'help']:
                        self.show_help()
                    
                    elif action in ['s', 'summary']:
                        await self.quick_view()
                    
                    elif action in ['l', 'list']:
                        limit = int(args[0]) if args and args[0].isdigit() else 10
                        await self.detailed_view(limit)

                    elif action == 'stars':
                        self.list_stars()

                    elif action == 'star':
                        await self.add_star(args)

                    elif action == 'unstar':
                        await self.remove_star(args)

                    elif action == 'use':
                        await self.use_dialog(args)

                    elif action == 'back':
                        self.leave_dialog()
                    
                    elif action in ['c', 'chat']:
                        if args:
                            await self.chat_view(" ".join(args))
                        elif self.current_dialog:
                            await self.chat_view(
                                self.current_dialog["dialog_id"],
                                dialog_label=self.current_dialog["name"]
                            )
                        else:
                            print("  用法: chat <对话名称>  (或先 use 进入对话)")
                    
                    elif action in ['m', 'send']:
                        dialog = None
                        dialog_label = None
                        text = None

                        if args:
                            if '--' in args:
                                sep_index = args.index('--')
                                dialog_tokens = args[:sep_index]
                                text_tokens = args[sep_index + 1:]
                                if dialog_tokens and text_tokens:
                                    dialog = " ".join(dialog_tokens)
                                    text = " ".join(text_tokens)
                            elif len(args) >= 2:
                                dialog = args[0]
                                text = " ".join(args[1:])
                            elif len(args) == 1 and self.current_dialog:
                                dialog = self.current_dialog["dialog_id"]
                                dialog_label = self.current_dialog["name"]
                                text = args[0]
                        elif self.current_dialog:
                            self._print_send_usage(True)
                            continue
                        else:
                            self._print_send_usage(False)
                            continue

                        if dialog and text:
                            await self.send_quick_message(dialog, text, dialog_label=dialog_label)
                        else:
                            self._print_send_usage(self.current_dialog is not None)
                    
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
        print("     c, chat [名称]  - 查看特定对话 (进入对话后可省略)")
        print("     m, send [对话] <消息> - 发送消息 (进入对话后可省略)")
        print("     stars           - 查看收藏对话")
        print("     star <对话|序号> - 收藏对话 (可省略使用当前对话)")
        print("     unstar <对话|序号> - 取消收藏 (可省略使用当前对话)")
        print("     use <对话|序号>  - 进入对话")
        print("     back            - 退出当前对话")
        print("     示例: send 你好")
        print("           send \"群组 名称\" 消息内容  或  send 群组 名称 -- 消息内容")
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
