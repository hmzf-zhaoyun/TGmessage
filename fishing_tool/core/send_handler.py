"""
消息发送处理器模块
负责消息发送和遗漏检测

注意：此模块原名为 message_sender.py，为避免与 TGmessage.message_sender 混淆而重命名
"""
from typing import Optional, TYPE_CHECKING

from ..ui.formatter import UIFormatter

if TYPE_CHECKING:
    from TGmessage import TelegramUnreadMessageAPI


class MessageSendHandler:
    """消息发送处理器"""
    
    def __init__(self):
        """初始化消息发送处理器"""
        self.formatter = UIFormatter()
    
    async def send_with_check(
        self,
        api: 'TelegramUnreadMessageAPI',
        dialog,
        text: str,
        dialog_label: Optional[str] = None
    ):
        """
        发送消息并检查遗漏消息
        
        Args:
            api: TelegramUnreadMessageAPI 实例
            dialog: 对话标识符
            text: 消息内容
            dialog_label: 对话标签(用于显示)
        """
        try:
            # 获取对话ID(用于消息追踪)
            dialog_id = None
            if isinstance(dialog, int):
                dialog_id = dialog
            else:
                from TGmessage.utils import find_dialog
                dialog_obj = await find_dialog(api.client_wrapper.client, dialog)
                if dialog_obj:
                    dialog_id = dialog_obj.id
            
            # 检查是否有遗漏的消息(发送前)
            missed_messages = []
            if dialog_id and hasattr(api.message_fetcher, 'tracker') and api.message_fetcher.tracker:
                tracker = api.message_fetcher.tracker
                last_read_id = tracker.get_last_read_message_id(dialog_id)
                
                if last_read_id:
                    try:
                        all_messages = await api.get_unread_messages(dialog=dialog)
                        if all_messages:
                            missed_messages = [
                                msg for msg in all_messages
                                if msg.message_id > last_read_id
                            ]
                    except Exception as e:
                        print(f"  ⚠️  检查遗漏消息时出错: {e}")
            
            # 发送消息
            msg_id = await api.send_message(dialog=dialog, text=text)
            target = dialog_label or str(dialog)
            print(f"\n  ✅ 消息已发送给 {target} (ID: {msg_id})")
            
            # 如果有遗漏的消息,使用与 chat 相同的格式完整显示
            if missed_messages:
                print(f"\n  📬 检测到 {len(missed_messages)} 条中间消息:")
                self.formatter.print_line("-", 70)

                for msg in missed_messages:
                    # 显示消息头部(与 chat 格式一致)
                    print(f"\n{self.formatter.format_message_header(msg, time_format='%m-%d %H:%M')}")

                    # 显示回复信息
                    if msg.is_reply and msg.reply_info:
                        print(self.formatter.format_reply_info(msg))

                    # 显示消息内容(完整内容)
                    print(self.formatter.format_message_content(msg, max_lines=None, max_line_length=1000))

                self.formatter.print_line("-", 70)
            
            print()
        
        except Exception as e:
            print(f"\n  ❌ 发送失败: {e}\n")


# 向后兼容别名
MessageSenderWrapper = MessageSendHandler

