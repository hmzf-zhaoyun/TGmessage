"""
消息发送模块
提供发送消息的功能
"""
import logging
from typing import Optional, Union, List
from pathlib import Path

from telethon import errors
from telethon.tl.types import InputMediaUploadedPhoto, InputMediaUploadedDocument

from .client import TelegramClientWrapper
from .utils import handle_flood_wait, find_dialog
from .message_tracker import MessageTracker


logger = logging.getLogger(__name__)


class MessageSender:
    """消息发送器"""

    def __init__(self, client_wrapper: TelegramClientWrapper, enable_tracking: bool = True):
        """
        初始化消息发送器

        Args:
            client_wrapper: Telegram 客户端封装实例
            enable_tracking: 是否启用消息追踪(防止消息遗漏)
        """
        self.client_wrapper = client_wrapper
        self.enable_tracking = enable_tracking
        self.tracker = MessageTracker() if enable_tracking else None
    
    @property
    def client(self):
        """获取 Telegram 客户端"""
        return self.client_wrapper.client
    
    @handle_flood_wait
    async def send_text_message(
        self,
        dialog_identifier: Union[int, str],
        text: str,
        parse_mode: Optional[str] = 'md',
        link_preview: bool = True,
        reply_to: Optional[int] = None
    ) -> int:
        """
        发送文本消息
        
        Args:
            dialog_identifier: 对话标识符(ID/用户名/名称)
            text: 消息文本内容
            parse_mode: 解析模式('md' 为 Markdown, 'html' 为 HTML, None 为纯文本)
            link_preview: 是否显示链接预览
            reply_to: 回复的消息 ID
            
        Returns:
            发送的消息 ID
            
        Raises:
            ValueError: 找不到指定的对话
            errors.ChatWriteForbiddenError: 没有发送消息的权限
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")
        
        if not text or not text.strip():
            raise ValueError("消息内容不能为空")
        
        try:
            # 获取目标实体
            entity = await self._get_entity(dialog_identifier)
            
            # 发送消息
            message = await self.client.send_message(
                entity,
                text,
                parse_mode=parse_mode,
                link_preview=link_preview,
                reply_to=reply_to
            )
            
            logger.info(
                f"成功发送消息到 {dialog_identifier}, 消息 ID: {message.id}"
            )

            # 记录发送的消息(用于消息追踪)
            if self.enable_tracking and self.tracker:
                # 获取对话ID
                dialog_id = None
                if isinstance(dialog_identifier, int):
                    dialog_id = dialog_identifier
                else:
                    # 从entity获取ID
                    try:
                        from telethon import utils as tl_utils
                        dialog_id = tl_utils.get_peer_id(entity)
                    except Exception as e:
                        logger.warning(f"无法获取对话ID用于追踪: {e}")

                if dialog_id:
                    self.tracker.record_sent_message(dialog_id, message.id)
                    logger.debug(f"已记录发送消息: 对话 {dialog_id}, 消息 {message.id}")

            return message.id
            
        except errors.ChatWriteForbiddenError as e:
            logger.error(f"没有发送消息的权限: {e}")
            raise
        except errors.UserIsBlockedError as e:
            logger.error(f"用户已被封禁: {e}")
            raise
        except errors.RPCError as e:
            logger.error(f"发送消息失败: {e}")
            raise
    
    @handle_flood_wait
    async def send_photo(
        self,
        dialog_identifier: Union[int, str],
        photo: Union[str, Path, bytes],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = 'md',
        reply_to: Optional[int] = None
    ) -> int:
        """
        发送图片消息
        
        Args:
            dialog_identifier: 对话标识符
            photo: 图片文件路径、Path 对象或字节数据
            caption: 图片说明文字
            parse_mode: 解析模式
            reply_to: 回复的消息 ID
            
        Returns:
            发送的消息 ID
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")
        
        try:
            entity = await self._get_entity(dialog_identifier)
            
            # 发送图片
            message = await self.client.send_file(
                entity,
                photo,
                caption=caption,
                parse_mode=parse_mode,
                reply_to=reply_to
            )
            
            logger.info(
                f"成功发送图片到 {dialog_identifier}, 消息 ID: {message.id}"
            )
            
            return message.id
            
        except errors.RPCError as e:
            logger.error(f"发送图片失败: {e}")
            raise
    
    @handle_flood_wait
    async def send_file(
        self,
        dialog_identifier: Union[int, str],
        file: Union[str, Path],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = 'md',
        reply_to: Optional[int] = None,
        force_document: bool = False
    ) -> int:
        """
        发送文件消息
        
        Args:
            dialog_identifier: 对话标识符
            file: 文件路径或 Path 对象
            caption: 文件说明文字
            parse_mode: 解析模式
            reply_to: 回复的消息 ID
            force_document: 是否强制作为文档发送(否则图片/视频会压缩)
            
        Returns:
            发送的消息 ID
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")
        
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file}")
        
        try:
            entity = await self._get_entity(dialog_identifier)
            
            # 发送文件
            message = await self.client.send_file(
                entity,
                str(file_path),
                caption=caption,
                parse_mode=parse_mode,
                reply_to=reply_to,
                force_document=force_document
            )
            
            logger.info(
                f"成功发送文件 '{file_path.name}' 到 {dialog_identifier}, "
                f"消息 ID: {message.id}"
            )
            
            return message.id
            
        except errors.RPCError as e:
            logger.error(f"发送文件失败: {e}")
            raise

    @handle_flood_wait
    async def forward_message(
        self,
        from_dialog: Union[int, str],
        to_dialog: Union[int, str],
        message_ids: Union[int, List[int]]
    ) -> List[int]:
        """
        转发消息

        Args:
            from_dialog: 源对话标识符
            to_dialog: 目标对话标识符
            message_ids: 消息 ID 或 ID 列表

        Returns:
            转发后的消息 ID 列表
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")

        # 确保 message_ids 是列表
        if isinstance(message_ids, int):
            message_ids = [message_ids]

        try:
            from_entity = await self._get_entity(from_dialog)
            to_entity = await self._get_entity(to_dialog)

            # 转发消息
            forwarded = await self.client.forward_messages(
                to_entity,
                message_ids,
                from_entity
            )

            # 提取转发后的消息 ID
            if isinstance(forwarded, list):
                forwarded_ids = [msg.id for msg in forwarded]
            else:
                forwarded_ids = [forwarded.id]

            logger.info(
                f"成功转发 {len(forwarded_ids)} 条消息 "
                f"从 {from_dialog} 到 {to_dialog}"
            )

            return forwarded_ids

        except errors.RPCError as e:
            logger.error(f"转发消息失败: {e}")
            raise

    @handle_flood_wait
    async def delete_messages(
        self,
        dialog_identifier: Union[int, str],
        message_ids: Union[int, List[int]],
        revoke: bool = True
    ) -> int:
        """
        删除消息

        Args:
            dialog_identifier: 对话标识符
            message_ids: 消息 ID 或 ID 列表
            revoke: 是否对所有人删除(True 为双向删除,False 为只删除自己这边)

        Returns:
            成功删除的消息数量
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")

        # 确保 message_ids 是列表
        if isinstance(message_ids, int):
            message_ids = [message_ids]

        try:
            entity = await self._get_entity(dialog_identifier)

            # 删除消息
            deleted = await self.client.delete_messages(
                entity,
                message_ids,
                revoke=revoke
            )

            # deleted 是一个 messages.AffectedMessages 对象
            count = len(message_ids) if deleted else 0

            logger.info(
                f"成功删除 {count} 条消息 "
                f"({'双向删除' if revoke else '单向删除'})"
            )

            return count

        except errors.RPCError as e:
            logger.error(f"删除消息失败: {e}")
            raise

    @handle_flood_wait
    async def edit_message(
        self,
        dialog_identifier: Union[int, str],
        message_id: int,
        new_text: str,
        parse_mode: Optional[str] = 'md'
    ) -> bool:
        """
        编辑消息

        Args:
            dialog_identifier: 对话标识符
            message_id: 要编辑的消息 ID
            new_text: 新的消息文本
            parse_mode: 解析模式

        Returns:
            是否编辑成功
        """
        if not self.client_wrapper.is_connected:
            raise RuntimeError("客户端未连接,请先调用 connect()")

        if not new_text or not new_text.strip():
            raise ValueError("新消息内容不能为空")

        try:
            entity = await self._get_entity(dialog_identifier)

            # 编辑消息
            message = await self.client.edit_message(
                entity,
                message_id,
                new_text,
                parse_mode=parse_mode
            )

            logger.info(f"成功编辑消息 {message_id}")

            return message is not None

        except errors.MessageNotModifiedError:
            logger.warning("消息内容未改变")
            return False
        except errors.MessageAuthorRequiredError:
            logger.error("只能编辑自己发送的消息")
            return False
        except errors.RPCError as e:
            logger.error(f"编辑消息失败: {e}")
            raise

    async def _get_entity(self, identifier: Union[int, str]):
        """
        根据标识符获取实体

        Args:
            identifier: 对话 ID、用户名或名称

        Returns:
            Telegram 实体对象

        Raises:
            ValueError: 找不到指定的对话
        """
        try:
            # 尝试直接获取实体
            entity = await self.client.get_entity(identifier)
            return entity
        except Exception as e:
            logger.warning("获取实体失败 %s: %s", identifier, e)

        dialog = await find_dialog(self.client, identifier)
        if dialog is None:
            logger.error("解析对话失败 %s", identifier)
            raise ValueError(f"找不到对话: {identifier}")

        return dialog.entity
