#!/usr/bin/env python3
"""
MemPalace 调用入口
作为用户与核心逻辑之间的桥梁
"""

import importlib.util
import os
import sys
from typing import List, Dict, Any, Optional, Tuple, Set, Union


class MemPalaceCaller:
    """
    MemPalace 调用入口类
    动态加载核心模块，提供与原接口相同的方法
    """
    
    def __init__(self, palace_path: str = "~/.mempalace/palace"):
        self.palace_path = os.path.expanduser(palace_path)
        self._core_module = None
        self._load_core_module()
        self._initialize_core(palace_path)
    
    def _load_core_module(self):
        """动态加载核心模块"""
        try:
            # 尝试加载编译后的二进制模块
            core_path = os.path.join(os.path.dirname(__file__), "..", "core")
            sys.path.insert(0, os.path.dirname(core_path))  # 添加项目根目录到路径
            
            # 首先尝试从 core 包导入
            try:
                from core import mempalace_core as core_module
                self._core_module = core_module
                print("加载编译后的核心模块成功")
            except ImportError:
                # 如果 core 包导入失败，尝试直接导入 mempalace_core
                try:
                    import mempalace_core as core_module
                    self._core_module = core_module
                    print("加载源码核心模块成功")
                except ImportError:
                    # 如果源码模块也不存在，尝试直接加载文件
                    core_file = os.path.join(core_path, "mempalace_core.py")
                    if os.path.exists(core_file):
                        spec = importlib.util.spec_from_file_location("mempalace_core", core_file)
                        core_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(core_module)
                        self._core_module = core_module
                        print("直接加载核心模块文件成功")
                    else:
                        raise ImportError("无法找到核心模块文件")
        except Exception as e:
            print(f"加载核心模块失败: {str(e)}")
            raise
    
    def _initialize_core(self, palace_path: str):
        """初始化核心模块"""
        if self._core_module:
            self._core_instance = self._core_module.MemPalaceIntegrationV2(palace_path)
        else:
            raise RuntimeError("核心模块未加载，无法初始化")
    
    def add_memory(self, content: Union[str, Dict[str, Any]], 
                   context: Dict[str, Any] = None, 
                   tags: List[str] = None) -> Dict[str, Any]:
        """添加记忆"""
        return self._core_instance.add_memory(content, context, tags)
    
    def search(self, query: str, limit: int = 5, 
               context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索记忆"""
        return self._core_instance.search(query, limit, context)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return self._core_instance.get_memory_stats()
    
    def cleanup_duplicates(self) -> Dict[str, Any]:
        """清理重复记忆"""
        return self._core_instance.cleanup_duplicates()
    
    def compress(self, content: str, memory_tier = None) -> str:
        """压缩内容"""
        if memory_tier is None:
            # 如果没有提供记忆分层，使用默认值
            from core.mempalace_core import MemoryTier
            memory_tier = MemoryTier.SHORT_TERM
        return self._core_instance.compress(content, memory_tier)
    
    def get_wake_up_context(self, context: Dict[str, Any] = None) -> str:
        """获取唤醒上下文"""
        # 这个方法在 V2 中可能不存在，需要检查
        if hasattr(self._core_instance, 'get_wake_up_context'):
            return self._core_instance.get_wake_up_context(context)
        return ""
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        # 这个方法在 V2 中可能不存在，需要检查
        if hasattr(self._core_instance, 'get_memory_summary'):
            return self._core_instance.get_memory_summary()
        return {}


# 向后兼容
MemPalaceIntegration = MemPalaceCaller


if __name__ == "__main__":
    # 测试调用
    try:
        caller = MemPalaceCaller()
        print("MemPalace 调用器初始化成功")
        
        # 测试添加记忆
        result = caller.add_memory(
            "测试记忆内容",
            context={"importance": "high", "project": "test"},
            tags=["test", "example"]
        )
        print(f"添加记忆结果: {result}")
        
        # 测试搜索
        search_results = caller.search("测试")
        print(f"搜索结果: {search_results}")
        
        # 测试统计
        stats = caller.get_memory_stats()
        print(f"记忆统计: {stats}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
