"""
应用主类模块
协调各个功能组件
"""
from contextlib import asynccontextmanager
from typing import Optional, TYPE_CHECKING

from TGmessage import TelegramUnreadMessageAPI
from TGmessage.config import get_config
from TGmessage.utils import find_dialog
from TGmessage.models import DialogInfo

from .favorites import FavoritesManager
from .message_viewer import MessageViewer
from .send_handler import MessageSendHandler
from .message_operator import MessageOperator
from .export_handler import ExportHandler
from ..ui.formatter import UIFormatter

if TYPE_CHECKING:
    pass


class FishingApp:
    """摸鱼工具应用主类"""

    def __init__(self):
        """初始化应用"""
        self.api: Optional[TelegramUnreadMessageAPI] = None

        # 初始化各个组件
        config = get_config()
        self.favorites_manager = FavoritesManager(config.favorites_file)
        self.message_viewer = MessageViewer()
        self.message_send_handler = MessageSendHandler()
        self.message_operator = MessageOperator()
        self.export_handler = ExportHandler()
        self.formatter = UIFormatter()

        # 当前对话
        self.current_dialog: Optional[DialogInfo] = None
    
    @asynccontextmanager
    async def _get_api(self):
        """获取 API 实例的上下文管理器"""
        if self.api is not None:
            yield self.api
            return
        async with TelegramUnreadMessageAPI() as api:
            yield api
    
    async def _resolve_dialog_info(self, identifier) -> DialogInfo:
        """
        解析对话信息
        
        Args:
            identifier: 对话标识符
            
        Returns:
            DialogInfo 对象
            
        Raises:
            ValueError: 找不到对话
        """
        if self.api is None:
            raise RuntimeError("API 未初始化")
        
        dialog = await find_dialog(self.api.client_wrapper.client, identifier)
        if dialog is None:
            raise ValueError(f"找不到对话: {identifier}")
        
        entity = dialog.entity
        username = getattr(entity, "username", None)
        
        return DialogInfo(
            dialog_id=dialog.id,
            name=dialog.name,
            username=username
        )
    
    # ===== 收藏管理相关方法 =====
    
    def list_favorites(self):
        """列出所有收藏"""
        favorites = self.favorites_manager.get_all()
        if not favorites:
            print("\n  暂无收藏对话\n")
            return
        
        print("\n  ⭐ 收藏对话:")
        current_id = self.current_dialog.dialog_id if self.current_dialog else None
        for i, fav in enumerate(favorites, 1):
            mark = "★" if current_id == fav.dialog_id else " "
            print(f"  {i}. {mark} {self.formatter.format_dialog_info(fav)}")
        print()
    
    async def add_favorite(self, args: list):
        """添加收藏"""
        if not args:
            if not self.current_dialog:
                print("  用法: star <对话名称/用户名/ID>  (或先 use 进入对话)")
                return
            dialog_info = self.current_dialog
        else:
            identifier = " ".join(args)
            try:
                dialog_info = await self._resolve_dialog_info(identifier)
            except ValueError as e:
                print(f"  ❌ {e}")
                return
        
        is_new = self.favorites_manager.add_or_update(dialog_info)
        if is_new:
            print(f"  ✅ 已收藏: {self.formatter.format_dialog_info(dialog_info)}")
        else:
            print(f"  ✅ 收藏已更新: {self.formatter.format_dialog_info(dialog_info)}")
    
    async def remove_favorite(self, args: list):
        """移除收藏"""
        if not args:
            if not self.current_dialog:
                print("  用法: unstar <序号|对话名称/用户名/ID>  (或先 use 进入对话)")
                return
            removed = self.favorites_manager.remove_by_id(self.current_dialog.dialog_id)
            if removed is None:
                print("  ❌ 当前对话不在收藏中")
                return
            print(f"  ✅ 已取消收藏: {self.formatter.format_dialog_info(removed)}")
            return
        
        index = None
        if len(args) == 1 and args[0].isdigit():
            idx = int(args[0])
            favorites_count = len(self.favorites_manager.get_all())
            if 1 <= idx <= favorites_count:
                index = idx - 1
            else:
                print("  ❌ 序号超出范围")
                return
        else:
            identifier = " ".join(args)
            matches = self.favorites_manager.find_by_identifier(identifier)
            if len(matches) == 1:
                index = matches[0]
            elif len(matches) > 1:
                print("  ❌ 匹配到多个收藏,请使用序号")
                return
            else:
                try:
                    dialog_info = await self._resolve_dialog_info(identifier)
                except ValueError as e:
                    print(f"  ❌ {e}")
                    return
                removed = self.favorites_manager.remove_by_id(dialog_info.dialog_id)
                if removed is None:
                    print("  ❌ 未找到对应的收藏")
                    return
                print(f"  ✅ 已取消收藏: {self.formatter.format_dialog_info(removed)}")
                return
        
        removed = self.favorites_manager.remove_by_index(index)
        print(f"  ✅ 已取消收藏: {self.formatter.format_dialog_info(removed)}")

    async def use_dialog(self, args: list):
        """进入对话"""
        if not args:
            print("  用法: use <序号|对话名称/用户名/ID>")
            return

        dialog_info = None
        if len(args) == 1 and args[0].isdigit():
            idx = int(args[0])
            favorites = self.favorites_manager.get_all()
            if 1 <= idx <= len(favorites):
                identifier = favorites[idx - 1].dialog_id
                try:
                    dialog_info = await self._resolve_dialog_info(identifier)
                except ValueError as e:
                    print(f"  ❌ {e}")
                    return
            else:
                print("  ❌ 序号超出范围")
                return

        if dialog_info is None:
            identifier = " ".join(args)
            try:
                dialog_info = await self._resolve_dialog_info(identifier)
            except ValueError as e:
                print(f"  ❌ {e}")
                return

        self.current_dialog = dialog_info
        # 同步更新收藏中的信息
        self.favorites_manager.add_or_update(dialog_info)
        print(f"  ✅ 已进入对话: {self.formatter.format_dialog_info(dialog_info)}")

    def leave_dialog(self):
        """退出当前对话"""
        if not self.current_dialog:
            print("  当前未进入任何对话")
            return
        dialog_info = self.current_dialog
        self.current_dialog = None
        print(f"  ✅ 已退出对话: {self.formatter.format_dialog_info(dialog_info)}")

    # ===== 消息查看相关方法 =====

    async def run_summary_view(self):
        """运行摘要查看"""
        async with self._get_api() as api:
            await self.message_viewer.show_summary(api)

    async def run_recent_view(self, limit: int = 10):
        """运行最近消息查看"""
        async with self._get_api() as api:
            await self.message_viewer.show_recent_messages(api, limit)

    async def run_dialog_view(self, dialog_identifier=None, dialog_label: str = None):
        """运行对话查看"""
        async with self._get_api() as api:
            if dialog_identifier is None and self.current_dialog:
                dialog_identifier = self.current_dialog.dialog_id
                dialog_label = self.current_dialog.name

            if dialog_identifier is None:
                print("  用法: chat <对话名称>  (或先 use 进入对话)")
                return

            await self.message_viewer.show_dialog_messages(api, dialog_identifier, dialog_label)

    # ===== 消息发送相关方法 =====

    async def send_message(self, dialog=None, text: str = None, dialog_label: str = None):
        """发送消息"""
        async with self._get_api() as api:
            if dialog and text:
                await self.message_send_handler.send_with_check(api, dialog, text, dialog_label)
            else:
                self.formatter.print_send_usage(self.current_dialog is not None)

    # ===== 消息操作相关方法 =====

    async def reply_message(self, message_id: int, text: str):
        """回复消息"""
        async with self._get_api() as api:
            await self.message_operator.reply_message(api, self.current_dialog, message_id, text)

    async def edit_message(self, message_id: int, new_text: str):
        """编辑消息"""
        async with self._get_api() as api:
            await self.message_operator.edit_message(api, self.current_dialog, message_id, new_text)

    async def delete_messages(self, message_ids: list):
        """删除消息"""
        async with self._get_api() as api:
            await self.message_operator.delete_messages(api, self.current_dialog, message_ids)

    async def forward_message(self, message_id: int, to_dialog: str):
        """转发消息"""
        async with self._get_api() as api:
            await self.message_operator.forward_message(api, self.current_dialog, message_id, to_dialog)

    # ===== 消息导出相关方法 =====

    async def export_messages(
        self,
        dialog_identifier=None,
        output_path: str = None,
        fmt: str = 'json',
        limit: int = None,
        start_date: str = None,
        end_date: str = None,
        download_media: bool = False,
    ):
        """
        导出消息

        Args:
            dialog_identifier: 对话标识符（可选，默认使用当前对话）
            output_path: 输出路径
            fmt: 导出格式
            limit: 最大消息数量
            start_date: 开始时间字符串
            end_date: 结束时间字符串
            download_media: 是否下载媒体
        """
        # 确定对话
        if dialog_identifier is None:
            if self.current_dialog is None:
                print("  ❌ 请先使用 'use' 命令进入对话，或指定对话名称")
                return
            dialog_identifier = self.current_dialog.dialog_id

        # 解析时间
        parsed_start = None
        parsed_end = None
        if start_date:
            parsed_start = self.export_handler.parse_date(start_date)
            if parsed_start is None:
                print(f"  ❌ 无法解析开始时间: {start_date}")
                print("  支持格式: YYYY-MM-DD, YYYY-MM-DD HH:MM")
                return
        if end_date:
            parsed_end = self.export_handler.parse_date(end_date)
            if parsed_end is None:
                print(f"  ❌ 无法解析结束时间: {end_date}")
                print("  支持格式: YYYY-MM-DD, YYYY-MM-DD HH:MM")
                return

        async with self._get_api() as api:
            await self.export_handler.export_dialog(
                api=api,
                dialog_identifier=dialog_identifier,
                output_path=output_path,
                fmt=fmt,
                limit=limit,
                start_date=parsed_start,
                end_date=parsed_end,
                download_media=download_media,
            )