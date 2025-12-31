# TGmessage 快速开始指南

本指南将帮助你在 5 分钟内开始使用 TGmessage。

## 步骤 1: 安装依赖

```bash
cd TGmessage
pip install -r requirements.txt
```

或者手动安装:

```bash
pip install telethon python-dotenv
```

## 步骤 2: 获取 Telegram API 凭证

1. 访问 https://my.telegram.org/apps
2. 使用你的手机号登录 Telegram
3. 创建一个新应用
4. 记下 `api_id` 和 `api_hash`

## 步骤 3: 配置环境变量

在 `TGmessage` 目录下创建 `.env` 文件:

```env
TG_API_ID=你的api_id
TG_API_HASH=你的api_hash
TG_SESSION_NAME=my_session
TG_SESSION_DIR=./sessions
```

**示例:**
```env
TG_API_ID=12345678
TG_API_HASH=0123456789abcdef0123456789abcdef
TG_SESSION_NAME=my_session
TG_SESSION_DIR=./sessions
```

## 步骤 4: 首次登录

运行快速入门脚本:

```bash
python quickstart.py
```

首次运行会要求:
1. 输入手机号(格式: +8613800138000)
2. 输入收到的验证码
3. 如果开启了两步验证,输入密码

登录成功后会保存会话,下次无需重复登录。

## 步骤 5: 开始使用

### 方式 1: 使用便捷函数

创建文件 `test.py`:

```python
import asyncio
from TGmessage import get_unread_messages

async def main():
    # 获取所有未读消息
    messages = await get_unread_messages()
    
    print(f"共有 {len(messages)} 条未读消息\n")
    
    # 显示前 5 条
    for msg in messages[:5]:
        print(f"来自 {msg.chat_name}")
        print(f"发送者: {msg.sender_name}")
        print(f"内容: {msg.content[:50]}...")
        print("-" * 50)

asyncio.run(main())
```

运行:
```bash
python test.py
```

### 方式 2: 使用 API 类

```python
import asyncio
from TGmessage import TelegramUnreadMessageAPI

async def main():
    async with TelegramUnreadMessageAPI() as api:
        # 获取未读对话
        dialogs = await api.get_all_unread_dialogs()
        
        print(f"有 {len(dialogs)} 个对话有未读消息:\n")
        for dialog in dialogs:
            print(f"• {dialog.name}: {dialog.unread_count} 条")

asyncio.run(main())
```

### 方式 3: 发送消息

```python
import asyncio
from TGmessage import send_message

async def main():
    # 发送消息到指定用户/群组
    msg_id = await send_message(
        dialog="@username",  # 替换为实际的用户名或群组名
        text="Hello from TGmessage!"
    )
    
    print(f"消息已发送! 消息ID: {msg_id}")

asyncio.run(main())
```

## 常用代码片段

### 1. 获取特定群组的未读消息

```python
messages = await get_unread_messages(dialog="我的群组名称")
# 或者
messages = await get_unread_messages(dialog="@groupusername")
# 或者
messages = await get_unread_messages(dialog=-1001234567890)
```

### 2. 限制获取的消息数量

```python
messages = await get_unread_messages(limit=10)
```

### 3. 过滤特定类型的消息

```python
all_messages = await get_unread_messages()

# 只要私聊消息
user_messages = [m for m in all_messages if m.is_user]

# 只要群组消息
group_messages = [m for m in all_messages if m.is_group]

# 只要包含媒体的消息
media_messages = [m for m in all_messages if m.has_media]
```

### 4. 发送 Markdown 格式消息

```python
await send_message(
    dialog="@username",
    text="**粗体** *斜体* `代码`",
    parse_mode='md'
)
```

### 5. 发送图片

```python
from TGmessage import send_photo

await send_photo(
    dialog="@username",
    photo="path/to/image.jpg",
    caption="这是图片说明"
)
```

### 6. 转发消息

```python
async with TelegramUnreadMessageAPI() as api:
    await api.forward_message(
        from_dialog="源群组",
        to_dialog="目标群组",
        message_ids=[123, 456, 789]  # 消息ID列表
    )
```

## 完整示例: 自动回复未读消息

```python
import asyncio
from TGmessage import TelegramUnreadMessageAPI

async def auto_reply():
    """自动回复所有私聊的未读消息"""
    async with TelegramUnreadMessageAPI() as api:
        # 获取所有有未读消息的对话
        dialogs = await api.get_all_unread_dialogs()
        
        for dialog in dialogs:
            # 只处理私聊
            if dialog.is_user:
                print(f"处理来自 {dialog.name} 的消息...")
                
                # 获取该对话的未读消息
                messages = await api.get_unread_messages(
                    dialog=dialog.dialog_id,
                    limit=5
                )
                
                # 发送回复
                if messages:
                    await api.send_message(
                        dialog=dialog.dialog_id,
                        text=f"收到你的 {len(messages)} 条消息,稍后回复!"
                    )
                    print(f"✓ 已回复 {dialog.name}")

if __name__ == '__main__':
    asyncio.run(auto_reply())
```

## 故障排查

### 问题 1: ImportError: No module named 'telethon'

**解决方法:**
```bash
pip install telethon python-dotenv
```

### 问题 2: ValueError: API ID or API Hash not configured

**解决方法:**
- 确保创建了 `.env` 文件
- 确保填写了正确的 `TG_API_ID` 和 `TG_API_HASH`

### 问题 3: 首次登录失败

**解决方法:**
- 确保手机号格式正确(包含国家代码,如 +86)
- 确保验证码输入正确
- 如果开启了两步验证,需要输入密码

### 问题 4: FloodWaitError

**说明:** Telegram 限制了请求频率,库会自动等待并重试,无需手动处理。

### 问题 5: 找不到对话

**解决方法:**
- 使用 `get_unread_dialogs()` 查看所有对话的名称和ID
- 确保对话标识符(名称/用户名/ID)正确

## 下一步

- 查看 `README.md` 了解完整 API 文档
- 查看 `examples.py` 了解更多使用示例
- 查看 `PROJECT_SUMMARY.md` 了解项目架构

## 需要帮助?

- 查看完整文档: `README.md`
- 查看示例代码: `examples.py`
- 提交 Issue: GitHub Issues

---

**祝使用愉快! 🎉**

