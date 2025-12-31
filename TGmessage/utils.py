"""
工具函数模块
提供辅助功能和装饰器
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, Union
from datetime import datetime

from telethon import errors


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步函数重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间的递增倍数
        exceptions: 需要捕获的异常类型元组
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} 失败,已达到最大重试次数 {max_attempts}: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次尝试失败: {e}, "
                        f"{current_delay:.1f}秒后重试..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def handle_flood_wait(func: Callable) -> Callable:
    """
    处理 Telegram FloodWaitError 的装饰器
    自动等待指定的时间后重试
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except errors.FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(
                    f"遭遇 FloodWaitError,需要等待 {wait_time} 秒后重试..."
                )
                await asyncio.sleep(wait_time)
            except errors.FloodError as e:
                # 通用的 Flood 错误,等待固定时间
                wait_time = 60
                logger.warning(
                    f"遭遇 FloodError: {e},等待 {wait_time} 秒后重试..."
                )
                await asyncio.sleep(wait_time)
    
    return wrapper


def format_timestamp(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化时间戳
    
    Args:
        dt: datetime 对象
        fmt: 格式化字符串
        
    Returns:
        格式化后的时间字符串
    """
    if dt is None:
        return "N/A"
    return dt.strftime(fmt)


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
        
    Returns:
        截断后的文本
    """
    if text is None:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


async def find_dialog(client, identifier: Union[int, str]):
    if identifier is None:
        return None

    if isinstance(identifier, int):
        try:
            await client.get_entity(identifier)
            dialogs = await client.get_dialogs()
            for dialog in dialogs:
                if dialog.id == identifier:
                    return dialog
        except Exception as e:
            logger.warning("通过 ID %s 查找对话失败: %s", identifier, e)
            return None

    identifier_str = str(identifier).strip()
    if not identifier_str:
        return None

    if identifier_str.startswith('@'):
        identifier_str = identifier_str[1:]

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        username = getattr(entity, 'username', None)
        if username and username.lower() == identifier_str.lower():
            return dialog

        name = dialog.name
        if name and name.lower() == identifier_str.lower():
            return dialog

    return None


def get_media_type(message) -> Optional[str]:
    """
    获取消息的媒体类型
    
    Args:
        message: Telethon Message 对象
        
    Returns:
        媒体类型字符串,如 'photo', 'video', 'document' 等
    """
    if not message.media:
        return None
    
    media_class_name = message.media.__class__.__name__
    
    # 映射 Telegram 媒体类型到友好名称
    media_type_mapping = {
        'MessageMediaPhoto': 'photo',
        'MessageMediaDocument': 'document',
        'MessageMediaContact': 'contact',
        'MessageMediaGeo': 'location',
        'MessageMediaVenue': 'venue',
        'MessageMediaPoll': 'poll',
        'MessageMediaDice': 'dice',
        'MessageMediaWebPage': 'webpage',
        'MessageMediaGame': 'game',
        'MessageMediaInvoice': 'invoice',
        'MessageMediaGeoLive': 'live_location',
    }
    
    media_type = media_type_mapping.get(media_class_name, 'unknown')
    
    # 对于 document,进一步判断是否是视频、音频等
    if media_type == 'document' and hasattr(message.media, 'document'):
        mime_type = getattr(message.media.document, 'mime_type', '')
        if mime_type.startswith('video/'):
            media_type = 'video'
        elif mime_type.startswith('audio/'):
            media_type = 'audio'
        elif mime_type.startswith('image/'):
            media_type = 'image'
    
    return media_type
