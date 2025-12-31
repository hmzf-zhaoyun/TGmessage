"""
对话信息数据模型
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DialogInfo:
    """对话信息数据类"""
    
    dialog_id: int
    name: str
    username: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "dialog_id": self.dialog_id,
            "name": self.name,
            "username": self.username
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DialogInfo':
        """从字典创建"""
        return cls(
            dialog_id=data["dialog_id"],
            name=data["name"],
            username=data.get("username")
        )
    
    def format_info(self) -> str:
        """格式化对话信息"""
        username_part = f" (@{self.username})" if self.username else ""
        return f"{self.name}{username_part} [ID: {self.dialog_id}]"

