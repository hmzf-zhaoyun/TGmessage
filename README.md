# TGmessage - Telegram 未读消息获取工具

基于 Telethon 库开发的 Telegram 未读消息获取工具,提供简洁的 API 来获取和管理 Telegram 的未读消息。

## 功能特性

### 📩 读取消息

- ✅ 获取所有对话的未读消息
- ✅ 获取指定群组/频道/用户的未读消息
- ✅ 支持通过群组 ID、用户名或名称筛选
- ✅ 返回详细的消息信息(内容、发送者、时间戳等)
- ✅ **显示消息回复链** - 自动显示被回复的消息内容和发送者

### ✍️ 发送消息

- ✅ 发送文本消息(支持 Markdown/HTML 格式)
- ✅ **回复消息** - 指定回复的消息 ID，建立回复关系
- ✅ **@ 提及用户** - 在消息中提及其他用户
- ✅ 发送图片和文件
- ✅ 转发消息
- ✅ 编辑已发送的消息
- ✅ 删除消息(支持双向删除)

### 🔧 技术特性

- ✅ 完善的错误处理(网络错误、认证失败等)
- ✅ 异步编程支持
- ✅ 支持会话管理,避免重复登录
- ✅ 环境变量配置,保护敏感信息
- ✅ 自动处理 FloodWaitError(请求频率限制)

## 安装依赖

```bash
# 安装必需的依赖
pip install telethon python-dotenv
```

## 配置

### 1. 获取 Telegram API 凭证

