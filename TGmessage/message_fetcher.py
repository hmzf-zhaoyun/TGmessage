"""
未读消息获取核心模块
提供获取未读消息的主要功能
"""
import logging
from typing import List, Optional, Union

from telethon import errors, utils
from telethon.tl.types import (
    User, Chat, Channel,
    InputPeerUser, InputPeerChat, InputPeerChannel
)

from .client import TelegramClientWrapper
from .models import UnreadMessage, DialogInfo
from .utils import handle_flood_wait, get_media_type


logger = logging.getLogger(__name__)


class MessageFetcher:
    """未读消息获取器"""
    
    def __init__(self, client_wrapper: TelegramClientWrapper):
        """
        初始化消息获取器
        
        Args:
            client_wrapper: Telegram 客户端封装实例
        """
        self.client_wrapper = client_wrapper
    
    @property
    def client(self):
        """获取 Telegram 客户端"""
        return self.client_wrapper.client
    
    @handle_flood_wait
    async def get_all_unread_dialogs(
        self,
        include_archived: bool = False,
        include_muted: bool = True
    ) -> List[DialogInfo]:
        """
        获取所有有未读消息的对话信息
        
        Args:
            include_archived: 是否包含已归档的对话
            include_muted: 是否包含已静音的对话
            
        Returns:
            DialogInfo 列表
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")
        
        unread_dialogs = []
        
        logger.info("正在获取所有对话...")
        
        try:
            async for dialog in self.client.iter_dialogs():
                # 跳过没有未读消息的对话
                if dialog.unread_count == 0:
                    continue
                
                # 根据参数过滤归档对话
                if not include_archived and dialog.archived:
                    continue
                
                # 转换为 DialogInfo 对象
                dialog_info = self._create_dialog_info(dialog)
                unread_dialogs.append(dialog_info)
                
                logger.debug(
                    f"发现未读对话: {dialog_info.name}, "
                    f"未读数: {dialog_info.unread_count}"
                )
            
            logger.info(f"共找到 {len(unread_dialogs)} 个有未读消息的对话")
            return unread_dialogs
            
        except errors.RPCError as e:
            logger.error(f"获取对话列表失败: {e}")
            raise
    
    @handle_flood_wait
    async def get_unread_messages_from_dialog(
        self,
        dialog_identifier: Union[int, str],
        limit: Optional[int] = None
    ) -> List[UnreadMessage]:
        """
        从指定对话获取未读消息
        
        Args:
            dialog_identifier: 对话标识符,可以是:
                - 对话 ID (int)
                - 用户名 (str, 如 'username' 或 '@username')
                - 对话名称 (str)
            limit: 最多获取的消息数量,None 表示获取所有未读消息
            
        Returns:
            UnreadMessage 列表
            
        Raises:
            ValueError: 找不到指定的对话
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")
        
        try:
            # 查找对话
            dialog = await self._find_dialog(dialog_identifier)
            if dialog is None:
                raise ValueError(f"找不到对话: {dialog_identifier}")
            
            logger.info(
                f"正在获取对话 '{dialog.name}' 的未读消息 "
                f"(未读数: {dialog.unread_count})..."
            )
            
            if dialog.unread_count == 0:
                logger.info("该对话没有未读消息")
                return []
            
            # 确定获取消息的数量
            fetch_limit = min(limit, dialog.unread_count) if limit else dialog.unread_count
            
            # 获取未读消息
            unread_messages = []
            async for message in self.client.iter_messages(
                dialog.entity,
                limit=fetch_limit
            ):
                # Telethon 没有直接的"未读"标记
                # 我们获取最近的 N 条消息,其中 N 是未读计数
                unread_msg = self._create_unread_message(message, dialog)
                unread_messages.append(unread_msg)
            
            # 反转列表,使消息按时间从旧到新排列
            unread_messages.reverse()
            
            logger.info(f"成功获取 {len(unread_messages)} 条未读消息")
            return unread_messages
            
        except errors.RPCError as e:
            logger.error(f"获取未读消息失败: {e}")
            raise

    @handle_flood_wait
    async def mark_dialog_read(
        self,
        dialog_identifier: Union[int, str],
        max_message_id: Optional[int] = None
    ) -> None:
        """
        标记指定对话为已读

        Args:
            dialog_identifier: 对话标识符(对话 ID/用户名/名称)
            max_message_id: 读取到的最大消息 ID,为 None 时标记所有未读

        Raises:
            ValueError: 找不到指定的对话
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")

        dialog = await self._find_dialog(dialog_identifier)
        if dialog is None:
            raise ValueError(f"找不到对话: {dialog_identifier}")

        if max_message_id is not None and max_message_id <= 0:
            raise ValueError("max_message_id 必须为正整数")

        if max_message_id is None:
            await self.client.send_read_acknowledge(dialog.entity)
        else:
            await self.client.send_read_acknowledge(dialog.entity, max_id=max_message_id)

        logger.info(f"已标记对话 '{dialog.name}' 为已读")

    @handle_flood_wait
    async def get_all_unread_messages(
        self,
        include_archived: bool = False,
        limit_per_dialog: Optional[int] = None
    ) -> List[UnreadMessage]:
        """
        获取所有对话的未读消息

        Args:
            include_archived: 是否包含已归档的对话
            limit_per_dialog: 每个对话最多获取的消息数量

        Returns:
            UnreadMessage 列表,按对话分组并按时间排序
        """
        # 先获取所有有未读消息的对话
        unread_dialogs = await self.get_all_unread_dialogs(
            include_archived=include_archived
        )

        if not unread_dialogs:
            logger.info("没有未读消息")
            return []

        all_messages = []

        for dialog_info in unread_dialogs:
            try:
                messages = await self.get_unread_messages_from_dialog(
                    dialog_info.dialog_id,
                    limit=limit_per_dialog
                )
                all_messages.extend(messages)
            except Exception as e:
                logger.warning(
                    f"获取对话 '{dialog_info.name}' 的未读消息失败: {e}"
                )
                continue

        logger.info(f"共获取 {len(all_messages)} 条未读消息")
        return all_messages

    async def _find_dialog(self, identifier: Union[int, str]):
        """
        根据标识符查找对话

        Args:
            identifier: 对话 ID、用户名或名称

        Returns:
            Dialog 对象或 None
        """
        # 如果是整数,直接作为 ID 查找
        if isinstance(identifier, int):
            try:
                entity = await self.client.get_entity(identifier)
                dialogs = await self.client.get_dialogs()
                for dialog in dialogs:
                    if dialog.id == identifier:
                        return dialog
            except Exception as e:
                logger.warning(f"通过 ID {identifier} 查找对话失败: {e}")
                return None

        # 如果是字符串,尝试多种方式查找
        identifier_str = str(identifier).strip()

        # 移除 @ 前缀(如果有)
        if identifier_str.startswith('@'):
            identifier_str = identifier_str[1:]

        # 遍历所有对话查找匹配项
        async for dialog in self.client.iter_dialogs():
            # 检查用户名匹配
            entity = dialog.entity
            if hasattr(entity, 'username') and entity.username:
                if entity.username.lower() == identifier_str.lower():
                    return dialog

            # 检查名称匹配
            if dialog.name.lower() == identifier_str.lower():
                return dialog

        return None

    def _create_dialog_info(self, dialog) -> DialogInfo:
        """
        从 Telethon Dialog 对象创建 DialogInfo

        Args:
            dialog: Telethon Dialog 对象

        Returns:
            DialogInfo 实例
        """
        entity = dialog.entity
        username = getattr(entity, 'username', None)

        return DialogInfo(
            dialog_id=dialog.id,
            name=dialog.name,
            username=username,
            unread_count=dialog.unread_count,
            unread_mentions_count=dialog.unread_mentions_count,
            is_user=dialog.is_user,
            is_group=dialog.is_group,
            is_channel=dialog.is_channel,
            is_pinned=dialog.pinned,
            is_archived=dialog.archived,
            last_message_date=dialog.date,
            last_message_text=dialog.message.message if dialog.message else None,
        )

    def _create_unread_message(self, message, dialog) -> UnreadMessage:
        """
        从 Telethon Message 对象创建 UnreadMessage

        Args:
            message: Telethon Message 对象
            dialog: Telethon Dialog 对象

        Returns:
            UnreadMessage 实例
        """
        # 获取发送者信息
        sender = message.sender
        sender_name = utils.get_display_name(sender) if sender else "Unknown"
        sender_username = getattr(sender, 'username', None)

        # 获取消息内容
        content = message.message or ""

        # 检查媒体类型
        has_media = message.media is not None
        media_type = get_media_type(message) if has_media else None

        return UnreadMessage(
            message_id=message.id,
            content=content,
            date=message.date,
            sender_id=message.sender_id or 0,
            sender_name=sender_name,
            sender_username=sender_username,
            chat_id=dialog.id,
            chat_name=dialog.name,
            chat_username=getattr(dialog.entity, 'username', None),
            is_user=dialog.is_user,
            is_group=dialog.is_group,
            is_channel=dialog.is_channel,
            is_reply=message.is_reply,
            is_forwarded=message.forward is not None,
            has_media=has_media,
            media_type=media_type,
            raw_message=message,
        )
