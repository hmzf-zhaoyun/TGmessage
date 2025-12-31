"""
配置管理模块
负责从环境变量或配置文件中读取敏感信息,如 API_ID, API_HASH 等
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Telegram API 配置管理类"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            env_file: .env 文件路径,默认为项目根目录的 .env
        """
        # 确定 .env 文件路径
        base_dir = Path(__file__).resolve().parent.parent
        if env_file is None:
            env_file = base_dir / '.env'
        else:
            env_file = Path(env_file)
        
        # 加载环境变量
        if env_file.exists():
            load_dotenv(env_file)
        
        # 读取配置
        self._api_id = os.getenv('TG_API_ID')
        self._api_hash = os.getenv('TG_API_HASH')
        self._session_name = os.getenv('TG_SESSION_NAME', 'telegram_session')
        self._session_dir = os.getenv('TG_SESSION_DIR', str(base_dir / 'sessions'))
        self._proxy_type = os.getenv('TG_PROXY_TYPE')
        self._proxy_host = os.getenv('TG_PROXY_HOST')
        self._proxy_port = os.getenv('TG_PROXY_PORT')
        self._proxy_username = os.getenv('TG_PROXY_USERNAME')
        self._proxy_password = os.getenv('TG_PROXY_PASSWORD')
        self._proxy_rdns = os.getenv('TG_PROXY_RDNS')
        self._max_unread_fetch = os.getenv('TG_MAX_UNREAD_FETCH', '60')
        
        # 验证必需的配置
        self._validate()
    
    def _validate(self):
        """验证必需的配置项是否存在"""
        if not self._api_id:
            raise ValueError(
                "TG_API_ID 未设置。请在环境变量或 .env 文件中设置。\n"
                "获取方式: https://my.telegram.org/apps"
            )
        
        if not self._api_hash:
            raise ValueError(
                "TG_API_HASH 未设置。请在环境变量或 .env 文件中设置。\n"
                "获取方式: https://my.telegram.org/apps"
            )
        
        # 确保 API_ID 是整数
        try:
            int(self._api_id)
        except ValueError:
            raise ValueError(f"TG_API_ID 必须是整数,当前值: {self._api_id}")

        try:
            max_unread_fetch = int(self._max_unread_fetch)
        except ValueError:
            raise ValueError("TG_MAX_UNREAD_FETCH 必须是整数")
        if max_unread_fetch < 1:
            raise ValueError("TG_MAX_UNREAD_FETCH 必须大于等于 1")
        self._max_unread_fetch = max_unread_fetch

        proxy_fields = (
            self._proxy_type,
            self._proxy_host,
            self._proxy_port,
            self._proxy_username,
            self._proxy_password,
            self._proxy_rdns,
        )
        if any(proxy_fields):
            if not self._proxy_type:
                raise ValueError("TG_PROXY_TYPE is required when proxy is set.")
            proxy_type = self._proxy_type.strip().lower()
            if proxy_type not in {'socks5', 'socks4', 'http', 'https'}:
                raise ValueError("TG_PROXY_TYPE must be one of: socks5, socks4, http, https.")
            if not self._proxy_host:
                raise ValueError("TG_PROXY_HOST is required when proxy is set.")
            if not self._proxy_port:
                raise ValueError("TG_PROXY_PORT is required when proxy is set.")
            try:
                proxy_port = int(self._proxy_port)
            except ValueError:
                raise ValueError("TG_PROXY_PORT must be an integer.")
            if not (1 <= proxy_port <= 65535):
                raise ValueError("TG_PROXY_PORT must be between 1 and 65535.")
            self._proxy_type = proxy_type
            self._proxy_port = proxy_port
            self._proxy_rdns = self._parse_proxy_rdns(self._proxy_rdns)

    @staticmethod
    def _parse_proxy_rdns(value: Optional[str]) -> bool:
        if value is None or str(value).strip() == "":
            return True
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError("TG_PROXY_RDNS must be a boolean (true/false).")

    @property
    def api_id(self) -> int:
        """Telegram API ID"""
        return int(self._api_id)
    
    @property
    def api_hash(self) -> str:
        """Telegram API Hash"""
        return self._api_hash
    
    @property
    def session_name(self) -> str:
        """会话名称"""
        return self._session_name
    
    @property
    def session_path(self) -> Path:
        """会话文件完整路径"""
        session_dir = Path(self._session_dir)
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"{self._session_name}.session"
    
    @property
    def proxy_type(self) -> Optional[str]:
        return self._proxy_type

    @property
    def proxy_host(self) -> Optional[str]:
        return self._proxy_host

    @property
    def proxy_port(self) -> Optional[int]:
        return self._proxy_port

    @property
    def proxy_username(self) -> Optional[str]:
        return self._proxy_username

    @property
    def proxy_password(self) -> Optional[str]:
        return self._proxy_password

    @property
    def proxy_rdns(self) -> Optional[bool]:
        return self._proxy_rdns

    @property
    def max_unread_fetch(self) -> int:
        return self._max_unread_fetch

    def __repr__(self) -> str:
        return (
            f"Config(api_id={self.api_id}, "
            f"session_name={self.session_name}, "
            f"session_path={self.session_path})"
        )


# 创建默认配置实例
default_config = None

def get_config(env_file: Optional[str] = None) -> Config:
    """
    获取配置实例(单例模式)
    
    Args:
        env_file: .env 文件路径
        
    Returns:
        Config 实例
    """
    global default_config
    if default_config is None:
        default_config = Config(env_file)
    return default_config
