"""
消息导出模块
提供消息导出功能，支持多种格式和媒体下载
"""
import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from .client import TelegramClientWrapper
from .models import UnreadMessage, DialogInfo
from .utils import handle_flood_wait, find_dialog, get_media_type

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """导出格式枚举"""
    JSON = "json"
    TXT = "txt"
    CSV = "csv"
    MARKDOWN = "md"


class BaseFormatter(ABC):
    """导出格式化器基类"""

    @abstractmethod
    def format(self, messages: List[UnreadMessage], dialog_info: DialogInfo) -> str:
        """格式化消息列表"""
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """获取文件扩展名"""
        pass


class JsonFormatter(BaseFormatter):
    """JSON 格式化器"""

    def format(self, messages: List[UnreadMessage], dialog_info: DialogInfo) -> str:
        data = {
            "dialog": dialog_info.to_dict(),
            "export_time": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": [msg.to_dict() for msg in messages],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def get_extension(self) -> str:
        return ".json"


class TxtFormatter(BaseFormatter):
    """纯文本格式化器"""

    def format(self, messages: List[UnreadMessage], dialog_info: DialogInfo) -> str:
        lines = [
            f"对话: {dialog_info.name}",
            f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"消息数量: {len(messages)}",
            "=" * 60,
            "",
        ]

        for msg in messages:
            time_str = msg.date.strftime('%Y-%m-%d %H:%M:%S')
            media_info = f" [{msg.media_type}]" if msg.has_media else ""
            lines.append(f"[{time_str}] {msg.sender_name}{media_info}")
            if msg.is_reply and msg.reply_info:
                lines.append(f"  ↩️ 回复: {msg.reply_info.sender_name}: {msg.reply_info.content[:50]}...")
            lines.append(f"  {msg.content}")
            lines.append("")

        return "\n".join(lines)

    def get_extension(self) -> str:
        return ".txt"


class CsvFormatter(BaseFormatter):
    """CSV 格式化器"""

    def format(self, messages: List[UnreadMessage], dialog_info: DialogInfo) -> str:
        import io
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow([
            "消息ID", "时间", "发送者", "发送者用户名", "内容",
            "是否回复", "回复消息ID", "是否转发", "媒体类型"
        ])

        for msg in messages:
            writer.writerow([
                msg.message_id,
                msg.date.strftime('%Y-%m-%d %H:%M:%S'),
                msg.sender_name,
                msg.sender_username or "",
                msg.content,
                "是" if msg.is_reply else "否",
                msg.reply_to_msg_id or "",
                "是" if msg.is_forwarded else "否",
                msg.media_type or "",
            ])

        return output.getvalue()

    def get_extension(self) -> str:
        return ".csv"


class MarkdownFormatter(BaseFormatter):
    """Markdown 格式化器"""

    def format(self, messages: List[UnreadMessage], dialog_info: DialogInfo) -> str:
        chat_type = "用户" if dialog_info.is_user else "群组" if dialog_info.is_group else "频道"
        lines = [
            f"# {dialog_info.name}",
            "",
            f"- **类型**: {chat_type}",
            f"- **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **消息数量**: {len(messages)}",
            "",
            "---",
            "",
        ]

        current_date = None
        for msg in messages:
            msg_date = msg.date.strftime('%Y-%m-%d')
            if msg_date != current_date:
                current_date = msg_date
                lines.append(f"## {msg_date}")
                lines.append("")

            time_str = msg.date.strftime('%H:%M:%S')
            media_badge = f" `{msg.media_type}`" if msg.has_media else ""

            lines.append(f"### [{time_str}] {msg.sender_name}{media_badge}")
            lines.append("")

            if msg.is_reply and msg.reply_info:
                reply_preview = msg.reply_info.content[:80].replace('\n', ' ')
                lines.append(f"> ↩️ **{msg.reply_info.sender_name}**: {reply_preview}")
                lines.append("")

            content = msg.content.replace('\n', '\n> ') if '\n' in msg.content else msg.content
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    def get_extension(self) -> str:
        return ".md"




def _get_formatter(fmt: ExportFormat) -> BaseFormatter:
    """获取对应格式的格式化器"""
    formatters = {
        ExportFormat.JSON: JsonFormatter(),
        ExportFormat.TXT: TxtFormatter(),
        ExportFormat.CSV: CsvFormatter(),
        ExportFormat.MARKDOWN: MarkdownFormatter(),
    }
    return formatters[fmt]


class MessageExporter:
    """消息导出器"""

    def __init__(self, client_wrapper: TelegramClientWrapper):
        """
        初始化消息导出器

        Args:
            client_wrapper: Telegram 客户端封装实例
        """
        self.client_wrapper = client_wrapper

    @property
    def client(self):
        """获取 Telegram 客户端"""
        return self.client_wrapper.client

    @handle_flood_wait
    async def fetch_messages(
        self,
        dialog_identifier: Union[int, str],
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[UnreadMessage], DialogInfo]:
        """
        获取对话消息（支持时间范围筛选）

        Args:
            dialog_identifier: 对话标识符
            limit: 最大消息数量
            start_date: 开始时间（包含）
            end_date: 结束时间（包含）

        Returns:
            (消息列表, 对话信息)
        """
        from .models import ReplyInfo
        from telethon import utils

        dialog = await find_dialog(self.client, dialog_identifier)
        if dialog is None:
            raise ValueError(f"找不到对话: {dialog_identifier}")

        entity = dialog.entity
        dialog_info = DialogInfo(
            dialog_id=dialog.id,
            name=dialog.name,
            username=getattr(entity, 'username', None),
            is_user=dialog.is_user,
            is_group=dialog.is_group,
            is_channel=dialog.is_channel,
        )

        logger.info(f"正在获取对话 '{dialog.name}' 的消息...")

        messages = []
        async for message in self.client.iter_messages(
            dialog.entity,
            limit=limit,
            offset_date=end_date,
            reverse=False,
        ):
            # 时间范围筛选
            if start_date and message.date.replace(tzinfo=None) < start_date:
                break
            if end_date and message.date.replace(tzinfo=None) > end_date:
                continue

            # 构建消息对象
            sender = message.sender
            sender_name = utils.get_display_name(sender) if sender else "Unknown"

            reply_info = None
            if message.is_reply and message.reply_to:
                try:
                    replied_msg = await message.get_reply_message()
                    if replied_msg:
                        reply_sender = replied_msg.sender
                        reply_info = ReplyInfo(
                            message_id=replied_msg.id,
                            content=replied_msg.message or "",
                            sender_id=replied_msg.sender_id or 0,
                            sender_name=utils.get_display_name(reply_sender) if reply_sender else "Unknown",
                            sender_username=getattr(reply_sender, 'username', None),
                            date=replied_msg.date,
                            has_media=replied_msg.media is not None,
                            media_type=get_media_type(replied_msg) if replied_msg.media else None,
                        )
                except Exception as e:
                    logger.warning(f"获取回复消息失败: {e}")

            msg = UnreadMessage(
                message_id=message.id,
                content=message.message or "",
                date=message.date.replace(tzinfo=None),
                sender_id=message.sender_id or 0,
                sender_name=sender_name,
                sender_username=getattr(sender, 'username', None),
                chat_id=dialog.id,
                chat_name=dialog.name,
                chat_username=getattr(entity, 'username', None),
                is_user=dialog.is_user,
                is_group=dialog.is_group,
                is_channel=dialog.is_channel,
                is_reply=message.is_reply,
                is_forwarded=message.forward is not None,
                has_media=message.media is not None,
                media_type=get_media_type(message) if message.media else None,
                reply_to_msg_id=message.reply_to.reply_to_msg_id if message.reply_to else None,
                reply_info=reply_info,
                raw_message=message,
            )
            messages.append(msg)

        messages.reverse()  # 按时间正序排列
        logger.info(f"获取到 {len(messages)} 条消息")
        return messages, dialog_info


    async def export_to_file(
        self,
        dialog_identifier: Union[int, str],
        output_path: Union[str, Path],
        fmt: ExportFormat = ExportFormat.JSON,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        download_media: bool = False,
        media_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        导出消息到文件

        Args:
            dialog_identifier: 对话标识符
            output_path: 输出文件路径（不含扩展名）或目录
            fmt: 导出格式
            limit: 最大消息数量
            start_date: 开始时间
            end_date: 结束时间
            download_media: 是否下载媒体文件
            media_dir: 媒体文件保存目录

        Returns:
            导出文件的路径
        """
        messages, dialog_info = await self.fetch_messages(
            dialog_identifier, limit, start_date, end_date
        )

        if not messages:
            raise ValueError("没有可导出的消息")

        # 处理输出路径
        output_path = Path(output_path)
        formatter = _get_formatter(fmt)

        if output_path.is_dir():
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in dialog_info.name)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_name}_{timestamp}{formatter.get_extension()}"
            output_path = output_path / filename
        else:
            if not output_path.suffix:
                output_path = output_path.with_suffix(formatter.get_extension())

        # 确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 下载媒体文件
        if download_media:
            media_path = Path(media_dir) if media_dir else output_path.parent / "media"
            await self._download_media_files(messages, media_path)

        # 格式化并写入文件
        content = formatter.format(messages, dialog_info)
        output_path.write_text(content, encoding='utf-8')

        logger.info(f"已导出 {len(messages)} 条消息到 {output_path}")
        return output_path

    async def _download_media_files(
        self,
        messages: List[UnreadMessage],
        media_dir: Path,
    ) -> int:
        """
        下载消息中的媒体文件

        Args:
            messages: 消息列表
            media_dir: 媒体保存目录

        Returns:
            下载成功的文件数量
        """
        media_dir.mkdir(parents=True, exist_ok=True)
        downloaded = 0

        for msg in messages:
            if not msg.has_media or msg.raw_message is None:
                continue

            raw_msg = msg.raw_message
            if raw_msg.media is None:
                continue

            try:
                # 生成文件名
                timestamp = msg.date.strftime('%Y%m%d_%H%M%S')
                ext = self._get_media_extension(raw_msg)
                filename = f"{msg.message_id}_{timestamp}{ext}"
                file_path = media_dir / filename

                # 下载媒体
                await self.client.download_media(raw_msg, file=str(file_path))
                downloaded += 1
                logger.debug(f"已下载媒体: {filename}")

            except Exception as e:
                logger.warning(f"下载媒体失败 (消息ID: {msg.message_id}): {e}")

        logger.info(f"共下载 {downloaded} 个媒体文件到 {media_dir}")
        return downloaded

    @staticmethod
    def _get_media_extension(message) -> str:
        """获取媒体文件扩展名"""
        if hasattr(message.media, 'photo'):
            return ".jpg"
        if hasattr(message.media, 'document'):
            doc = message.media.document
            if doc and hasattr(doc, 'mime_type'):
                mime = doc.mime_type
                ext_map = {
                    'video/mp4': '.mp4',
                    'audio/mpeg': '.mp3',
                    'audio/ogg': '.ogg',
                    'image/gif': '.gif',
                    'image/png': '.png',
                    'image/jpeg': '.jpg',
                }
                if mime in ext_map:
                    return ext_map[mime]
            # 尝试从文件属性获取
            for attr in getattr(doc, 'attributes', []):
                if hasattr(attr, 'file_name') and attr.file_name:
                    return Path(attr.file_name).suffix or ".bin"
        return ".bin"