"""
消息操作器模块
负责回复、编辑、删除、转发等操作
"""
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from TGmessage import TelegramUnreadMessageAPI
    from ..models import DialogInfo


class MessageOperator:
    """消息操作器"""
    
    def __init__(self):
        """初始化消息操作器"""
        pass
    
    async def reply_message(
        self,
        api: 'TelegramUnreadMessageAPI',
        current_dialog: 'DialogInfo',
        message_id: int,
        text: str
    ):
        """
        回复消息
        
        Args:
            api: TelegramUnreadMessageAPI 实例
            current_dialog: 当前对话信息
            message_id: 要回复的消息ID
            text: 回复内容
        """
        if not current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return
        
        try:
            await api.send_message(
                dialog=current_dialog.dialog_id,
                text=text,
                reply_to=message_id
            )
            
            print(f"\n  ✅ 已回复消息 ID:{message_id}")
            print(f"  内容: {text}\n")
        
        except Exception as e:
            print(f"  ❌ 回复失败: {e}")
    
    async def edit_message(
        self,
        api: 'TelegramUnreadMessageAPI',
        current_dialog: 'DialogInfo',
        message_id: int,
        new_text: str
    ):
        """
        编辑消息
        
        Args:
            api: TelegramUnreadMessageAPI 实例
            current_dialog: 当前对话信息
            message_id: 要编辑的消息ID
            new_text: 新的内容
        """
        if not current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return
        
        try:
            success = await api.edit_message(
                dialog=current_dialog.dialog_id,
                message_id=message_id,
                new_text=new_text
            )
            
            if success:
                print(f"\n  ✅ 已编辑消息 ID:{message_id}")
                print(f"  新内容: {new_text}\n")
            else:
                print(f"  ❌ 编辑失败 (可能不是你发送的消息或超过编辑时限)")
        
        except Exception as e:
            print(f"  ❌ 编辑失败: {e}")
    
    async def delete_messages(
        self,
        api: 'TelegramUnreadMessageAPI',
        current_dialog: 'DialogInfo',
        message_ids: List[int]
    ):
        """
        删除消息
        
        Args:
            api: TelegramUnreadMessageAPI 实例
            current_dialog: 当前对话信息
            message_ids: 要删除的消息ID列表
        """
        if not current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return
        
        try:
            count = await api.delete_messages(
                dialog=current_dialog.dialog_id,
                message_ids=message_ids,
                revoke=True  # 双向删除
            )
            
            print(f"\n  ✅ 成功删除 {count} 条消息")
            print(f"  消息ID: {', '.join(str(mid) for mid in message_ids)}\n")
        
        except Exception as e:
            print(f"  ❌ 删除失败: {e}")
    
    async def forward_message(
        self,
        api: 'TelegramUnreadMessageAPI',
        current_dialog: 'DialogInfo',
        message_id: int,
        to_dialog: str
    ):
        """
        转发消息
        
        Args:
            api: TelegramUnreadMessageAPI 实例
            current_dialog: 当前对话信息
            message_id: 要转发的消息ID
            to_dialog: 目标对话
        """
        if not current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话（源对话）")
            return
        
        try:
            forwarded_ids = await api.forward_message(
                from_dialog=current_dialog.dialog_id,
                to_dialog=to_dialog,
                message_ids=message_id
            )
            
            print(f"\n  ✅ 消息已转发")
            print(f"  源消息ID: {message_id}")
            print(f"  目标对话: {to_dialog}")
            print(f"  新消息ID: {forwarded_ids}\n")
        
        except Exception as e:
            print(f"  ❌ 转发失败: {e}")