访问 [https://my.telegram.org/apps](https://my.telegram.org/apps) 创建应用并获取:

- API ID
- API Hash

### 2. 配置环境变量

复制 `.env.example` 为 `.env`:

```bash
cp .env.example .env
```

编辑 `.env` 文件,填入你的凭证:

```env
TG_API_ID=12345678
TG_API_HASH=0123456789abcdef0123456789abcdef
TG_SESSION_NAME=my_telegram_session
TG_SESSION_DIR=./sessions
```

## 🎣 命令行工具(摸鱼专用)

TGmessage 提供了命令行工具,适合在工作时快速查看 Telegram 消息。

### 快速查看

```bash
python fishing.py              # 查看摘要
python fishing.py -l           # 查看消息详情
python fishing.py -c "张三"     # 查看特定对话
python fishing.py -i           # 交互模式(推荐)
```

### 交互模式示例

```bash
$ python fishing.py -i

TG> s              # 查看摘要
TG> l 20           # 查看20条消息
TG> c 技术群       # 查看"技术群"的消息
TG> send 张三 收到  # 发送消息
TG> q              # 退出
```

详细说明请查看 [摸鱼工具使用指南](FISHING_GUIDE.md)

## 快速开始

### 示例 1: 获取所有有未读消息的对话

```python
import asyncio
from TGmessage import get_unread_dialogs

async def main():
    # 获取所有有未读消息的对话
    dialogs = await get_unread_dialogs()

    for dialog in dialogs:
        print(f"{dialog.name}: {dialog.unread_count} 条未读消息")

asyncio.run(main())
```

### 示例 2: 获取所有未读消息

```python
import asyncio
from TGmessage import get_unread_messages

async def main():
    # 获取所有未读消息
    messages = await get_unread_messages()

    for msg in messages:
        print(f"[{msg.chat_name}] {msg.sender_name}: {msg.content}")

asyncio.run(main())
```

### 示例 3: 获取特定群组的未读消息

```python
import asyncio
from TGmessage import get_unread_messages

async def main():
    # 通过群组名称获取
    messages = await get_unread_messages(dialog="我的群组")

    # 通过用户名获取
    messages = await get_unread_messages(dialog="@groupusername")

    # 通过 ID 获取
    messages = await get_unread_messages(dialog=-1001234567890)

    for msg in messages:
        print(msg)

asyncio.run(main())
```

### 示例 4: 使用 API 类进行更多控制

```python
import asyncio
from TGmessage import TelegramUnreadMessageAPI

async def main():
    api = TelegramUnreadMessageAPI()

    try:
        # 连接(首次登录需要提供手机号)
        await api.connect(phone='+8613800138000')

        # 获取对话列表
        dialogs = await api.get_all_unread_dialogs()

        # 获取特定对话的消息
        messages = await api.get_unread_messages(
            dialog="MyGroup",
            limit=10  # 限制数量
        )

        for msg in messages:
            print(msg.to_dict())

    finally:
        await api.disconnect()

asyncio.run(main())
```

### 示例 5: 使用异步上下文管理器

```python
import asyncio
from TGmessage import TelegramUnreadMessageAPI

async def main():
    async with TelegramUnreadMessageAPI() as api:
        dialogs = await api.get_all_unread_dialogs()
        print(f"有 {len(dialogs)} 个对话有未读消息")

asyncio.run(main())
```

### 示例 6: 发送文本消息

```python
import asyncio
from TGmessage import send_message

async def main():
    # 发送简单文本消息
    msg_id = await send_message(
        dialog="@username",
        text="Hello from TGmessage!"
    )
    print(f"消息已发送,ID: {msg_id}")

    # 发送 Markdown 格式消息
    await send_message(
        dialog="MyGroup",
        text="**粗体** *斜体* `代码`",
        parse_mode='md'
    )

    # 回复消息
    await send_message(
        dialog="@username",
        text="这是一条回复",
        reply_to=msg_id  # 回复刚才发送的消息
    )

    # @ 提及用户（在群组中）
    await send_message(
        dialog="MyGroup",
        text="@username 请查看这条消息"
    )

    # 使用显示名称提及（适用于没有用户名的用户）
    await send_message(
        dialog="MyGroup",
        text='@"张三"(123456789) 你好！'
    )

asyncio.run(main())
```

### 示例 7: 发送图片和文件

```python
import asyncio
from TGmessage import send_photo, send_file

async def main():
    # 发送图片
    await send_photo(
        dialog="@username",
        photo="image.jpg",
        caption="这是一张图片"
    )

    # 发送文件
    await send_file(
        dialog="MyGroup",
        file="document.pdf"
    )

asyncio.run(main())
```

### 示例 8: 消息操作(编辑、转发、删除)

```python
import asyncio
from TGmessage import TelegramUnreadMessageAPI

async def main():
    async with TelegramUnreadMessageAPI() as api:
        # 发送消息
        msg_id = await api.send_message(
            dialog="@username",
            text="原始消息"
        )

        # 编辑消息
        await api.edit_message(
            dialog="@username",
            message_id=msg_id,
            new_text="已编辑的消息"
        )

        # 转发消息
        await api.forward_message(
            from_dialog="@username",
            to_dialog="me",  # "me" = 我的收藏
            message_ids=msg_id
        )

        # 删除消息
        await api.delete_messages(
            dialog="@username",
            message_ids=msg_id,
            revoke=True  # 双向删除
        )

asyncio.run(main())
```

## API 文档

### 便捷函数

#### `get_unread_dialogs()`

获取所有有未读消息的对话。

**参数:**

- `phone` (str, 可选): 手机号码(首次登录需要)
- `password` (str, 可选): 两步验证密码
- `include_archived` (bool): 是否包含已归档对话,默认 False
- `config` (Config, 可选): 自定义配置对象

**返回:** `List[DialogInfo]`

#### `get_unread_messages()`

获取未读消息。

**参数:**

- `dialog` (int | str, 可选): 对话标识符,为 None 时获取所有对话的未读消息
- `phone` (str, 可选): 手机号码(首次登录需要)
- `password` (str, 可选): 两步验证密码
- `limit` (int, 可选): 限制消息数量
- `include_archived` (bool): 是否包含已归档对话
- `config` (Config, 可选): 自定义配置对象

**返回:** `List[UnreadMessage]`

#### `send_message()`

发送文本消息。

**参数:**

- `dialog` (int | str): 对话标识符(ID/用户名/名称)
- `text` (str): 消息文本内容
- `phone` (str, 可选): 手机号码(首次登录需要)
- `password` (str, 可选): 两步验证密码
- `parse_mode` (str, 可选): 解析模式('md' 为 Markdown, 'html' 为 HTML)
- `reply_to` (int, 可选): 回复的消息 ID
- `config` (Config, 可选): 自定义配置对象

**返回:** `int` - 发送的消息 ID

#### `send_photo()`

发送图片。

**参数:**

- `dialog` (int | str): 对话标识符
- `photo` (str | Path): 图片文件路径
- `caption` (str, 可选): 图片说明
- `phone` (str, 可选): 手机号码(首次登录需要)
- `password` (str, 可选): 两步验证密码
- `config` (Config, 可选): 自定义配置对象

**返回:** `int` - 发送的消息 ID

#### `send_file()`

发送文件。

**参数:**

- `dialog` (int | str): 对话标识符
- `file` (str | Path): 文件路径
- `caption` (str, 可选): 文件说明
- `phone` (str, 可选): 手机号码(首次登录需要)
- `password` (str, 可选): 两步验证密码
- `config` (Config, 可选): 自定义配置对象

**返回:** `int` - 发送的消息 ID

### TelegramUnreadMessageAPI 类

主要 API 类,提供完整的消息读取和发送功能。

#### 读取消息方法

- `get_all_unread_dialogs(include_archived=False)` - 获取所有有未读消息的对话
- `get_unread_messages(dialog=None, limit=None, include_archived=False)` - 获取未读消息

#### 发送消息方法

- `send_message(dialog, text, parse_mode='md', reply_to=None)` - 发送文本消息
- `send_photo(dialog, photo, caption=None, reply_to=None)` - 发送图片
- `send_file(dialog, file, caption=None, reply_to=None)` - 发送文件

#### 消息操作方法

- `forward_message(from_dialog, to_dialog, message_ids)` - 转发消息
- `edit_message(dialog, message_id, new_text, parse_mode='md')` - 编辑消息
- `delete_messages(dialog, message_ids, revoke=True)` - 删除消息

### 数据模型

#### UnreadMessage

未读消息数据模型。

**属性:**

- `message_id`: 消息 ID
- `content`: 消息内容
- `date`: 发送时间
- `sender_id`: 发送者 ID
- `sender_name`: 发送者名称
- `sender_username`: 发送者用户名
- `chat_id`: 对话 ID
- `chat_name`: 对话名称
- `chat_username`: 对话用户名
- `is_user`: 是否为私聊
- `is_group`: 是否为群组
- `is_channel`: 是否为频道
- `has_media`: 是否包含媒体
- `media_type`: 媒体类型

**方法:**

- `to_dict()`: 转换为字典
- `__str__()`: 格式化输出

#### DialogInfo

对话信息数据模型。

**属性:**

- `dialog_id`: 对话 ID
- `name`: 对话名称
- `username`: 对话用户名
- `unread_count`: 未读消息数
- `unread_mentions_count`: 未读提及数
- `is_user`: 是否为私聊
- `is_group`: 是否为群组
- `is_channel`: 是否为频道
- `is_pinned`: 是否已置顶
- `is_archived`: 是否已归档
- `last_message_date`: 最后一条消息时间
- `last_message_text`: 最后一条消息内容

## 错误处理

该库已内置完善的错误处理:

```python
import asyncio
from TGmessage import get_unread_messages
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    FloodWaitError,
)

async def main():
    try:
        messages = await get_unread_messages()
    except SessionPasswordNeededError:
        print("需要两步验证密码")
    except PhoneNumberInvalidError:
        print("手机号码无效")
    except FloodWaitError as e:
        print(f"请求过于频繁,需要等待 {e.seconds} 秒")
    except ValueError as e:
        print(f"参数错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

asyncio.run(main())
```

## 高级用法

### 自定义配置

```python
from TGmessage import Config, TelegramUnreadMessageAPI

# 创建自定义配置
config = Config()
# 或从指定的 .env 文件加载
# config = Config(env_file='/path/to/.env')

api = TelegramUnreadMessageAPI(config)
```

### 过滤消息

```python
import asyncio
from TGmessage import get_unread_messages

async def main():
    all_messages = await get_unread_messages()

    # 只获取私聊消息
    user_messages = [m for m in all_messages if m.is_user]

    # 只获取群组消息
    group_messages = [m for m in all_messages if m.is_group]

    # 只获取频道消息
    channel_messages = [m for m in all_messages if m.is_channel]

    # 只获取包含媒体的消息
    media_messages = [m for m in all_messages if m.has_media]

    # 只获取今天的消息
    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_messages = [
        m for m in all_messages
        if m.date.date() == today
    ]

asyncio.run(main())
```

### 导出为 JSON

```python
import asyncio
import json
from TGmessage import get_unread_messages

async def main():
    messages = await get_unread_messages(limit=50)

    # 转换为字典列表
    messages_dict = [msg.to_dict() for msg in messages]

    # 保存为 JSON
    with open('unread_messages.json', 'w', encoding='utf-8') as f:
        json.dump(messages_dict, f, ensure_ascii=False, indent=2)

asyncio.run(main())
```

## 项目结构

```
TGmessage/
├── __init__.py           # 包导出
├── config.py             # 配置管理
├── client.py             # Telegram 客户端封装
├── message_fetcher.py    # 消息获取核心逻辑
├── models.py             # 数据模型
├── utils.py              # 工具函数
├── main.py               # 主 API
├── examples.py           # 使用示例
├── .env.example          # 环境变量示例
├── README.md             # 使用文档
└── sessions/             # 会话文件目录(自动创建)
```

## 注意事项

1. **首次登录**: 首次使用需要提供手机号码,Telegram 会发送验证码
2. **会话管理**: 登录后会保存会话文件,下次无需重复登录
3. **API 限制**: Telegram 有请求频率限制,请勿频繁调用
4. **安全性**:
   - 不要将 `.env` 文件提交到版本控制系统
   - 不要泄露 API ID 和 API Hash
   - 会话文件包含认证信息,请妥善保管

## 常见问题

### Q: 如何获取群组 ID?

A: 可以使用 `get_unread_dialogs()` 查看所有对话的 ID。

### Q: FloodWaitError 如何处理?

A: 库已内置自动等待和重试机制,无需手动处理。

### Q: 支持 Bot Token 登录吗?

A: 当前版本主要支持用户账号登录,Bot 账号功能将在后续版本添加。

### Q: 会话文件存储在哪里?

A: 默认存储在 `./sessions/` 目录下,可通过 `TG_SESSION_DIR` 环境变量自定义。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 相关链接

- [Telethon 官方文档](https://docs.telethon.dev/)
- [Telegram API 文档](https://core.telegram.org/api)
- [获取 API 凭证](https://my.telegram.org/apps)
