#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory management module
"""
from typing import Dict, Any, Optional


class MemoryManager:
    """内存管理器"""
    
    def __init__(self):
        self.memory_store = {}
    
    def store(self, key: str, value: Any) -> bool:
        """存储内存数据"""
        self.memory_store[key] = value
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索内存数据"""
        return self.memory_store.get(key)
    
    def delete(self, key: str) -> bool:
        """删除内存数据"""
        if key in self.memory_store:
            del self.memory_store[key]
            return True
        return False
    
    def clear(self) -> bool:
        """清空所有内存数据"""
        self.memory_store.clear()
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有内存数据"""
        return self.memory_store.copy()
