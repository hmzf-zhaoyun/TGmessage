"""
数据模型定义
定义未读消息、对话等数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ReplyInfo:
    """回复消息信息"""

    message_id: int
    content: str
    sender_id: int
    sender_name: str
    sender_username: Optional[str] = None
    date: Optional[datetime] = None
    has_media: bool = False
    media_type: Optional[str] = None

    def __str__(self) -> str:
        """格式化输出回复信息"""
        media_info = f" [{self.media_type}]" if self.has_media else ""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.sender_name}: {content_preview}{media_info}"


@dataclass
class UnreadMessage:
    """未读消息数据模型"""

    message_id: int
    content: str
    date: datetime

    sender_id: int
    sender_name: str

    chat_id: int
    chat_name: str

    sender_username: Optional[str] = None
    chat_username: Optional[str] = None

    is_user: bool = False
    is_group: bool = False
    is_channel: bool = False

    is_reply: bool = False
    is_forwarded: bool = False
    has_media: bool = False
    media_type: Optional[str] = None

    # 回复相关信息
    reply_to_msg_id: Optional[int] = None
    reply_info: Optional[ReplyInfo] = None

    raw_message: Optional[object] = field(default=None, repr=False)

    def __str__(self) -> str:
        """格式化输出消息信息"""
        chat_type = "用户" if self.is_user else "群组" if self.is_group else "频道"
        media_info = f" [{self.media_type}]" if self.has_media else ""

        # 构建基本消息信息
        result = (
            f"[{chat_type}] {self.chat_name}\n"
            f"  发送者: {self.sender_name}\n"
            f"  时间: {self.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # 如果是回复消息，添加被回复的消息信息
        if self.is_reply and self.reply_info:
            result += f"  ↩️ 回复 {self.reply_info}\n"

        result += f"  内容{media_info}: {self.content[:100]}{'...' if len(self.content) > 100 else ''}"

        return result

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            'message_id': self.message_id,
            'content': self.content,
            'date': self.date.isoformat(),
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'sender_username': self.sender_username,
            'chat_id': self.chat_id,
            'chat_name': self.chat_name,
            'chat_username': self.chat_username,
            'is_user': self.is_user,
            'is_group': self.is_group,
            'is_channel': self.is_channel,
            'is_reply': self.is_reply,
            'is_forwarded': self.is_forwarded,
            'has_media': self.has_media,
            'media_type': self.media_type,
            'reply_to_msg_id': self.reply_to_msg_id,
        }

        # 添加回复信息
        if self.reply_info:
            result['reply_info'] = {
                'message_id': self.reply_info.message_id,
                'content': self.reply_info.content,
                'sender_id': self.reply_info.sender_id,
                'sender_name': self.reply_info.sender_name,
                'sender_username': self.reply_info.sender_username,
                'date': self.reply_info.date.isoformat() if self.reply_info.date else None,
                'has_media': self.reply_info.has_media,
                'media_type': self.reply_info.media_type,
            }

        return result


@dataclass
class DialogInfo:
    """对话信息数据模型"""

    dialog_id: int
    name: str
    username: Optional[str] = None

    unread_count: int = 0
    unread_mentions_count: int = 0

    is_user: bool = False
    is_group: bool = False
    is_channel: bool = False

    is_pinned: bool = False
    is_archived: bool = False

    last_message_date: Optional[datetime] = None
    last_message_text: Optional[str] = None

    def __str__(self) -> str:
        """格式化输出对话信息"""
        chat_type = "用户" if self.is_user else "群组" if self.is_group else "频道"
        pinned_mark = "📌 " if self.is_pinned else ""
        archived_mark = "🗄️ " if self.is_archived else ""
        mention_info = (
            f", {self.unread_mentions_count} 次提及"
            if self.unread_mentions_count > 0
            else ""
        )

        return (
            f"{pinned_mark}{archived_mark}[{chat_type}] {self.name}\n"
            f"  未读: {self.unread_count} 条消息{mention_info}"
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'dialog_id': self.dialog_id,
            'name': self.name,
            'username': self.username,
            'unread_count': self.unread_count,
            'unread_mentions_count': self.unread_mentions_count,
            'is_user': self.is_user,
            'is_group': self.is_group,
            'is_channel': self.is_channel,
            'is_pinned': self.is_pinned,
            'is_archived': self.is_archived,
            'last_message_date': self.last_message_date.isoformat() if self.last_message_date else None,
            'last_message_text': self.last_message_text,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DialogInfo':
        """从字典创建 DialogInfo 实例"""
        from datetime import datetime
        last_message_date = data.get('last_message_date')
        if last_message_date and isinstance(last_message_date, str):
            last_message_date = datetime.fromisoformat(last_message_date)

        return cls(
            dialog_id=data['dialog_id'],
            name=data['name'],
            username=data.get('username'),
            unread_count=data.get('unread_count', 0),
            unread_mentions_count=data.get('unread_mentions_count', 0),
            is_user=data.get('is_user', False),
            is_group=data.get('is_group', False),
            is_channel=data.get('is_channel', False),
            is_pinned=data.get('is_pinned', False),
            is_archived=data.get('is_archived', False),
            last_message_date=last_message_date,
            last_message_text=data.get('last_message_text'),
        )

    def format_info(self) -> str:
        """格式化对话信息（用于 UI 显示）"""
        username_part = f" (@{self.username})" if self.username else ""
        return f"{self.name}{username_part} [ID: {self.dialog_id}]"
