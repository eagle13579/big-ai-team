"""
缓存策略演示示例
"""

import time

from src.access.adapters.cache_manager import cache_manager
from src.shared.logging import logger


def demo_basic_cache_operations():
    """
    演示基本缓存操作
    """
    logger.info("=== 演示基本缓存操作 ===")
    
    # 设置缓存
    cache_manager.set("tool", "test_value", 60, "test_tool", user_id="123")
    logger.info("设置缓存成功")
    
    # 获取缓存
    value = cache_manager.get("tool", "test_tool", user_id="123")
    logger.info(f"获取缓存值: {value}")
    
    # 再次获取（应该从本地缓存获取）
    value2 = cache_manager.get("tool", "test_tool", user_id="123")
    logger.info(f"再次获取缓存值: {value2}")
    
    # 删除缓存
    cache_manager.delete("tool", "test_tool", user_id="123")
    logger.info("删除缓存成功")
    
    # 验证缓存已删除
    value3 = cache_manager.get("tool", "test_tool", user_id="123")
    logger.info(f"删除后获取缓存值: {value3}")


def demo_cache_decorator():
    """
    演示缓存装饰器
    """
    logger.info("\n=== 演示缓存装饰器 ===")
    
    @cache_manager.cache("api", ttl=30)
    def slow_function(a, b):
        """模拟耗时操作"""
        logger.info(f"执行耗时操作: {a} + {b}")
        time.sleep(1)  # 模拟耗时
        return a + b
    
    # 第一次调用（执行函数）
    start_time = time.time()
    result1 = slow_function(10, 20)
    end_time = time.time()
    logger.info(f"第一次调用结果: {result1}, 耗时: {end_time - start_time:.2f}秒")
    
    # 第二次调用（从缓存获取）
    start_time = time.time()
    result2 = slow_function(10, 20)
    end_time = time.time()
    logger.info(f"第二次调用结果: {result2}, 耗时: {end_time - start_time:.2f}秒")


def demo_cache_warmup():
    """
    演示缓存预热
    """
    logger.info("\n=== 演示缓存预热 ===")
    
    # 准备预热数据
    warmup_items = [
        {
            "category": "data",
            "value": {"id": 1, "name": "Item 1"},
            "ttl": 600,
            "args": ["item", 1],
            "kwargs": {}
        },
        {
            "category": "data",
            "value": {"id": 2, "name": "Item 2"},
            "ttl": 600,
            "args": ["item", 2],
            "kwargs": {}
        },
        {
            "category": "model",
            "value": {"model_id": "gpt-4", "version": "1.0"},
            "ttl": 3600,
            "args": ["model_config"],
            "kwargs": {"model": "gpt-4"}
        }
    ]
    
    # 执行预热
    success_count = cache_manager.cache_warmup(warmup_items)
    logger.info(f"缓存预热完成，成功预热 {success_count} 个项目")
    
    # 验证预热结果
    for item in warmup_items:
        category = item["category"]
        args = item["args"]
        kwargs = item["kwargs"]
        value = cache_manager.get(category, *args, **kwargs)
        logger.info(f"验证预热缓存: {category}:{args} = {value}")


def demo_cache_stats():
    """
    演示缓存统计信息
    """
    logger.info("\n=== 演示缓存统计信息 ===")
    
    stats = cache_manager.get_stats()
    logger.info(f"缓存统计信息: {stats}")


def demo_cache_invalidation():
    """
    演示缓存失效策略
    """
    logger.info("\n=== 演示缓存失效策略 ===")
    
    # 设置多个缓存
    for i in range(5):
        cache_manager.set("test", f"value_{i}", 60, f"key_{i}")
    
    logger.info("设置了 5 个测试缓存")
    
    # 删除整个类别
    deleted_count = cache_manager.delete_category("test")
    logger.info(f"删除了 {deleted_count} 个缓存")
    
    # 验证删除结果
    for i in range(5):
        value = cache_manager.get("test", f"key_{i}")
        logger.info(f"验证删除结果: key_{i} = {value}")


if __name__ == "__main__":
    logger.info("开始缓存策略演示")
    
    try:
        demo_basic_cache_operations()
        demo_cache_decorator()
        demo_cache_warmup()
        demo_cache_stats()
        demo_cache_invalidation()
        
        logger.info("缓存策略演示完成")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
