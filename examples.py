"""
使用示例脚本
演示如何使用 TGmessage 库获取 Telegram 未读消息
"""
import asyncio
import json
from TGmessage import (
    TelegramUnreadMessageAPI,
    get_unread_dialogs,
    get_unread_messages,
)


async def example1_get_all_unread_dialogs():
    """示例1: 获取所有有未读消息的对话"""
    print("=== 示例1: 获取所有有未读消息的对话 ===\n")
    
    # 方式1: 使用便捷函数
    dialogs = await get_unread_dialogs()
    
    print(f"共有 {len(dialogs)} 个对话有未读消息:\n")
    for dialog in dialogs:
        print(dialog)
        print()


async def example2_get_all_unread_messages():
    """示例2: 获取所有未读消息"""
    print("=== 示例2: 获取所有未读消息 ===\n")
    
    # 方式1: 使用便捷函数
    messages = await get_unread_messages()
    
    print(f"共有 {len(messages)} 条未读消息:\n")
    for msg in messages[:10]:  # 只打印前10条
        print(msg)
        print("-" * 60)


async def example3_get_unread_from_specific_chat():
    """示例3: 获取特定群组的未读消息"""
    print("=== 示例3: 获取特定群组的未读消息 ===\n")
    
    # 可以使用群组名称、用户名或 ID
    chat_identifier = "MyGroupName"  # 替换为实际的群组名称或 @username
    
    messages = await get_unread_messages(dialog=chat_identifier)
    
    print(f"群组 '{chat_identifier}' 有 {len(messages)} 条未读消息:\n")
    for msg in messages:
        print(msg)
        print("-" * 60)


async def example4_use_api_class():
    """示例4: 使用 API 类进行更多控制"""
    print("=== 示例4: 使用 API 类 ===\n")
    
    # 创建 API 实例
    api = TelegramUnreadMessageAPI()
    
    try:
        # 连接(首次登录时需要提供手机号)
        # await api.connect(phone='+8613800138000', password='your_2fa_password')
        await api.connect()
        
        # 获取所有有未读消息的对话
        dialogs = await api.get_all_unread_dialogs()
        print(f"有未读消息的对话数: {len(dialogs)}\n")
        
        # 逐个获取每个对话的未读消息
        for dialog in dialogs[:3]:  # 只处理前3个
            print(f"\n处理对话: {dialog.name} (未读: {dialog.unread_count})")
            messages = await api.get_unread_messages(
                dialog=dialog.dialog_id,
                limit=5  # 每个对话最多获取5条
            )
            
            for msg in messages:
                print(f"  - {msg.sender_name}: {msg.content[:50]}...")
    
    finally:
        # 断开连接
        await api.disconnect()


async def example5_export_to_json():
    """示例5: 导出未读消息为 JSON"""
    print("=== 示例5: 导出为 JSON ===\n")
    
    messages = await get_unread_messages(limit=20)  # 限制每个对话20条
    
    # 转换为字典列表
    messages_dict = [msg.to_dict() for msg in messages]
    
    # 保存为 JSON
    output_file = "unread_messages.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages_dict, f, ensure_ascii=False, indent=2)
    
    print(f"已导出 {len(messages)} 条未读消息到 {output_file}")


async def example6_with_context_manager():
    """示例6: 使用异步上下文管理器"""
    print("=== 示例6: 使用上下文管理器 ===\n")
    
    async with TelegramUnreadMessageAPI() as api:
        # 自动连接和断开
        dialogs = await api.get_all_unread_dialogs()
        print(f"有 {len(dialogs)} 个对话有未读消息")


async def example7_filter_by_chat_type():
    """示例7: 按对话类型过滤"""
    print("=== 示例7: 按对话类型过滤 ===\n")
    
    all_messages = await get_unread_messages()
    
    # 分类统计
    user_messages = [m for m in all_messages if m.is_user]
    group_messages = [m for m in all_messages if m.is_group]
    channel_messages = [m for m in all_messages if m.is_channel]
    
    print(f"私聊未读: {len(user_messages)} 条")
    print(f"群组未读: {len(group_messages)} 条")
    print(f"频道未读: {len(channel_messages)} 条")
    
    # 只显示私聊消息
    print("\n私聊消息:")
    for msg in user_messages[:5]:
        print(f"  {msg.sender_name}: {msg.content[:50]}...")


async def example8_send_text_message():
    """示例8: 发送文本消息"""
    print("\n=== 示例8: 发送文本消息 ===\n")

    # 导入发送消息函数
    from TGmessage import send_message

    # 发送简单文本消息
    chat_id = "username"  # 替换为实际的对话标识符

    msg_id = await send_message(
        dialog=chat_id,
        text="Hello from TGmessage!"
    )

    print(f"消息已发送,消息 ID: {msg_id}")


async def example9_send_photo():
    """示例9: 发送图片"""
    print("\n=== 示例9: 发送图片 ===\n")

    from TGmessage import send_photo

    # 发送图片
    msg_id = await send_photo(
        dialog="username",
        photo="path/to/photo.jpg",
        caption="这是一张图片"
    )

    print(f"图片已发送,消息 ID: {msg_id}")


async def example10_send_file():
    """示例10: 发送文件"""
    print("\n=== 示例10: 发送文件 ===\n")

    from TGmessage import send_file

    # 发送文件
    msg_id = await send_file(
        dialog="username",
        file="path/to/document.pdf",
        caption="这是一个文档"
    )

    print(f"文件已发送,消息 ID: {msg_id}")


async def example11_comprehensive_api_usage():
    """示例11: 综合使用 API"""
    print("\n=== 示例11: 综合使用 API ===\n")

    async with TelegramUnreadMessageAPI() as api:
        # 1. 获取未读对话
        dialogs = await api.get_all_unread_dialogs()
        print(f"有 {len(dialogs)} 个对话有未读消息")

        if dialogs:
            # 2. 选择第一个对话
            first_dialog = dialogs[0]
            print(f"\n处理对话: {first_dialog.name}")

            # 3. 获取该对话的未读消息
            messages = await api.get_unread_messages(
                dialog=first_dialog.dialog_id,
                limit=5
            )

            print(f"找到 {len(messages)} 条未读消息")

            # 4. 发送一条回复消息
            if messages:
                await api.send_message(
                    dialog=first_dialog.dialog_id,
                    text="我已经看到你的消息了!",
                    reply_to=messages[0].message_id
                )
                print("已发送回复")

            # 5. 转发消息到"我的收藏"
            if messages and len(messages) > 0:
                await api.forward_message(
                    from_dialog=first_dialog.dialog_id,
                    to_dialog="me",  # "me" 代表我的收藏
                    message_ids=[messages[0].message_id]
                )
                print("已转发消息到我的收藏")


async def main():
    """主函数"""
    print("Telegram 未读消息获取示例\n")
    print("=" * 60)
    
    try:
        # 运行示例 (根据需要选择)
        await example1_get_all_unread_dialogs()
        # await example2_get_all_unread_messages()
        # await example3_get_unread_from_specific_chat()
        # await example4_use_api_class()
        # await example5_export_to_json()
        # await example6_with_context_manager()
        # await example7_filter_by_chat_type()
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 运行异步主函数
    asyncio.run(main())

