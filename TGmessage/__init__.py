"""
TGmessage - Telegram 未读消息获取工具

提供便捷的 API 来获取 Telegram 的未读消息和发送消息
"""

__version__ = '1.0.0'
__author__ = 'Your Name'

from .config import Config, get_config
from .models import UnreadMessage, DialogInfo
from .client import TelegramClientWrapper
from .message_fetcher import MessageFetcher
from .message_sender import MessageSender
from .main import (
    TelegramUnreadMessageAPI,
    get_unread_dialogs,
    get_unread_messages,
    send_message,
    send_photo,
    send_file,
)

__all__ = [
    'Config',
    'get_config',
    'UnreadMessage',
    'DialogInfo',
    'TelegramClientWrapper',
    'MessageFetcher',
    'MessageSender',
    'TelegramUnreadMessageAPI',
    'get_unread_dialogs',
    'get_unread_messages',
    'send_message',
    'send_photo',
    'send_file',
]
