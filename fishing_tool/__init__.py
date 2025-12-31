"""
TGmessage 摸鱼工具 - 重构版

功能特性:
- 📬 自动显示消息回复链（谁回复了谁的消息）
- 💬 支持 @ 提及用户
- ✏️ 支持编辑、删除、转发消息（通过 API）
- ⭐ 收藏常用对话
- 📨 发送消息
"""
from .core import FishingApp
from .ui import InteractiveShell
from .models import DialogInfo

__version__ = '2.0.0'
__all__ = ['FishingApp', 'InteractiveShell', 'DialogInfo']

