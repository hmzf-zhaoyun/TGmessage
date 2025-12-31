"""
主入口模块
提供便捷的 API 和使用示例
"""
import asyncio
import logging
from typing import List, Optional, Union
from pathlib import Path

from .client import TelegramClientWrapper
from .message_fetcher import MessageFetcher
from .message_sender import MessageSender
from .models import UnreadMessage, DialogInfo
from .config import Config, get_config


logger = logging.getLogger(__name__)


class TelegramUnreadMessageAPI:
    """Telegram 未读消息 API 封装"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化 API

        Args:
            config: 配置对象,默认使用环境变量配置
        """
        self.config = config or get_config()
        self.client_wrapper = TelegramClientWrapper(self.config)
        self.message_fetcher = MessageFetcher(self.client_wrapper)
        self.message_sender = MessageSender(self.client_wrapper)
    
    async def connect(
        self,
        phone: Optional[str] = None,
        password: Optional[str] = None
    ) -> 'TelegramUnreadMessageAPI':
        """
        连接到 Telegram
        
        Args:
            phone: 手机号码(首次登录需要)
            password: 两步验证密码(如果启用)
            
        Returns:
            self,支持链式调用
        """
        await self.client_wrapper.connect(phone=phone, password=password)
        return self
    
    async def disconnect(self):
        """断开连接"""
        await self.client_wrapper.disconnect()
    
    async def get_all_unread_dialogs(
        self,
        include_archived: bool = False
    ) -> List[DialogInfo]:
        """
        获取所有有未读消息的对话
        
        Args:
            include_archived: 是否包含已归档的对话
            
        Returns:
            DialogInfo 列表
        """
        return await self.message_fetcher.get_all_unread_dialogs(
            include_archived=include_archived
        )
    
    async def get_unread_messages(
        self,
        dialog: Optional[Union[int, str]] = None,
        limit: Optional[int] = None,
        include_archived: bool = False
    ) -> List[UnreadMessage]:
        """
        获取未读消息
        
        Args:
            dialog: 对话标识符(ID/用户名/名称),为 None 时获取所有对话的未读消息
            limit: 限制消息数量
            include_archived: 是否包含已归档对话(仅当 dialog 为 None 时有效)
            
        Returns:
            UnreadMessage 列表
        """
        if dialog is None:
            return await self.message_fetcher.get_all_unread_messages(
                include_archived=include_archived,
                limit_per_dialog=limit
            )
        else:
            return await self.message_fetcher.get_unread_messages_from_dialog(
                dialog_identifier=dialog,
                limit=limit
            )

    async def mark_dialog_read(
        self,
        dialog: Union[int, str],
        max_message_id: Optional[int] = None
    ) -> None:
        """
        标记指定对话为已读

        Args:
            dialog: 对话标识符
            max_message_id: 读取到的最大消息 ID,为 None 时标记所有未读
        """
        await self.message_fetcher.mark_dialog_read(
            dialog_identifier=dialog,
            max_message_id=max_message_id
        )

    # 发送消息相关方法

    async def send_message(
        self,
        dialog: Union[int, str],
        text: str,
        parse_mode: Optional[str] = 'md',
        reply_to: Optional[int] = None
    ) -> int:
        """
        发送文本消息

        Args:
            dialog: 对话标识符
            text: 消息文本
            parse_mode: 解析模式('md' 或 'html')
            reply_to: 回复的消息 ID

        Returns:
            发送的消息 ID
        """
        return await self.message_sender.send_text_message(
            dialog_identifier=dialog,
            text=text,
            parse_mode=parse_mode,
            reply_to=reply_to
        )

    async def send_photo(
        self,
        dialog: Union[int, str],
        photo: Union[str, Path],
        caption: Optional[str] = None,
        reply_to: Optional[int] = None
    ) -> int:
        """
        发送图片

        Args:
            dialog: 对话标识符
            photo: 图片文件路径
            caption: 图片说明
            reply_to: 回复的消息 ID

        Returns:
            发送的消息 ID
        """
        return await self.message_sender.send_photo(
            dialog_identifier=dialog,
            photo=photo,
            caption=caption,
            reply_to=reply_to
        )

    async def send_file(
        self,
        dialog: Union[int, str],
        file: Union[str, Path],
        caption: Optional[str] = None,
        reply_to: Optional[int] = None
    ) -> int:
        """
        发送文件

        Args:
            dialog: 对话标识符
            file: 文件路径
            caption: 文件说明
            reply_to: 回复的消息 ID

        Returns:
            发送的消息 ID
        """
        return await self.message_sender.send_file(
            dialog_identifier=dialog,
            file=file,
            caption=caption,
            reply_to=reply_to
        )

    async def forward_message(
        self,
        from_dialog: Union[int, str],
        to_dialog: Union[int, str],
        message_ids: Union[int, List[int]]
    ) -> List[int]:
        """
        转发消息

        Args:
            from_dialog: 源对话
            to_dialog: 目标对话
            message_ids: 消息 ID 或 ID 列表

        Returns:
            转发后的消息 ID 列表
        """
        return await self.message_sender.forward_message(
            from_dialog=from_dialog,
            to_dialog=to_dialog,
            message_ids=message_ids
        )

    async def delete_messages(
        self,
        dialog: Union[int, str],
        message_ids: Union[int, List[int]],
        revoke: bool = True
    ) -> int:
        """
        删除消息

        Args:
            dialog: 对话标识符
            message_ids: 消息 ID 或 ID 列表
            revoke: 是否对所有人删除

        Returns:
            成功删除的消息数量
        """
        return await self.message_sender.delete_messages(
            dialog_identifier=dialog,
            message_ids=message_ids,
            revoke=revoke
        )

    async def edit_message(
        self,
        dialog: Union[int, str],
        message_id: int,
        new_text: str,
        parse_mode: Optional[str] = 'md'
    ) -> bool:
        """
        编辑消息

        Args:
            dialog: 对话标识符
            message_id: 消息 ID
            new_text: 新的消息文本
            parse_mode: 解析模式

        Returns:
            是否编辑成功
        """
        return await self.message_sender.edit_message(
            dialog_identifier=dialog,
            message_id=message_id,
            new_text=new_text,
            parse_mode=parse_mode
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return await self.connect()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


# 便捷函数


async def get_unread_dialogs(
    phone: Optional[str] = None,
    password: Optional[str] = None,
    include_archived: bool = False,
    config: Optional[Config] = None
) -> List[DialogInfo]:
    """
    获取所有有未读消息的对话(便捷函数)
    
    Args:
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        include_archived: 是否包含已归档对话
        config: 配置对象
        
    Returns:
        DialogInfo 列表
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.get_all_unread_dialogs(include_archived=include_archived)


async def get_unread_messages(
    dialog: Optional[Union[int, str]] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    limit: Optional[int] = None,
    include_archived: bool = False,
    config: Optional[Config] = None
) -> List[UnreadMessage]:
    """
    获取未读消息(便捷函数)
    
    Args:
        dialog: 对话标识符,为 None 时获取所有对话的未读消息
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        limit: 限制消息数量
        include_archived: 是否包含已归档对话
        config: 配置对象
        
    Returns:
        UnreadMessage 列表
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.get_unread_messages(
            dialog=dialog,
            limit=limit,
            include_archived=include_archived
        )


# 发送消息便捷函数


async def send_message(
    dialog: Union[int, str],
    text: str,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    parse_mode: Optional[str] = 'md',
    reply_to: Optional[int] = None,
    config: Optional[Config] = None
) -> int:
    """
    发送文本消息(便捷函数)

    Args:
        dialog: 对话标识符
        text: 消息文本
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        parse_mode: 解析模式
        reply_to: 回复的消息 ID
        config: 配置对象

    Returns:
        发送的消息 ID
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.send_message(
            dialog=dialog,
            text=text,
            parse_mode=parse_mode,
            reply_to=reply_to
        )


async def send_photo(
    dialog: Union[int, str],
    photo: Union[str, Path],
    caption: Optional[str] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    config: Optional[Config] = None
) -> int:
    """
    发送图片(便捷函数)

    Args:
        dialog: 对话标识符
        photo: 图片文件路径
        caption: 图片说明
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        config: 配置对象

    Returns:
        发送的消息 ID
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.send_photo(
            dialog=dialog,
            photo=photo,
            caption=caption
        )


async def send_file(
    dialog: Union[int, str],
    file: Union[str, Path],
    caption: Optional[str] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    config: Optional[Config] = None
) -> int:
    """
    发送文件(便捷函数)

    Args:
        dialog: 对话标识符
        file: 文件路径
        caption: 文件说明
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        config: 配置对象

    Returns:
        发送的消息 ID
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.send_file(
            dialog=dialog,
            file=file,
            caption=caption
        )
