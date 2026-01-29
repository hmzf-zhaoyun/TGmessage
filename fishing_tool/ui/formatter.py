"""
UI 格式化工具模块
提供统一的显示格式
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TGmessage import UnreadMessage
    from ..models import DialogInfo


class UIFormatter:
    """UI 格式化工具类"""

    @staticmethod
    def to_local_time(dt: datetime) -> datetime:
        """
        将 datetime 转换为本地时间

        Args:
            dt: datetime 对象（可能是 UTC 时间或带时区信息的时间）

        Returns:
            本地时间的 datetime 对象
        """
        if dt is None:
            return None

        # 如果有时区信息，转换为本地时间
        if dt.tzinfo is not None:
            # 转换为本地时间并移除时区信息（用于显示）
            local_dt = dt.astimezone()
            return local_dt.replace(tzinfo=None)

        # 如果没有时区信息，假设已经是本地时间
        return dt

    @staticmethod
    def print_line(char: str = "-", width: int = 70):
        """打印分隔线"""
        print(char * width)

    @staticmethod
    def print_title(title: str):
        """打印标题"""
        UIFormatter.print_line("=")
        print(f"  {title}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        UIFormatter.print_line("=")

    @staticmethod
    def format_dialog_info(dialog: 'DialogInfo') -> str:
        """格式化对话信息"""
        return dialog.format_info()

    @staticmethod
    def format_message_header(msg: 'UnreadMessage', time_format: str = "%H:%M") -> str:
        """格式化消息头部"""
        # 将 UTC 时间转换为本地时间
        local_time = UIFormatter.to_local_time(msg.date)
        time_str = local_time.strftime(time_format) if local_time else "??:??"
        sender_info = msg.sender_name
        if msg.sender_username:
            sender_info += f" (@{msg.sender_username})"
        return f"[ID:{msg.message_id}] {time_str} {sender_info}:"
    
    @staticmethod
    def format_reply_info(msg: 'UnreadMessage') -> str:
        """格式化回复信息"""
        if not msg.is_reply or not msg.reply_info:
            return ""
        
        reply_preview = msg.reply_info.content[:30] if msg.reply_info.content else "[媒体]"
        reply_sender_info = msg.reply_info.sender_name
        if msg.reply_info.sender_username:
            reply_sender_info += f" (@{msg.reply_info.sender_username})"
        return f"  ↩️  回复 {reply_sender_info}: {reply_preview}..."
    
    @staticmethod
    def format_message_content(msg: 'UnreadMessage', max_lines: int = None, max_line_length: int = 60):
        """格式化消息内容"""
        lines = []
        
        if msg.content:
            content_lines = msg.content.split('\n')
            if max_lines:
                content_lines = content_lines[:max_lines]
            
            for line in content_lines:
                if len(line) > max_line_length:
                    line = line[:max_line_length - 3] + "..."
                lines.append(f"  {line}")
        
        if msg.has_media:
            lines.append(f"  📎 [{msg.media_type}]")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_chat_header(msg: 'UnreadMessage') -> str:
        """格式化对话头部"""
        emoji = "👤" if msg.is_user else "👥" if msg.is_group else "📢"
        return f"{emoji} [{msg.chat_name}]"
    
    @staticmethod
    def print_send_usage(has_current: bool):
        """打印发送消息的用法说明"""
        if has_current:
            print("  用法: send <消息内容>  或  send <对话名称> <消息内容>")
            print("  示例: send 你好")
        else:
            print("  用法: send <对话名称> <消息内容>")
        print("  示例: send \"群组 名称\" 消息内容")
        print("        send 群组 名称 -- 消息内容")

