"""
Telegram 客户端封装模块
负责客户端的初始化、认证和连接管理
"""
import logging
from pathlib import Path
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    AuthKeyError,
    UnauthorizedError,
    RPCError
)

from .config import Config, get_config
from .utils import async_retry


logger = logging.getLogger(__name__)


class TelegramClientWrapper:
    """Telegram 客户端封装类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化 Telegram 客户端
        
        Args:
            config: 配置对象,如果为 None 则使用默认配置
        """
        self.config = config or get_config()
        self._client: Optional[TelegramClient] = None
        self._is_connected = False
        
        logger.info(f"初始化 Telegram 客户端: {self.config}")
    
    @property
    def client(self) -> TelegramClient:
        """获取 TelegramClient 实例"""
        if self._client is None:
            raise RuntimeError("客户端未初始化,请先调用 connect() 方法")
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """检查客户端是否已连接"""
        return self._is_connected and self._client is not None
    
    async def connect(
        self,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        force_reconnect: bool = False
    ) -> 'TelegramClientWrapper':
        """
        连接并认证 Telegram 客户端
        
        Args:
            phone: 手机号码(包括国家代码,如 +8613800138000)
                   如果会话已存在则不需要
            password: 两步验证密码(如果启用了 2FA)
            force_reconnect: 是否强制重新连接
            
        Returns:
            self,支持链式调用
            
        Raises:
            PhoneNumberInvalidError: 手机号码无效
            SessionPasswordNeededError: 需要两步验证密码
            AuthKeyError: 认证密钥错误
            UnauthorizedError: 未授权错误
        """
        if self.is_connected and not force_reconnect:
            logger.info("客户端已连接")
            return self
        
        try:
            proxy = None
            if self.config.proxy_type:
                try:
                    import python_socks  # noqa: F401
                except ImportError as e:
                    raise RuntimeError(
                        "python-socks[asyncio] is required for proxy support. "
                        "Install python-socks[asyncio]."
                    ) from e
                if not self.config.proxy_host or not self.config.proxy_port:
                    raise ValueError("Proxy host/port is required when proxy is set.")

                rdns = True if self.config.proxy_rdns is None else self.config.proxy_rdns
                proxy = {
                    "proxy_type": self.config.proxy_type,
                    "addr": self.config.proxy_host,
                    "port": self.config.proxy_port,
                    "rdns": rdns,
                }
                if self.config.proxy_username:
                    proxy["username"] = self.config.proxy_username
                if self.config.proxy_password:
                    proxy["password"] = self.config.proxy_password
                auth_enabled = bool(self.config.proxy_username or self.config.proxy_password)
                logger.info(
                    "Proxy enabled: type=%s host=%s port=%s rdns=%s auth=%s",
                    self.config.proxy_type,
                    self.config.proxy_host,
                    self.config.proxy_port,
                    rdns,
                    "yes" if auth_enabled else "no",
                )
            else:
                logger.info("Proxy disabled.")
            # 创建客户端实例
            self._client = TelegramClient(
                str(self.config.session_path),
                self.config.api_id,
                self.config.api_hash,
                proxy=proxy,
                # 设置超时和重试参数
                connection_retries=5,
                retry_delay=1,
                timeout=10,
                # 自动重连
                auto_reconnect=True,
            )
            
            logger.info("正在连接到 Telegram...")
            await self._client.connect()
            
            # 检查是否已授权
            if not await self._client.is_user_authorized():
                logger.info("需要进行用户认证")
                await self._authenticate(phone, password)
            else:
                logger.info("使用已有会话,无需重新认证")
            
            self._is_connected = True
            
            # 获取并打印当前用户信息
            me = await self._client.get_me()
            logger.info(
                f"成功登录: {me.first_name} "
                f"{me.last_name or ''} (@{me.username or 'N/A'})"
            )
            
            return self
            
        except PhoneNumberInvalidError as e:
            logger.error(f"手机号码无效: {e}")
            raise
        except AuthKeyError as e:
            logger.error(f"认证密钥错误,可能需要删除会话文件重新登录: {e}")
            raise
        except UnauthorizedError as e:
            logger.error(f"未授权错误: {e}")
            raise
        except RPCError as e:
            logger.error(f"Telegram RPC 错误: {e}")
            raise
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise
    
    async def _authenticate(self, phone: Optional[str], password: Optional[str]):
        """
        执行用户认证流程
        
        Args:
            phone: 手机号码
            password: 两步验证密码
        """
        if not phone:
            phone = input("Enter phone with country code (e.g. +8613800138000): ").strip()
        if not phone:
            raise ValueError(
                "首次登录需要提供手机号码。\n"
                "格式: +8613800138000 (包括国家代码)"
            )
        
        try:
            # 使用 start() 方法进行交互式登录
            # start() 会自动处理发送验证码、输入验证码等流程
            await self._client.start(
                phone=phone,
                password=password or (lambda: input('请输入两步验证密码: '))
            )
            
        except SessionPasswordNeededError:
            if not password:
                raise ValueError(
                    "您的账号启用了两步验证,请提供密码参数"
                )
            raise
    
    async def disconnect(self):
        """断开客户端连接"""
        if self._client and self._is_connected:
            await self._client.disconnect()
            self._is_connected = False
            logger.info("客户端已断开连接")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return await self.connect()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    def __repr__(self) -> str:
        status = "已连接" if self.is_connected else "未连接"
        return f"TelegramClientWrapper(status={status}, config={self.config})"
