"""
主入口模块
提供便捷的 API 和使用示例
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Union
from pathlib import Path

from .client import TelegramClientWrapper
from .message_fetcher import MessageFetcher
from .message_sender import MessageSender
from .message_exporter import MessageExporter, ExportFormat, _get_formatter
from .models import UnreadMessage, DialogInfo, FolderInfo
from .config import Config, get_config


logger = logging.getLogger(__name__)


class TelegramUnreadMessageAPI:
    """Telegram 未读消息 API 封装"""

    def __init__(self, config: Optional[Config] = None, enable_message_tracking: bool = True):
        """
        初始化 API

        Args:
            config: 配置对象,默认使用环境变量配置
            enable_message_tracking: 是否启用消息追踪(防止消息遗漏),默认启用
        """
        self.config = config or get_config()
        self.client_wrapper = TelegramClientWrapper(self.config)
        self.message_fetcher = MessageFetcher(self.client_wrapper, enable_tracking=enable_message_tracking)
        self.message_sender = MessageSender(self.client_wrapper, enable_tracking=enable_message_tracking)
        self._message_exporter: Optional[MessageExporter] = None

    @property
    def message_exporter(self) -> MessageExporter:
        """获取消息导出器（延迟初始化）"""
        if self._message_exporter is None:
            self._message_exporter = MessageExporter(self.client_wrapper)
        return self._message_exporter
    
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

    # 文件夹/分组相关方法

    async def get_folders(self) -> List[FolderInfo]:
        """
        获取所有对话文件夹/分组

        Returns:
            FolderInfo 列表
        """
        return await self.message_fetcher.get_folders()

    async def get_dialogs_by_folder(
        self,
        folder_id: int,
        include_unread_only: bool = False
    ) -> List[DialogInfo]:
        """
        获取指定文件夹中的对话列表

        Args:
            folder_id: 文件夹ID
            include_unread_only: 是否只返回有未读消息的对话

        Returns:
            DialogInfo 列表
        """
        return await self.message_fetcher.get_dialogs_by_folder(
            folder_id=folder_id,
            include_unread_only=include_unread_only
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

    # 消息导出相关方法

    async def export_messages(
        self,
        dialog: Union[int, str],
        output_path: Union[str, Path],
        fmt: Union[ExportFormat, str] = ExportFormat.JSON,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        download_media: bool = False,
        media_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        导出对话消息到文件

        Args:
            dialog: 对话标识符（ID/用户名/名称）
            output_path: 输出文件路径或目录
            fmt: 导出格式（json/txt/csv/md）
            limit: 最大消息数量
            start_date: 开始时间
            end_date: 结束时间
            download_media: 是否下载媒体文件
            media_dir: 媒体文件保存目录

        Returns:
            导出文件的路径
        """
        # 支持字符串格式转换
        if isinstance(fmt, str):
            fmt = ExportFormat(fmt.lower())

        return await self.message_exporter.export_to_file(
            dialog_identifier=dialog,
            output_path=output_path,
            fmt=fmt,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            download_media=download_media,
            media_dir=media_dir,
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


async def edit_message(
    dialog: Union[int, str],
    message_id: int,
    new_text: str,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    parse_mode: Optional[str] = 'md',
    config: Optional[Config] = None
) -> bool:
    """
    编辑消息(便捷函数)

    Args:
        dialog: 对话标识符
        message_id: 要编辑的消息 ID
        new_text: 新的消息文本
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        parse_mode: 解析模式
        config: 配置对象

    Returns:
        是否编辑成功
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.edit_message(
            dialog=dialog,
            message_id=message_id,
            new_text=new_text,
            parse_mode=parse_mode
        )


async def delete_messages(
    dialog: Union[int, str],
    message_ids: Union[int, List[int]],
    phone: Optional[str] = None,
    password: Optional[str] = None,
    revoke: bool = True,
    config: Optional[Config] = None
) -> int:
    """
    删除消息(便捷函数)

    Args:
        dialog: 对话标识符
        message_ids: 消息 ID 或 ID 列表
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        revoke: 是否对所有人删除(True 为双向删除,False 为只删除自己这边)
        config: 配置对象

    Returns:
        成功删除的消息数量
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.delete_messages(
            dialog=dialog,
            message_ids=message_ids,
            revoke=revoke
        )


async def forward_message(
    from_dialog: Union[int, str],
    to_dialog: Union[int, str],
    message_ids: Union[int, List[int]],
    phone: Optional[str] = None,
    password: Optional[str] = None,
    config: Optional[Config] = None
) -> List[int]:
    """
    转发消息(便捷函数)

    Args:
        from_dialog: 源对话标识符
        to_dialog: 目标对话标识符
        message_ids: 消息 ID 或 ID 列表
        phone: 手机号码(首次登录需要)
        password: 两步验证密码
        config: 配置对象

    Returns:
        转发后的消息 ID 列表
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.forward_message(
            from_dialog=from_dialog,
            to_dialog=to_dialog,
            message_ids=message_ids
        )


async def export_messages(
    dialog: Union[int, str],
    output_path: Union[str, Path],
    fmt: Union[ExportFormat, str] = ExportFormat.JSON,
    limit: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    download_media: bool = False,
    media_dir: Optional[Union[str, Path]] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    config: Optional[Config] = None,
) -> Path:
    """
    导出对话消息到文件（便捷函数）

    Args:
        dialog: 对话标识符（ID/用户名/名称）
        output_path: 输出文件路径或目录
        fmt: 导出格式（json/txt/csv/md 或 ExportFormat 枚举）
        limit: 最大消息数量
        start_date: 开始时间
        end_date: 结束时间
        download_media: 是否下载媒体文件
        media_dir: 媒体文件保存目录
        phone: 手机号码（首次登录需要）
        password: 两步验证密码
        config: 配置对象

    Returns:
        导出文件的路径
    """
    async with TelegramUnreadMessageAPI(config) as api:
        if phone:
            await api.connect(phone=phone, password=password)
        return await api.export_messages(
            dialog=dialog,
            output_path=output_path,
            fmt=fmt,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            download_media=download_media,
            media_dir=media_dir,
        )
