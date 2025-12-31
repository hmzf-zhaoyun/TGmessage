# 🎣 摸鱼工具使用指南

**fishing.py** - TGmessage 命令行工具,专为在工作时快速查看 Telegram 消息设计。

## 🚀 快速开始

### 1. 确保已配置
```bash
# 确保 .env 文件已配置
cd TGmessage
```

### 2. 使用方式

#### 📊 快速查看摘要(默认)
```bash
python fishing.py
```
输出示例:
```
==================================================
  📱 Telegram 未读消息摘要
  2024-01-15 14:30:25
==================================================

  📊 统计:
     总未读: 15 条消息
     私聊: 2 个 (8 条)
     群组: 3 个 (7 条)
     频道: 0 个 (0 条)

  👤 私聊消息 (重要):
     • 张三: 3 条
       └─ 晚上一起吃饭吗?
     • 李四: 5 条
       └─ 会议推迟到明天

  👥 群组消息:
     • 技术交流群: 4 条 (@2)
     • 产品讨论组: 3 条
```

#### 📨 查看消息详情
```bash
# 查看最近10条未读消息
python fishing.py -l

# 查看最近20条
python fishing.py -l 20
```

输出示例:
```
==================================================
  📨 最近 10 条未读消息
  2024-01-15 14:30:25
==================================================

👤 [张三]
------------------------------------------------------
14:25 张三:
  晚上一起吃饭吗?

14:28 张三:
  在吗?

👥 [技术交流群]
------------------------------------------------------
14:20 王五:
  @你 这个bug怎么解决?
  📎 [photo]

14:22 赵六:
  可以用XXX方法
```

#### 💬 查看特定对话
```bash
# 使用对话名称
python fishing.py -c "张三"

# 使用用户名
python fishing.py -c "@username"

# 使用群组名
python fishing.py -c "技术交流群"
```

#### 🎮 交互模式(推荐)
```bash
python fishing.py -i
```

交互模式命令:
```
TG> s              # 查看摘要
TG> l              # 查看10条消息
TG> l 20           # 查看20条消息
TG> c 张三         # 查看"张三"的消息
TG> send 张三 好的   # 发送消息给"张三"
TG> help           # 显示帮助
TG> q              # 退出
```

## 📖 命令参考

### 命令行选项

| 命令 | 说明 | 示例 |
|------|------|------|
| (无参数) | 快速查看摘要 | `python fishing.py` |
| `-l [数量]` | 查看消息列表 | `python fishing.py -l 15` |
| `-c <对话>` | 查看特定对话 | `python fishing.py -c "张三"` |
| `-i` | 交互模式 | `python fishing.py -i` |
| `-h` | 显示帮助 | `python fishing.py -h` |

### 交互模式命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `s`, `summary` | 查看摘要 | `s` |
| `l`, `list [数量]` | 查看消息列表 | `l 20` |
| `c`, `chat <名称>` | 查看特定对话 | `c 张三` |
| `m`, `send <对话> <消息>` | 发送消息 | `send 张三 收到` |
| `h`, `help` | 显示帮助 | `h` |
| `q`, `quit` | 退出 | `q` |

## 💡 使用场景

### 场景 1: 快速检查
工作间隙,快速看一眼有没有重要消息:
```bash
python fishing.py
```

### 场景 2: 详细查看
发现有未读消息,查看详细内容:
```bash
python fishing.py -l
```

### 场景 3: 专注某个对话
需要专门查看某个人的消息:
```bash
python fishing.py -c "老板"
```

### 场景 4: 持续监控
需要持续监控消息(交互模式):
```bash
python fishing.py -i
# 然后随时输入命令查看
```

### 场景 5: 快速回复
看到消息后快速回复:
```bash
python fishing.py -i
TG> send 张三 好的,马上处理
```

## 🎯 摸鱼技巧

### 技巧 1: 创建快捷方式
Windows:
```batch
# 创建 tg.bat
@echo off
cd /d D:\program\小东西\TGmessage
python fishing.py %*
```

Linux/Mac:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias tg='cd ~/path/to/TGmessage && python fishing.py'
```

使用:
```bash
tg          # 快速查看
tg -l       # 查看消息
tg -i       # 交互模式
```

### 技巧 2: 定时检查
使用 cron(Linux) 或任务计划程序(Windows)定时运行:
```bash
# 每10分钟检查一次
*/10 * * * * cd ~/TGmessage && python fishing.py >> ~/tg_check.log
```

### 技巧 3: 只看重要消息
修改脚本,只显示私聊或@提及的消息(已内置优先显示私聊)

### 技巧 4: 后台运行
```bash
# Linux/Mac 后台运行
nohup python fishing.py -i &

# Windows 最小化运行
start /min python fishing.py -i
```

## ⚠️ 注意事项

1. **首次使用需要登录** - 会要求输入手机号和验证码
2. **网络连接** - 需要能访问 Telegram 服务器
3. **API 限制** - 频繁请求可能触发限流(工具已内置处理)
4. **隐私安全** - 不要在公共电脑上使用

## 🔧 故障排查

### 问题: 连接失败
```
解决: 检查网络连接,确保能访问 Telegram
```

### 问题: 找不到对话
```
解决: 使用 -i 交互模式,输入 s 查看所有对话名称
```

### 问题: 中文显示乱码
```
解决: 
Windows: chcp 65001  # 设置 UTF-8 编码
Linux/Mac: export LANG=zh_CN.UTF-8
```

## 📝 示例工作流

```bash
# 早上上班
python fishing.py              # 快速查看有什么消息

# 发现有重要私聊
python fishing.py -l           # 查看详细内容

# 需要回复某人
python fishing.py -i           # 进入交互模式
TG> send 张三 收到,马上处理
TG> q                          # 退出

# 中午休息
python fishing.py              # 再次检查

# 下午工作中
python fishing.py -i           # 交互模式常驻
TG> s                          # 随时查看摘要
```

## 🎊 高级用法

### 结合其他工具
```bash
# 统计未读消息数
python fishing.py | grep "总未读"

# 只看私聊
python fishing.py -l | grep "👤"

# 保存到文件
python fishing.py -l > messages.txt
```

---

**享受摸鱼时光! 🎣**

