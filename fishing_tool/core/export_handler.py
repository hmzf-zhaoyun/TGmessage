"""
消息导出处理器模块
负责命令行工具中的消息导出功能
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from TGmessage.message_exporter import ExportFormat

if TYPE_CHECKING:
    from TGmessage import TelegramUnreadMessageAPI
    from ..models import DialogInfo


class ExportHandler:
    """消息导出处理器"""

    SUPPORTED_FORMATS = ['json', 'txt', 'csv', 'md']

    def __init__(self):
        """初始化导出处理器"""
        pass

    async def export_dialog(
        self,
        api: 'TelegramUnreadMessageAPI',
        dialog_identifier,
        output_path: Optional[str] = None,
        fmt: str = 'json',
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        download_media: bool = False,
    ):
        """
        导出对话消息

        Args:
            api: TelegramUnreadMessageAPI 实例
            dialog_identifier: 对话标识符
            output_path: 输出路径（可选，默认当前目录）
            fmt: 导出格式
            limit: 最大消息数量
            start_date: 开始时间
            end_date: 结束时间
            download_media: 是否下载媒体文件
        """
        if fmt.lower() not in self.SUPPORTED_FORMATS:
            print(f"  ❌ 不支持的格式: {fmt}")
            print(f"  支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
            return

        # 确定输出路径
        if output_path is None:
            output_path = Path.cwd()
        else:
            output_path = Path(output_path)

        try:
            export_format = ExportFormat(fmt.lower())

            print(f"\n  📤 正在导出消息...")
            if limit:
                print(f"     限制数量: {limit} 条")
            if start_date:
                print(f"     开始时间: {start_date.strftime('%Y-%m-%d %H:%M')}")
            if end_date:
                print(f"     结束时间: {end_date.strftime('%Y-%m-%d %H:%M')}")
            if download_media:
                print(f"     下载媒体: 是")

            result_path = await api.export_messages(
                dialog=dialog_identifier,
                output_path=output_path,
                fmt=export_format,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                download_media=download_media,
            )

            print(f"\n  ✅ 导出完成!")
            print(f"  📁 文件路径: {result_path}")
            if download_media:
                media_dir = result_path.parent / "media"
                if media_dir.exists():
                    print(f"  🖼️  媒体目录: {media_dir}")
            print()

        except ValueError as e:
            print(f"  ❌ 导出失败: {e}")
        except Exception as e:
            print(f"  ❌ 导出出错: {e}")

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        支持格式:
        - YYYY-MM-DD
        - YYYY-MM-DD HH:MM
        - YYYY-MM-DD HH:MM:SS
        """
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

