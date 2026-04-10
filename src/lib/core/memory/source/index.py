#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory management module
"""

from typing import Dict, Any, Optional


class MemoryManager:
    """内存管理器

    负责管理内存中的数据存储和检索。

    Attributes:
        memory_store: 内存数据存储字典
    """

    def __init__(self) -> None:
        """初始化内存管理器

        创建一个空的内存存储字典。
        """
        self.memory_store: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> bool:
        """存储内存数据

        将数据存储到内存中。

        Args:
            key: 存储键
            value: 存储值

        Returns:
            bool: 存储是否成功
        """
        self.memory_store[key] = value
        return True

    def retrieve(self, key: str) -> Optional[Any]:
        """检索内存数据

        从内存中检索数据。

        Args:
            key: 检索键

        Returns:
            Optional[Any]: 检索到的数据，若不存在则返回None
        """
        return self.memory_store.get(key)

    def delete(self, key: str) -> bool:
        """删除内存数据

        从内存中删除数据。

        Args:
            key: 要删除的键

        Returns:
            bool: 删除是否成功
        """
        if key in self.memory_store:
            del self.memory_store[key]
            return True
        return False

    def clear(self) -> bool:
        """清空所有内存数据

        清空内存中的所有数据。

        Returns:
            bool: 清空是否成功
        """
        self.memory_store.clear()
        return True

    def get_all(self) -> Dict[str, Any]:
        """获取所有内存数据

        获取内存中存储的所有数据的副本。

        Returns:
            Dict[str, Any]: 内存数据的副本
        """
        return self.memory_store.copy()
