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

    async def get_dialog_unread_count(self, dialog_identifier=None, dialog_label: str = None):
        """
        获取指定对话的未读消息总数

        Args:
            dialog_identifier: 对话标识符（对话ID/用户名/名称），可选
            dialog_label: 用于显示的友好对话名称，可选
        """
        async with self._get_api() as api:
            # 如果未指定对话标识符，尝试使用当前对话
            if dialog_identifier is None:
                if self.current_dialog:
                    dialog_identifier = self.current_dialog.dialog_id
                    dialog_label = self.current_dialog.name
                else:
                    print("  用法: unread <对话名称/用户名/ID>  (或先 use 进入对话)")
                    return

            # 查找对话
            dialog = await find_dialog(api.client_wrapper.client, dialog_identifier)
            if dialog is None:
                print(f"  ❌ 找不到对话: {dialog_identifier}")
                return

            # 获取对话信息
            unread_count = dialog.unread_count
            display_name = dialog_label or dialog.name
            username = getattr(dialog.entity, 'username', None)
            username_part = f" (@{username})" if username else ""

            # 显示格式化的未读消息总数
            if unread_count == 0:
                print(f"  ✅ {display_name}{username_part} 没有未读消息")
            else:
                # 获取提及数量
                mentions_count = dialog.unread_mentions_count
                mentions_info = f"，其中 {mentions_count} 条提及" if mentions_count > 0 else ""
                print(f"  📬 {display_name}{username_part} 有 {unread_count} 条未读消息{mentions_info}")

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

    # ===== 文件夹/分组相关方法 =====

    async def list_folders(self):
        """列出所有文件夹/分组"""
        async with self._get_api() as api:
            try:
                folders = await api.get_folders()

                if not folders:
                    print("\n  📂 没有找到任何文件夹/分组")
                    print("  提示: 请在 Telegram 客户端中创建文件夹")
                    return

                self.formatter.print_title("📂 文件夹列表")

                for i, folder in enumerate(folders, 1):
                    emoji = folder.emoticon or "📁"

                    # 构建类型标签
                    types = []
                    if folder.include_contacts:
                        types.append("联系人")
                    if folder.include_non_contacts:
                        types.append("非联系人")
                    if folder.include_groups:
                        types.append("群组")
                    if folder.include_channels:
                        types.append("频道")
                    if folder.include_bots:
                        types.append("机器人")

                    type_info = ", ".join(types) if types else "自定义"

                    # 构建过滤条件标签
                    filters = []
                    if folder.exclude_muted:
                        filters.append("排除静音")
                    if folder.exclude_read:
                        filters.append("仅未读")
                    if folder.exclude_archived:
                        filters.append("排除归档")
                    filter_info = f" ({', '.join(filters)})" if filters else ""

                    print(f"\n  {i}. {emoji} {folder.title}")
                    print(f"     ID: {folder.folder_id} | 类型: {type_info}{filter_info}")

                    # 显示包含的特定对话数量
                    specific_count = len(folder.include_peer_ids) + len(folder.pinned_peer_ids)
                    if specific_count > 0:
                        print(f"     包含 {specific_count} 个指定对话")

                print()
                print("  💡 使用 'folders <ID>' 查看文件夹中的对话")
                print()

            except Exception as e:
                print(f"\n  ❌ 获取文件夹列表失败: {e}\n")

    async def list_folder_dialogs(self, folder_id: str, unread_only: bool = False):
        """
        列出指定文件夹中的对话

        Args:
            folder_id: 文件夹ID（字符串形式）
            unread_only: 是否只显示有未读消息的对话
        """
        try:
            fid = int(folder_id)
        except ValueError:
            print(f"  ❌ 无效的文件夹ID: {folder_id}")
            return

        async with self._get_api() as api:
            try:
                # 先获取文件夹信息用于显示标题
                folders = await api.get_folders()
                folder = next((f for f in folders if f.folder_id == fid), None)

                if folder is None:
                    print(f"  ❌ 找不到文件夹: {folder_id}")
                    print("  使用 'folders' 命令查看所有文件夹")
                    return

                dialogs = await api.get_dialogs_by_folder(
                    folder_id=fid,
                    include_unread_only=unread_only
                )

                emoji = folder.emoticon or "📁"
                filter_text = "（仅未读）" if unread_only else ""
                self.formatter.print_title(f"{emoji} {folder.title} {filter_text}")

                if not dialogs:
                    if unread_only:
                        print("\n  ✅ 该文件夹中没有未读消息")
                    else:
                        print("\n  📭 该文件夹中没有对话")
                    print()
                    return

                # 按未读数排序
                dialogs.sort(key=lambda d: d.unread_count, reverse=True)

                for i, dialog in enumerate(dialogs, 1):
                    # 对话类型图标
                    if dialog.is_user:
                        type_emoji = "👤"
                    elif dialog.is_group:
                        type_emoji = "👥"
                    else:
                        type_emoji = "📢"

                    # 未读标记
                    unread_mark = f" 🔴 {dialog.unread_count}" if dialog.unread_count > 0 else ""

                    # 用户名
                    username_part = f" (@{dialog.username})" if dialog.username else ""

                    print(f"  {i:3}. {type_emoji} {dialog.name}{username_part}{unread_mark}")
                    print(f"       ID: {dialog.dialog_id}")

                print()
                print(f"  共 {len(dialogs)} 个对话")
                print("  💡 使用 'use <对话名/ID>' 进入对话")
                print()

            except ValueError as e:
                print(f"\n  ❌ {e}\n")
            except Exception as e:
                print(f"\n  ❌ 获取文件夹对话失败: {e}\n")