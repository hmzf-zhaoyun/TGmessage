"""
交互式命令行界面模块
"""
import shlex
from typing import TYPE_CHECKING

from TGmessage import TelegramUnreadMessageAPI

if TYPE_CHECKING:
    from ..core.app import FishingApp


class InteractiveShell:
    """交互式命令行界面"""
    
    def __init__(self, app: 'FishingApp'):
        """
        初始化交互式Shell
        
        Args:
            app: FishingApp 实例
        """
        self.app = app
    
    async def run(self):
        """运行交互模式"""
        async with TelegramUnreadMessageAPI() as api:
            self.app.api = api
            
            print("\n  🎣 TGmessage 摸鱼工具 - 交互模式")
            print("  ✨ 新功能: 支持消息回复链显示、@ 提及、编辑、删除等")
            print("  输入 'help' 查看帮助\n")
            
            while True:
                try:
                    cmd = input("TG> ").strip()
                    
                    if not cmd:
                        continue
                    
                    try:
                        tokens = shlex.split(cmd)
                    except ValueError as e:
                        print(f"  ❌ 参数解析失败: {e}")
                        continue
                    
                    if not tokens:
                        continue
                    
                    action = tokens[0].lower()
                    args = tokens[1:]
                    
                    # 处理退出命令
                    if action in ['q', 'quit', 'exit']:
                        print("\n  👋 再见!\n")
                        break
                    
                    # 处理各种命令
                    await self._handle_command(action, args)
                
                except KeyboardInterrupt:
                    print("\n\n  👋 再见!\n")
                    break
                
                except Exception as e:
                    print(f"  ❌ 错误: {e}")
            
            self.app.api = None
    
    async def _handle_command(self, action: str, args: list):
        """处理命令"""
        if action in ['h', 'help']:
            self._show_help()
        
        elif action in ['s', 'summary']:
            await self.app.run_summary_view()
        
        elif action in ['l', 'list']:
            limit = int(args[0]) if args and args[0].isdigit() else 10
            await self.app.run_recent_view(limit)
        
        elif action == 'stars':
            self.app.list_favorites()
        
        elif action == 'star':
            await self.app.add_favorite(args)
        
        elif action == 'unstar':
            await self.app.remove_favorite(args)
        
        elif action == 'use':
            await self.app.use_dialog(args)
        
        elif action == 'back':
            self.app.leave_dialog()
        
        elif action in ['c', 'chat']:
            if args:
                await self.app.run_dialog_view(" ".join(args))
            else:
                await self.app.run_dialog_view()
        
        elif action in ['m', 'send']:
            await self._handle_send_command(args)
        
        elif action in ['r', 'reply']:
            await self._handle_reply_command(args)
        
        elif action in ['e', 'edit']:
            await self._handle_edit_command(args)
        
        elif action in ['d', 'delete', 'del']:
            await self._handle_delete_command(args)
        
        elif action in ['f', 'forward', 'fwd']:
            await self._handle_forward_command(args)
        
        else:
            print(f"  ❌ 未知命令: {action}")
            print("  输入 'help' 查看帮助")
    
    async def _handle_send_command(self, args: list):
        """处理发送命令"""
        dialog = None
        dialog_label = None
        text = None
        
        if args:
            if '--' in args:
                sep_index = args.index('--')
                dialog_tokens = args[:sep_index]
                text_tokens = args[sep_index + 1:]
                if dialog_tokens and text_tokens:
                    dialog = " ".join(dialog_tokens)
                    text = " ".join(text_tokens)
            elif len(args) >= 2:
                dialog = args[0]
                text = " ".join(args[1:])
            elif len(args) == 1 and self.app.current_dialog:
                dialog = self.app.current_dialog.dialog_id
                dialog_label = self.app.current_dialog.name
                text = args[0]
        
        await self.app.send_message(dialog, text, dialog_label)
    
    async def _handle_reply_command(self, args: list):
        """处理回复命令"""
        if not self.app.current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return
        
        if len(args) < 2:
            print("  用法: reply <消息ID> <回复内容>")
            print("  示例: reply 12345 收到！")
            return
        
        try:
            msg_id = int(args[0])
            text = " ".join(args[1:])
            await self.app.reply_message(msg_id, text)
        except ValueError:
            print("  ❌ 消息ID必须是数字")
    
    async def _handle_edit_command(self, args: list):
        """处理编辑命令"""
        if not self.app.current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return

        if len(args) < 2:
            print("  用法: edit <消息ID> <新内容>")
            print("  示例: edit 12345 这是修改后的内容")
            return

        try:
            msg_id = int(args[0])
            new_text = " ".join(args[1:])
            await self.app.edit_message(msg_id, new_text)
        except ValueError:
            print("  ❌ 消息ID必须是数字")

    async def _handle_delete_command(self, args: list):
        """处理删除命令"""
        if not self.app.current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话")
            return

        if not args:
            print("  用法: delete <消息ID> [消息ID2] [消息ID3] ...")
            print("  示例: delete 12345")
            print("        delete 12345 12346 12347")
            return

        try:
            msg_ids = [int(arg) for arg in args]
            await self.app.delete_messages(msg_ids)
        except ValueError:
            print("  ❌ 消息ID必须是数字")

    async def _handle_forward_command(self, args: list):
        """处理转发命令"""
        if not self.app.current_dialog:
            print("  ❌ 请先使用 'use' 命令进入对话（源对话）")
            return

        if len(args) < 2:
            print("  用法: forward <消息ID> <目标对话>")
            print("  示例: forward 12345 @username")
            print("        forward 12345 \"群组名称\"")
            return

        try:
            msg_id = int(args[0])
            to_dialog = " ".join(args[1:])
            await self.app.forward_message(msg_id, to_dialog)
        except ValueError:
            print("  ❌ 消息ID必须是数字")

    def _show_help(self):
        """显示帮助"""
        print("\n  📖 命令列表:")
        print("\n  📬 查看消息:")
        print("     s, summary      - 查看摘要")
        print("     l, list [数量]  - 查看消息列表 (默认10条，自动显示回复链和消息ID)")
        print("     c, chat [名称]  - 查看特定对话 (进入对话后可省略)")

        print("\n  💬 发送与操作:")
        print("     m, send [对话] <消息> - 发送消息 (进入对话后可省略，m 是快捷缩写)")
        print("     r, reply <消息ID> <内容> - 回复消息 (需先 use 进入对话)")
        print("     e, edit <消息ID> <新内容> - 编辑消息 (需先 use 进入对话)")
        print("     d, delete <消息ID> [...] - 删除消息 (需先 use 进入对话)")
        print("     f, forward <消息ID> <目标对话> - 转发消息")
        print("\n     示例:")
        print("           m 你好              (使用 m 快速发送)")
        print("           send @username 你好  (@ 提及用户)")
        print("           reply 12345 收到！")
        print("           edit 12345 修改后的内容")
        print("           delete 12345 12346")
        print("           forward 12345 @username")

        print("\n  📌 收藏管理:")
        print("     stars           - 查看收藏对话")
        print("     star <对话|序号> - 收藏对话 (可省略使用当前对话)")
        print("     unstar <对话|序号> - 取消收藏 (可省略使用当前对话)")
        print("     use <对话|序号>  - 进入对话")
        print("     back            - 退出当前对话")

        print("\n  ℹ️  通用:")
        print("     h, help         - 显示帮助")
        print("     q, quit         - 退出")
        print()
