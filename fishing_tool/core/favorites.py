"""
收藏管理器模块
负责收藏对话的持久化和查询
"""
import json
from pathlib import Path
from typing import List, Optional

from ..models import DialogInfo


class FavoritesManager:
    """收藏管理器"""
    
    def __init__(self, favorites_path: Path):
        """
        初始化收藏管理器
        
        Args:
            favorites_path: 收藏文件路径
        """
        self.favorites_path = favorites_path
        self.favorites: List[DialogInfo] = []
        self._load()
    
    def _load(self):
        """从文件加载收藏"""
        if not self.favorites_path.exists():
            self.favorites = []
            return
        
        try:
            data = json.loads(self.favorites_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"收藏文件解析失败: {e}")
        
        if not isinstance(data, list):
            raise ValueError("收藏文件格式错误: 需要列表")
        
        favorites = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("收藏文件格式错误: 列表元素必须为对象")
            
            dialog_id = item.get("dialog_id")
            name = item.get("name")
            username = item.get("username")
            
            if not isinstance(dialog_id, int):
                raise ValueError("收藏文件格式错误: dialog_id 必须为整数")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("收藏文件格式错误: name 必须为非空字符串")
            if username is not None and not isinstance(username, str):
                raise ValueError("收藏文件格式错误: username 必须为字符串或 null")
            
            favorites.append(DialogInfo(
                dialog_id=dialog_id,
                name=name,
                username=username
            ))
        
        self.favorites = favorites
    
    def _save(self):
        """保存收藏到文件"""
        data = [fav.to_dict() for fav in self.favorites]
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.favorites_path.write_text(json_data, encoding="utf-8")
    
    def get_all(self) -> List[DialogInfo]:
        """获取所有收藏"""
        return self.favorites.copy()
    
    def find_by_id(self, dialog_id: int) -> Optional[int]:
        """
        通过对话ID查找收藏的索引
        
        Returns:
            索引位置,如果不存在返回 None
        """
        for i, fav in enumerate(self.favorites):
            if fav.dialog_id == dialog_id:
                return i
        return None
    
    def find_by_identifier(self, identifier: str) -> List[int]:
        """
        通过标识符查找收藏的索引
        
        Args:
            identifier: 对话名称、用户名或ID
            
        Returns:
            匹配的索引列表
        """
        identifier_str = identifier.strip()
        if identifier_str.startswith("@"):
            identifier_str = identifier_str[1:]
        identifier_str = identifier_str.lower()
        
        matches = []
        for i, fav in enumerate(self.favorites):
            # 匹配ID
            if str(fav.dialog_id) == identifier_str:
                matches.append(i)
                continue
            # 匹配名称
            if fav.name and fav.name.lower() == identifier_str:
                matches.append(i)
                continue
            # 匹配用户名
            if fav.username and fav.username.lower() == identifier_str:
                matches.append(i)
        
        return matches
    
    def add_or_update(self, dialog_info: DialogInfo) -> bool:
        """
        添加或更新收藏
        
        Returns:
            True 表示新增, False 表示更新
        """
        index = self.find_by_id(dialog_info.dialog_id)
        if index is None:
            self.favorites.append(dialog_info)
            self._save()
            return True
        else:
            self.favorites[index] = dialog_info
            self._save()
            return False
    
    def remove_by_index(self, index: int) -> DialogInfo:
        """
        通过索引移除收藏
        
        Returns:
            被移除的对话信息
        """
        removed = self.favorites.pop(index)
        self._save()
        return removed
    
    def remove_by_id(self, dialog_id: int) -> Optional[DialogInfo]:
        """
        通过对话ID移除收藏
        
        Returns:
            被移除的对话信息,如果不存在返回 None
        """
        index = self.find_by_id(dialog_id)
        if index is None:
            return None
        return self.remove_by_index(index)

