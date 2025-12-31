"""
消息状态追踪器
用于追踪每个对话的消息读取状态,防止消息遗漏
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MessageTracker:
    """消息状态追踪器"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化消息追踪器
        
        Args:
            db_path: 数据库文件路径,默认在用户目录下
        """
        if db_path is None:
            db_path = Path.home() / ".tgmessage" / "message_tracker.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 对话状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialog_state (
                    dialog_id INTEGER PRIMARY KEY,
                    last_read_message_id INTEGER NOT NULL,
                    last_read_time TIMESTAMP NOT NULL,
                    last_sent_message_id INTEGER,
                    last_sent_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 发送历史表(用于追踪发送操作)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS send_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dialog_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    prev_read_message_id INTEGER,
                    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dialog_id) REFERENCES dialog_state(dialog_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_send_history_dialog 
                ON send_history(dialog_id, sent_time DESC)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接(上下文管理器)"""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_last_read_message_id(self, dialog_id: int) -> Optional[int]:
        """
        获取对话的最后已读消息ID
        
        Args:
            dialog_id: 对话ID
            
        Returns:
            最后已读消息ID,如果没有记录返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_read_message_id FROM dialog_state WHERE dialog_id = ?",
                (dialog_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def update_last_read_message_id(
        self,
        dialog_id: int,
        message_id: int,
        force: bool = False
    ) -> None:
        """
        更新对话的最后已读消息ID
        
        Args:
            dialog_id: 对话ID
            message_id: 消息ID
            force: 是否强制更新(即使新ID小于旧ID)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                "SELECT last_read_message_id FROM dialog_state WHERE dialog_id = ?",
                (dialog_id,)
            )
            row = cursor.fetchone()
            
            now = datetime.now()
            
            if row is None:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO dialog_state 
                    (dialog_id, last_read_message_id, last_read_time, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (dialog_id, message_id, now, now))
                logger.debug(f"对话 {dialog_id}: 初始化最后已读消息ID为 {message_id}")
            else:
                # 更新现有记录(只在新ID更大或强制更新时)
                old_id = row[0]
                if force or message_id > old_id:
                    cursor.execute("""
                        UPDATE dialog_state 
                        SET last_read_message_id = ?,
                            last_read_time = ?,
                            updated_at = ?
                        WHERE dialog_id = ?
                    """, (message_id, now, now, dialog_id))
                    logger.debug(
                        f"对话 {dialog_id}: 更新最后已读消息ID "
                        f"{old_id} -> {message_id}"
                    )
            
            conn.commit()
    
    def record_sent_message(
        self,
        dialog_id: int,
        message_id: int
    ) -> Optional[int]:
        """
        记录发送的消息
        
        Args:
            dialog_id: 对话ID
            message_id: 发送的消息ID
            
        Returns:
            发送前的最后已读消息ID(用于获取中间消息)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取当前的最后已读消息ID
            prev_read_id = self.get_last_read_message_id(dialog_id)
            
            # 记录发送历史
            cursor.execute("""
                INSERT INTO send_history 
                (dialog_id, message_id, prev_read_message_id)
                VALUES (?, ?, ?)
            """, (dialog_id, message_id, prev_read_id))
            
            # 更新对话状态
            now = datetime.now()
            cursor.execute("""
                UPDATE dialog_state 
                SET last_sent_message_id = ?,
                    last_sent_time = ?,
                    updated_at = ?
                WHERE dialog_id = ?
            """, (message_id, now, now, dialog_id))
            
            # 如果对话状态不存在,创建它
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO dialog_state 
                    (dialog_id, last_read_message_id, last_read_time,
                     last_sent_message_id, last_sent_time, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (dialog_id, message_id, now, message_id, now, now))
            
            conn.commit()
            
            logger.info(
                f"对话 {dialog_id}: 记录发送消息 {message_id}, "
                f"上次已读ID: {prev_read_id}"
            )
            
            return prev_read_id
    
    def get_dialog_state(self, dialog_id: int) -> Optional[Dict[str, Any]]:
        """
        获取对话的完整状态信息
        
        Args:
            dialog_id: 对话ID
            
        Returns:
            对话状态字典,如果不存在返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dialog_state WHERE dialog_id = ?",
                (dialog_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def clear_dialog_state(self, dialog_id: int) -> None:
        """
        清除对话的追踪状态
        
        Args:
            dialog_id: 对话ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM send_history WHERE dialog_id = ?", (dialog_id,))
            cursor.execute("DELETE FROM dialog_state WHERE dialog_id = ?", (dialog_id,))
            conn.commit()
            logger.info(f"对话 {dialog_id}: 已清除追踪状态")
    
    def get_all_tracked_dialogs(self) -> List[int]:
        """
        获取所有被追踪的对话ID列表

        Returns:
            对话ID列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dialog_id FROM dialog_state ORDER BY updated_at DESC")
            return [row[0] for row in cursor.fetchall()]

    def get_message_range_info(
        self,
        dialog_id: int
    ) -> Optional[Dict[str, Optional[int]]]:
        """
        获取需要补偿获取的消息范围信息

        Args:
            dialog_id: 对话ID

        Returns:
            包含 min_id 和 max_id 的字典,用于获取这个范围内的消息
            如果不需要补偿,返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 获取最后一次发送操作
            cursor.execute("""
                SELECT message_id, prev_read_message_id, sent_time
                FROM send_history
                WHERE dialog_id = ?
                ORDER BY sent_time DESC
                LIMIT 1
            """, (dialog_id,))

            send_row = cursor.fetchone()
            if not send_row:
                return None

            sent_msg_id = send_row[0]
            prev_read_id = send_row[1]

            # 如果没有之前的已读记录,返回 None
            if prev_read_id is None:
                return None

            # 返回需要获取的消息范围
            return {
                'min_id': prev_read_id,
                'max_id': sent_msg_id
            }

