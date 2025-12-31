# TGmessage 快速参考卡

## 📱 命令行工具(摸鱼专用)

### 一键查看
```bash
python fishing.py              # 摘要(推荐)
python fishing.py -l           # 详情
python fishing.py -i           # 交互模式
```

### 交互模式命令
```
s         查看摘要
l [数量]  查看消息列表
c <对话>  查看特定对话
send <对话> <消息>  发送消息
q         退出
```

---

## 💻 Python API

### 快速查看
```python
from TGmessage import get_unread_messages

# 获取所有未读
messages = await get_unread_messages()

# 获取特定对话
messages = await get_unread_messages(dialog="张三")
```

### 发送消息
```python
from TGmessage import send_message, send_photo

# 发送文本
await send_message(dialog="@user", text="Hello")

# 发送图片
await send_photo(dialog="@user", photo="pic.jpg")
```

### 完整API
```python
async with TelegramUnreadMessageAPI() as api:
    # 读取
    dialogs = await api.get_all_unread_dialogs()
    messages = await api.get_unread_messages()
    
    # 发送
    await api.send_message(dialog="@user", text="Hi")
    
    # 操作
    await api.forward_message(from_dialog="A", to_dialog="B", message_ids=123)
    await api.edit_message(dialog="@user", message_id=123, new_text="New")
    await api.delete_messages(dialog="@user", message_ids=[123])
```

---

## ⚙️ 配置(.env)

```env
TG_API_ID=你的API_ID
TG_API_HASH=你的API_HASH
TG_SESSION_NAME=my_session
TG_SESSION_DIR=./sessions
```

---

## 📂 文件说明

| 文件 | 用途 |
|------|------|
| `fishing.py` | 命令行工具(摸鱼) |
| `quickstart.py` | 快速入门脚本 |
| `examples.py` | 完整示例代码 |
| `README.md` | 完整文档 |
| `FISHING_GUIDE.md` | 摸鱼工具指南 |

---

## 🚀 常用场景

### 场景1: 快速检查消息
```bash
python fishing.py
```

### 场景2: 查看并回复
```bash
python fishing.py -i
TG> l              # 查看消息
TG> send 张三 收到  # 快速回复
```

### 场景3: 监控特定群组
```bash
python fishing.py -c "技术交流群"
```

### 场景4: Python集成
```python
# 获取未读并自动处理
messages = await get_unread_messages(limit=10)
for msg in messages:
    if msg.is_user:  # 只处理私聊
        print(f"{msg.sender_name}: {msg.content}")
```

---

## 🔧 故障排查

| 问题 | 解决方案 |
|------|---------|
| 找不到模块 | `pip install telethon python-dotenv` |
| 配置错误 | 检查 `.env` 文件 |
| 连接失败 | 检查网络,确保能访问Telegram |
| 找不到对话 | 使用 `python fishing.py -i` 然后 `s` 查看所有对话 |

---

## 📞 获取API凭证

1. 访问 https://my.telegram.org/apps
2. 登录Telegram
3. 创建应用
4. 复制 API ID 和 API Hash

---

**提示**: 首次使用需要手机号登录,会发送验证码

**保存此文件以便快速参考!**

