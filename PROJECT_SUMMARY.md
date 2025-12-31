# TGmessage 项目开发总结

## 项目概述

**项目名称**: TGmessage - Telegram 未读消息获取与发送工具  
**开发语言**: Python 3.7+  
**核心框架**: Telethon (Telegram MTProto API 库)  
**开发日期**: 2024

## 核心功能

### 1. 消息读取功能
- ✅ 获取所有未读消息
- ✅ 获取特定对话的未读消息
- ✅ 列出所有有未读消息的对话
- ✅ 支持通过 ID/用户名/名称筛选对话
- ✅ 返回详细消息信息(内容、发送者、时间戳、媒体类型等)

### 2. 消息发送功能
- ✅ 发送文本消息(支持 Markdown/HTML 格式)
- ✅ 发送图片
- ✅ 发送文件
- ✅ 回复特定消息
- ✅ 转发消息
- ✅ 编辑已发送的消息
- ✅ 删除消息(支持双向删除)

### 3. 技术特性
- ✅ 异步编程模式
- ✅ 完善的错误处理和自动重试机制
- ✅ FloodWaitError 自动处理
- ✅ 会话管理(避免重复登录)
- ✅ 环境变量配置(保护敏感信息)
- ✅ 类型提示(IDE 友好)

## 项目结构

```
TGmessage/
├── __init__.py           # 包导出,定义公共 API
├── config.py             # 配置管理(API ID/Hash、会话路径)
├── models.py             # 数据模型(UnreadMessage、DialogInfo)
├── utils.py              # 工具函数(重试装饰器、时间格式化等)
├── client.py             # Telegram 客户端封装
├── message_fetcher.py    # 消息获取核心逻辑
├── message_sender.py     # 消息发送核心逻辑
├── main.py               # 主 API 入口(统一接口)
├── examples.py           # 使用示例代码
├── quickstart.py         # 快速入门脚本
├── README.md             # 完整使用文档
├── .env.example          # 环境变量示例
└── .gitignore            # Git 忽略文件

sessions/                 # 会话文件目录(自动创建)
└── *.session             # Telegram 会话文件
```

## 核心模块说明

### config.py
- `Config` 类: 配置管理
- 从环境变量/`.env` 文件读取配置
- 自动验证必需配置
- 单例模式设计

### models.py
- `UnreadMessage` 数据类: 未读消息模型
- `DialogInfo` 数据类: 对话信息模型
- 提供 `to_dict()` 方法用于序列化

### utils.py
- `async_retry` 装饰器: 异步重试机制
- `handle_flood_wait` 装饰器: 自动处理 Telegram 限流
- `format_timestamp`: 时间格式化
- `get_media_type`: 媒体类型识别

### client.py
- `TelegramClientWrapper` 类: Telethon 客户端封装
- 处理认证流程(手机号、验证码、两步验证)
- 会话管理
- 连接状态管理

### message_fetcher.py
- `MessageFetcher` 类: 消息获取功能
- `get_all_unread_dialogs()`: 获取未读对话列表
- `get_all_unread_messages()`: 获取所有未读消息
- `get_unread_messages_from_dialog()`: 获取特定对话的未读消息

### message_sender.py
- `MessageSender` 类: 消息发送功能
- `send_text_message()`: 发送文本
- `send_photo()`: 发送图片
- `send_file()`: 发送文件
- `forward_message()`: 转发消息
- `edit_message()`: 编辑消息
- `delete_messages()`: 删除消息

### main.py
- `TelegramUnreadMessageAPI` 类: 统一 API 入口
- 集成读取和发送功能
- 支持异步上下文管理器
- 提供便捷函数: `get_unread_messages()`, `send_message()` 等

## 依赖库

```
telethon>=1.28.0       # Telegram MTProto API 客户端
python-dotenv>=0.19.0  # 环境变量管理
```

## 使用流程

### 1. 安装依赖
```bash
pip install telethon python-dotenv
```

### 2. 配置 API 凭证
创建 `.env` 文件:
```env
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
```

### 3. 快速开始
```bash
python quickstart.py
```

### 4. 使用示例
```python
import asyncio
from TGmessage import get_unread_messages, send_message

async def main():
    # 获取未读消息
    messages = await get_unread_messages()
    print(f"共有 {len(messages)} 条未读消息")
    
    # 发送消息
    await send_message(
        dialog="@username",
        text="Hello from TGmessage!"
    )

asyncio.run(main())
```

## 错误处理

库已内置以下错误处理:

1. **FloodWaitError**: 自动等待并重试
2. **SessionPasswordNeededError**: 提示需要两步验证密码
3. **PhoneNumberInvalidError**: 提示手机号无效
4. **NetworkError**: 自动重试(带指数退避)
5. **ValueError**: 参数验证错误

## 安全注意事项

1. **不要**将 `.env` 文件提交到版本控制系统
2. **不要**泄露 API ID 和 API Hash
3. **妥善保管**会话文件(包含认证信息)
4. **谨慎使用**自动化功能,避免触发 Telegram 限制

## 最佳实践

1. **使用异步上下文管理器**确保正确清理资源
2. **合理设置消息限制**避免一次性获取过多消息
3. **添加适当延迟**在批量操作时避免触发限流
4. **错误日志记录**便于问题排查
5. **定期更新依赖**保持与 Telegram API 兼容

## API 限制说明

Telegram 对 API 调用有以下限制:

- **消息发送**: 每秒约 30 条(私聊), 每分钟约 20 条(群组)
- **消息获取**: 较为宽松,但频繁请求会触发 FloodWaitError
- **文件上传**: 受大小和频率限制

库已内置自动处理机制,会自动等待并重试。

## 扩展功能建议

以下功能可在未来版本添加:

1. Bot Token 登录支持
2. 消息搜索功能
3. 批量消息操作
4. 消息统计分析
5. 媒体文件下载
6. 频道/群组管理
7. 用户信息查询
8. 消息定时发送

## 许可证

MIT License

## 联系方式

如有问题或建议,欢迎提交 Issue 或 Pull Request。

---

**开发完成时间**: 2024  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪

