"""
核心业务逻辑模块
"""
from .app import FishingApp
from .favorites import FavoritesManager
from .message_viewer import MessageViewer
from .send_handler import MessageSendHandler, MessageSenderWrapper
from .message_operator import MessageOperator
from .export_handler import ExportHandler

__all__ = [
    'FishingApp',
    'FavoritesManager',
    'MessageViewer',
    'MessageSendHandler',
    'MessageSenderWrapper',  # 向后兼容别名
    'MessageOperator',
    'ExportHandler',
]

