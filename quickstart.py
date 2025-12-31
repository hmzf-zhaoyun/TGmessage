"""
快速入门脚本
首次使用时运行此脚本进行配置和测试
"""
import asyncio
import os
from pathlib import Path


def setup_env_file():
    """创建 .env 配置文件"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        print("✓ .env 文件已存在")
        return True
    
    print("\n=== 配置 Telegram API 凭证 ===\n")
    print("请访问 https://my.telegram.org/apps 获取 API 凭证")
    print()
    
    api_id = input("请输入 API ID: ").strip()
    api_hash = input("请输入 API Hash: ").strip()
    
    if not api_id or not api_hash:
        print("❌ API ID 和 API Hash 不能为空")
        return False
    
    # 验证 API ID 是否为数字
    try:
        int(api_id)
    except ValueError:
        print("❌ API ID 必须是数字")
        return False
    
    # 创建 .env 文件
    env_content = f"""# Telegram API 配置
TG_API_ID={api_id}
TG_API_HASH={api_hash}
TG_SESSION_NAME=telegram_session
TG_SESSION_DIR=./sessions
# Proxy (optional)
# TG_PROXY_TYPE=socks5
# TG_PROXY_HOST=127.0.0.1
# TG_PROXY_PORT=1080
# TG_PROXY_USERNAME=
# TG_PROXY_PASSWORD=
# TG_PROXY_RDNS=true
"""
    
    env_path.write_text(env_content, encoding='utf-8')
    print("\n✓ .env 配置文件已创建")
    return True


async def test_connection():
    """测试连接"""
    print("\n=== 测试 Telegram 连接 ===\n")
    
    # 导入需要的模块
    try:
        from TGmessage import TelegramUnreadMessageAPI
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n请先安装依赖:")
        print("  pip install telethon python-dotenv")
        return False
    
    api = TelegramUnreadMessageAPI()
    
    try:
        # 尝试连接
        print("正在连接到 Telegram...")
        print("首次登录需要输入手机号和验证码\n")
        
        phone = input("请输入手机号(包括国家代码,如 +8613800138000): ").strip()
        
        if not phone:
            print("❌ 手机号不能为空")
            return False
        
        await api.connect(phone=phone)
        
        print("\n✓ 连接成功!")
        
        # 获取未读对话
        print("\n正在获取未读消息对话列表...")
        dialogs = await api.get_all_unread_dialogs()
        
        if dialogs:
            print(f"\n找到 {len(dialogs)} 个有未读消息的对话:\n")
            for i, dialog in enumerate(dialogs[:5], 1):  # 只显示前5个
                print(f"{i}. {dialog.name}: {dialog.unread_count} 条未读消息")
            
            if len(dialogs) > 5:
                print(f"   ... 还有 {len(dialogs) - 5} 个对话")
        else:
            print("\n没有未读消息")
        
        print("\n✓ 测试完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await api.disconnect()


async def main():
    """主函数"""
    print("=" * 60)
    print("  TGmessage - Telegram 未读消息获取工具 - 快速入门")
    print("=" * 60)
    
    # 步骤1: 设置环境变量
    if not setup_env_file():
        print("\n配置失败,请重新运行脚本")
        return
    
    # 步骤2: 测试连接
    await test_connection()
    
    print("\n" + "=" * 60)
    print("\n下一步:")
    print("  1. 查看 README.md 了解详细使用方法")
    print("  2. 运行 examples.py 查看更多示例")
    print("  3. 在你的代码中导入并使用:")
    print()
    print("     from TGmessage import get_unread_messages")
    print("     messages = await get_unread_messages()")
    print()
    print("=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
