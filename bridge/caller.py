#!/usr/bin/env python3
"""
MemPalace 调用入口
作为用户与核心逻辑之间的桥梁
最佳实践：
1. 动态加载：支持加载编译后的二进制模块或源码模块
2. 智能路径：自动检测核心模块的位置
3. 错误处理：提供详细的错误信息和解决方案
4. 版本兼容：支持不同版本的核心模块
5. 性能优化：缓存核心模块实例，减少重复加载
"""

import importlib.util
import os
import sys
import traceback
from typing import List, Dict, Any, Optional, Tuple, Set, Union


class MemPalaceCaller:
    """
    MemPalace 调用入口类
    动态加载核心模块，提供与原接口相同的方法
    """
    
    # 类变量，用于缓存核心模块实例
    _core_module_cache = None
    _core_instance_cache = None
    
    def __init__(self, palace_path: str = "~/.mempalace/palace"):
        self.palace_path = os.path.expanduser(palace_path)
        self._core_module = None
        self._core_instance = None
        self._load_core_module()
        self._initialize_core(palace_path)
    
    def _load_core_module(self):
        """动态加载核心模块"""
        try:
            # 检查缓存
            if MemPalaceCaller._core_module_cache is not None:
                self._core_module = MemPalaceCaller._core_module_cache
                print("✅ 从缓存加载核心模块")
                return
            
            # 尝试加载编译后的二进制模块
            core_path = os.path.join(os.path.dirname(__file__), "..", "core")
            project_root = os.path.dirname(core_path)
            
            # 添加项目根目录到路径
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 首先尝试从 core 包导入
            try:
                import core as core_module
                self._core_module = core_module
                print("✅ 加载编译后的核心模块成功")
            except ImportError as e1:
                # 如果 core 包导入失败，尝试直接导入 core
                try:
                    # 添加 core 目录到路径
                    if core_path not in sys.path:
                        sys.path.insert(0, core_path)
                    import core as core_module
                    self._core_module = core_module
                    print("✅ 加载源码核心模块成功")
                except ImportError as e2:
                    # 如果源码模块也不存在，尝试直接加载文件
                    core_file = os.path.join(core_path, "mempalace_core.py")
                    if os.path.exists(core_file):
                        spec = importlib.util.spec_from_file_location("core", core_file)
                        core_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(core_module)
                        self._core_module = core_module
                        print("✅ 直接加载核心模块文件成功")
                    else:
                        # 尝试从 dist/core 目录加载
                        dist_core_path = os.path.join(project_root, "dist", "core")
                        if os.path.exists(dist_core_path):
                            if dist_core_path not in sys.path:
                                sys.path.insert(0, os.path.join(project_root, "dist"))
                            try:
                                import core as core_module
                                self._core_module = core_module
                                print("✅ 从 dist/core 加载核心模块成功")
                            except ImportError as e3:
                                raise ImportError(f"无法找到核心模块文件，尝试了以下位置:\n" 
                                               f"1. {core_path}/mempalace_core.py\n" 
                                               f"2. {dist_core_path}/core.*")
                        else:
                            raise ImportError(f"无法找到核心模块文件，尝试了以下位置:\n" 
                                           f"1. {core_path}/mempalace_core.py\n" 
                                           f"2. {dist_core_path}/core.*")
        except Exception as e:
            print(f"❌ 加载核心模块失败: {str(e)}")
            print("💡 提示：请确保核心模块已正确构建，或运行 python build_protect.py 生成二进制模块")
            traceback.print_exc()
            raise
        
        # 缓存核心模块
        MemPalaceCaller._core_module_cache = self._core_module
    
    def _initialize_core(self, palace_path: str):
        """初始化核心模块"""
        if self._core_module:
            try:
                # 检查缓存
                if MemPalaceCaller._core_instance_cache is not None:
                    self._core_instance = MemPalaceCaller._core_instance_cache
                    print("✅ 从缓存加载核心实例")
                else:
                    # 尝试初始化所有可能的核心类
                    core_classes = [
                        'MemPalaceIntegrationV2',
                        'MemPalaceIntegration',
                        'MemPalaceCore',
                        'MemoryPalace'
                    ]
                    
                    initialized = False
                    for class_name in core_classes:
                        if hasattr(self._core_module, class_name):
                            try:
                                self._core_instance = getattr(self._core_module, class_name)(palace_path)
                                print(f"✅ 初始化 {class_name} 成功")
                                initialized = True
                                break
                            except Exception as e:
                                print(f"⚠️ 初始化 {class_name} 失败: {e}")
                    
                    if not initialized:
                        # 尝试直接从 mempalace_core 模块导入
                        try:
                            from core import mempalace_core
                            for class_name in core_classes:
                                if hasattr(mempalace_core, class_name):
                                    try:
                                        self._core_instance = getattr(mempalace_core, class_name)(palace_path)
                                        print(f"✅ 从 mempalace_core 初始化 {class_name} 成功")
                                        initialized = True
                                        break
                                    except Exception as e:
                                        print(f"⚠️ 从 mempalace_core 初始化 {class_name} 失败: {e}")
                        except ImportError:
                            print("⚠️ 无法导入 mempalace_core 模块")
                    
                    if not initialized:
                        raise RuntimeError("无法找到核心模块的初始化类")
                
                # 缓存核心实例
                MemPalaceCaller._core_instance_cache = self._core_instance
            except Exception as e:
                print(f"❌ 初始化核心模块失败: {str(e)}")
                raise
        else:
            raise RuntimeError("核心模块未加载，无法初始化")
    
    def add_memory(self, content: Union[str, Dict[str, Any]], 
                   context: Dict[str, Any] = None, 
                   tags: List[str] = None) -> Dict[str, Any]:
        """添加记忆"""
        try:
            return self._core_instance.add_memory(content, context, tags)
        except Exception as e:
            print(f"❌ 添加记忆失败: {str(e)}")
            raise
    
    def search(self, query: str, limit: int = 5, 
               context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索记忆"""
        try:
            return self._core_instance.search(query, limit, context)
        except Exception as e:
            print(f"❌ 搜索记忆失败: {str(e)}")
            raise
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        try:
            return self._core_instance.get_memory_stats()
        except Exception as e:
            print(f"❌ 获取记忆统计失败: {str(e)}")
            raise
    
    def cleanup_duplicates(self) -> Dict[str, Any]:
        """清理重复记忆"""
        try:
            return self._core_instance.cleanup_duplicates()
        except Exception as e:
            print(f"❌ 清理重复记忆失败: {str(e)}")
            raise
    
    def compress(self, content: str, memory_tier = None) -> str:
        """压缩内容"""
        try:
            if memory_tier is None:
                # 如果没有提供记忆分层，使用默认值
                try:
                    from core.mempalace_core import MemoryTier
                    memory_tier = MemoryTier.SHORT_TERM
                except ImportError:
                    # 尝试从已加载的模块获取
                    if hasattr(self._core_module, 'MemoryTier'):
                        memory_tier = self._core_module.MemoryTier.SHORT_TERM
                    else:
                        raise ImportError("无法找到 MemoryTier 类")
            return self._core_instance.compress(content, memory_tier)
        except Exception as e:
            print(f"❌ 压缩内容失败: {str(e)}")
            raise
    
    def get_wake_up_context(self, context: Dict[str, Any] = None) -> str:
        """获取唤醒上下文"""
        try:
            # 这个方法在 V2 中可能不存在，需要检查
            if hasattr(self._core_instance, 'get_wake_up_context'):
                return self._core_instance.get_wake_up_context(context)
            return ""
        except Exception as e:
            print(f"❌ 获取唤醒上下文失败: {str(e)}")
            return ""
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        try:
            # 这个方法在 V2 中可能不存在，需要检查
            if hasattr(self._core_instance, 'get_memory_summary'):
                return self._core_instance.get_memory_summary()
            return {}
        except Exception as e:
            print(f"❌ 获取记忆摘要失败: {str(e)}")
            return {}
    
    def get_core_version(self) -> str:
        """获取核心模块版本"""
        try:
            if hasattr(self._core_module, '__version__'):
                return self._core_module.__version__
            return "未知版本"
        except Exception:
            return "无法获取版本"


# 向后兼容
MemPalaceIntegration = MemPalaceCaller


if __name__ == "__main__":
    # 测试调用
    try:
        caller = MemPalaceCaller()
        print("🎉 MemPalace 调用器初始化成功")
        print(f"📦 核心模块版本: {caller.get_core_version()}")
        
        # 测试添加记忆
        print("\n🧪 测试添加记忆...")
        result = caller.add_memory(
            "测试记忆内容",
            context={"importance": "high", "project": "test"},
            tags=["test", "example"]
        )
        print(f"✅ 添加记忆结果: {result}")
        
        # 测试搜索
        print("\n🧪 测试搜索记忆...")
        search_results = caller.search("测试")
        print(f"✅ 搜索结果: {search_results}")
        
        # 测试统计
        print("\n🧪 测试获取统计信息...")
        stats = caller.get_memory_stats()
        print(f"✅ 记忆统计: {stats}")
        
        # 测试清理重复记忆
        print("\n🧪 测试清理重复记忆...")
        cleanup_result = caller.cleanup_duplicates()
        print(f"✅ 清理结果: {cleanup_result}")
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()
