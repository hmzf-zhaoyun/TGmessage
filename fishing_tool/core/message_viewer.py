"""
消息查看器模块
负责消息的查看和显示逻辑
"""
from typing import Dict, List, Optional, TYPE_CHECKING

from ..ui.formatter import UIFormatter

if TYPE_CHECKING:
    from TGmessage import TelegramUnreadMessageAPI, UnreadMessage


class MessageViewer:
    """消息查看器"""
    
    def __init__(self):
        """初始化消息查看器"""
        self.recent_messages: Dict[int, List['UnreadMessage']] = {}
        self.formatter = UIFormatter()
    
    async def show_summary(self, api: 'TelegramUnreadMessageAPI'):
        """显示消息摘要"""
        self.formatter.print_title("📱 Telegram 未读消息摘要")
        
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
    
    async def show_recent_messages(self, api: 'TelegramUnreadMessageAPI', limit: int = 10):
        """显示最近的未读消息"""
        self.formatter.print_title(f"📨 最近 {limit} 条未读消息")
        
        messages = await api.get_unread_messages(limit=limit)
        
        if not messages:
            print("\n  ✅ 没有未读消息\n")
            return
        
        # 存储消息以便后续引用
        for msg in messages:
            if msg.chat_id not in self.recent_messages:
                self.recent_messages[msg.chat_id] = []
            self.recent_messages[msg.chat_id].append(msg)
        
        current_chat = None
        msg_count = 0
        
        for msg in messages:
            # 新的对话,显示对话名
            if current_chat != msg.chat_id:
                if current_chat is not None:
                    print()
                
                current_chat = msg.chat_id
                print(f"\n{self.formatter.format_chat_header(msg)}")
                self.formatter.print_line("-", 70)
            
            # 显示消息头部
            print(self.formatter.format_message_header(msg))
            
            # 显示回复信息
            if msg.is_reply and msg.reply_info:
                print(self.formatter.format_reply_info(msg))
            
            # 显示消息内容
            print(self.formatter.format_message_content(msg, max_lines=3, max_line_length=60))
            
            msg_count += 1
        
        print(f"\n  显示了 {msg_count} 条消息\n")
        print("  💡 提示: 使用消息ID进行回复、编辑、删除等操作")
    
    async def show_dialog_messages(
        self,
        api: 'TelegramUnreadMessageAPI',
        dialog_identifier,
        dialog_label: Optional[str] = None
    ):
        """显示特定对话的消息"""
        title = dialog_label or str(dialog_identifier)
        self.formatter.print_title(f"💬 {title}")
        
        try:
            messages = await api.get_unread_messages(
                dialog=dialog_identifier,
                limit=api.config.max_unread_fetch
            )
            
            if not messages:
                print("\n  ✅ 没有未读消息\n")
                return
            
            # 存储消息以便后续引用
            if isinstance(dialog_identifier, int):
                dialog_id = dialog_identifier
            else:
                dialog_id = messages[0].chat_id if messages else None
            
            if dialog_id:
                if dialog_id not in self.recent_messages:
                    self.recent_messages[dialog_id] = []
                self.recent_messages[dialog_id].extend(messages)
            
            for msg in messages:
                # 显示消息头部
                print(f"\n{self.formatter.format_message_header(msg, time_format='%m-%d %H:%M')}")
                
                # 显示回复信息
                if msg.is_reply and msg.reply_info:
                    print(self.formatter.format_reply_info(msg))
                
                # 显示消息内容(完整内容)
                print(self.formatter.format_message_content(msg, max_lines=None, max_line_length=1000))
            
            # 标记为已读
            max_message_id = max(msg.message_id for msg in messages)
            await api.mark_dialog_read(
                dialog=dialog_identifier,
                max_message_id=max_message_id
            )
            
            print(f"\n  共 {len(messages)} 条未读消息,已标记为已读")
            print("  💡 提示: 使用消息ID进行回复、编辑、删除等操作\n")
        
        except ValueError as e:
            print(f"\n  ❌ 错误: {e}\n")

