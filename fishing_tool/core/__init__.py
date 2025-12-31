"""
核心业务逻辑模块
"""
from .app import FishingApp
from .favorites import FavoritesManager
from .message_viewer import MessageViewer
from .message_sender import MessageSenderWrapper
from .message_operator import MessageOperator

__all__ = [
    'FishingApp',
    'FavoritesManager',
    'MessageViewer',
    'MessageSenderWrapper',
    'MessageOperator'
]

