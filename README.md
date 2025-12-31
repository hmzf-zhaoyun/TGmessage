# TGmessage

TGmessage 是一个基于 Telethon 的 Telegram 未读消息获取与发送工具，提供可编程 API 与命令行“摸鱼”工具（fishing_tool），用于快速查看未读消息并进行常见操作。

## 主要特性

- 获取未读对话与消息，支持按对话 ID / 用户名 / 名称定位
- 发送文本、图片、文件，以及转发、编辑、删除消息
- 对话已读标记与消息追踪（本地 SQLite），减少遗漏
- 命令行摘要/列表/对话查看与交互式操作
- 支持会话文件复用与可选代理配置

## 技术栈

- Python
- Telethon
- python-dotenv
- PySocks
- 可选：`python-socks[asyncio]`（仅在启用代理时需要）

## 安装

```bash
pip install -r requirements.txt
# 如需代理支持
pip install "python-socks[asyncio]"
```

## 配置

项目通过环境变量或 `.env` 文件读取配置，默认在项目根目录查找 `.env`。

必填：
- `TG_API_ID`：Telegram API ID
- `TG_API_HASH`：Telegram API Hash

可选：
- `TG_SESSION_NAME`：会话名，默认 `telegram_session`
- `TG_SESSION_DIR`：会话文件目录，默认 `./sessions`
- `TG_MAX_UNREAD_FETCH`：单次对话拉取上限（命令行 `chat` 使用），默认 `60`

代理相关（任意一项启用即视为开启代理）：
- `TG_PROXY_TYPE`：`socks5` / `socks4` / `http` / `https`
- `TG_PROXY_HOST`
- `TG_PROXY_PORT`
- `TG_PROXY_USERNAME`（可选）
- `TG_PROXY_PASSWORD`（可选）
- `TG_PROXY_RDNS`：`true`/`false`，默认 `true`

示例 `.env`：

```env
TG_API_ID=12345678
TG_API_HASH=0123456789abcdef0123456789abcdef
TG_SESSION_NAME=my_session
TG_SESSION_DIR=./sessions
TG_MAX_UNREAD_FETCH=60
```

## 使用方法

### 作为库使用

```python
import asyncio
from TGmessage import (
    get_unread_dialogs,
    get_unread_messages,
    send_message,
    TelegramUnreadMessageAPI,
)

async def main():
    dialogs = await get_unread_dialogs()
    for d in dialogs:
        print(d)

    messages = await get_unread_messages(dialog="MyGroup", limit=20)
    for m in messages:
        print(m)

    await send_message(dialog="@username", text="Hello from TGmessage")

    async with TelegramUnreadMessageAPI() as api:
        dialogs = await api.get_all_unread_dialogs()
        if dialogs:
            await api.mark_dialog_read(dialogs[0].dialog_id)

asyncio.run(main())
```

### 命令行工具

支持 `fishing.py`（兼容入口）与 `fishing_tool` 模块。

```bash
# 摘要视图
python fishing.py
python -m fishing_tool

# 最近未读列表
python fishing.py -l 10
python -m fishing_tool -l 10

# 指定对话
python fishing.py -c "群组名称"
python -m fishing_tool -c "群组名称"

# 交互模式
python fishing.py -i
python -m fishing_tool -i
```

交互模式常用命令：
- `s`/`summary`：摘要
- `l`/`list [数量]`：最近未读列表
- `c`/`chat [对话]`：查看对话
- `m`/`send`：发送消息
- `r`/`reply`、`e`/`edit`、`d`/`delete`、`f`/`forward`
- `stars`/`star`/`unstar`/`use`/`back`：收藏与切换对话

## 项目结构

```
TGmessage/                 # 核心库
  config.py                # 配置读取与校验
  client.py                # Telethon 客户端封装
  message_fetcher.py       # 未读消息获取
  message_sender.py        # 消息发送与操作
  message_tracker.py       # 本地消息追踪(SQLite)
  models.py                # 数据模型
fishing_tool/              # 命令行工具
  core/                    # 业务逻辑
  ui/                      # 交互界面
fishing.py                 # 兼容入口
requirements.txt           # 依赖
LICENSE
```

## 常见问题

- 首次登录需要手机号验证码；若启用了两步验证，需要提供 `password` 或按提示输入。
- 会话文件默认保存在 `./sessions`；可通过 `TG_SESSION_DIR` 调整路径。
- 消息追踪数据库位置：`~/.tgmessage/message_tracker.db`。
- 收藏对话文件位置：项目根目录 `.tgmessage_favorites.json`。
- 使用代理时请先安装 `python-socks[asyncio]` 并配置 `TG_PROXY_*`。

## 许可证

MIT License，详见 `LICENSE`。
