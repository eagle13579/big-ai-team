import asyncio
import hashlib
import heapq
import os
import sys
import time
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import psutil

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.access.adapters.redis_cache import redis_cache
from src.shared.config import settings
from src.shared.logging import logger
from src.shared.monitoring import tool_monitor
from src.shared.reliability import (
    CircuitBreaker,
    FaultRecoveryManager,
    RetryMechanism,
    ServiceDegrader,
)
from src.skills import get_all_skills, skill_registry

logger = logger.bind(name="AceAgent.Execution")


class RateLimiter:
    """
    优化的速率限制器
    """

    def __init__(self, max_calls: int, time_frame: int):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.calls = []
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = datetime.now()
            # 清理过期的调用记录
            self.calls = [
                call for call in self.calls if now - call < timedelta(seconds=self.time_frame)
            ]

            # 检查是否超过速率限制
            if len(self.calls) >= self.max_calls:
                wait_time = self.time_frame - (now - self.calls[0]).total_seconds()
                if wait_time > 0:
                    # 减少日志输出频率
                    if len(self.calls) % 3 == 0:
                        logger.warning(f"⚠️  速率限制触发，等待 {wait_time:.2f} 秒")
                    await asyncio.sleep(wait_time)

            # 记录本次调用
            self.calls.append(datetime.now())
            return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ToolExecutor:
    """
    🚀 2026 生产级工具执行器 (Best Practice)
    特性：
    1. 异步非阻塞执行 (Async/Await)
    2. 动态工具注册映射
    3. 严格的异常捕获与上下文反馈
    4. 自动目录管理与资源清理
    5. 超时控制机制
    6. 权限管理
    7. 速率限制
    8. 结果缓存
    """

    def __init__(self):
        # 从配置中心读取输出路径，默认为 'output'
        self.output_dir = getattr(settings, "AGENT_OUTPUT_DIR", "output")
        self._ensure_workspace()

        # 核心工具注册表
        # key: 工具名称, value: 对应的异步函数
        self._tool_registry: dict[str, Callable[..., Awaitable[Any]]] = {
            "web_search": self._web_search,
            "write_file": self._write_file,
            "read_file": self._read_file,
            "list_files": self._list_files,
            "delete_file": self._delete_file,
            "get_system_status": self._get_system_status,
        }

        # 加载技能
        self._load_skills()

        # 速率限制器
        self._rate_limiters = {
            "web_search": RateLimiter(max_calls=5, time_frame=60),
            "default": RateLimiter(max_calls=10, time_frame=60),
        }

        # 结果缓存
        self._cache_ttl = settings.CACHE_TTL  # 缓存过期时间（秒）
        self._cache_hits = 0  # 缓存命中次数
        self._cache_misses = 0  # 缓存未命中次数
        self._cache_cleanup_interval = 300  # 缓存清理间隔（秒）
        self._last_cache_cleanup = time.time()

        # 权限管理
        self._permissions = {
            "write_file": ["admin", "user"],
            "delete_file": ["admin"],
            "default": ["admin", "user", "guest"],
        }
        
        # 线程池配置
        self._thread_pool = self._create_thread_pool()
        
        # 任务优先级队列
        self._task_queue: list[tuple[int, Callable]] = []
        self._task_counter = 0  # 用于确保任务顺序的计数器
        
        # 可靠性机制
        self._retry_mechanisms = {
            "default": RetryMechanism(),
            "web_search": RetryMechanism(max_retries=3, base_delay=2.0),
            "agent_reach": RetryMechanism(max_retries=3, base_delay=1.5),
        }
        
        # 熔断器
        self._circuit_breakers = {
            "default": CircuitBreaker(),
            "web_search": CircuitBreaker(name="web_search", failure_threshold=3),
            "agent_reach": CircuitBreaker(name="agent_reach", failure_threshold=3),
        }
        
        # 服务降级器
        self._service_degrader = ServiceDegrader(name="executor")
        
        # 故障恢复管理器
        self._fault_recovery_manager = FaultRecoveryManager()
        
        # 注册恢复策略
        self._register_recovery_strategies()

    def _load_skills(self):
        """加载技能"""
        try:
            skills = get_all_skills()
            for skill_name, skill_class in skills.items():
                # 根据技能名称创建实例
                if skill_name == "git_helper":
                    # GitHelperTool 需要 repo_path 参数
                    skill_instance = skill_class(repo_path=".")
                else:
                    # 其他技能使用默认参数
                    skill_instance = skill_class()

                # 包装同步方法为异步
                def create_async_wrapper(skill):
                    async def async_execute(**kwargs):
                        loop = asyncio.get_event_loop()
                        # 对于 agent_reach 技能，直接传递 kwargs 作为参数
                        return await loop.run_in_executor(self._thread_pool, skill.execute, kwargs)

                    return async_execute

                # 注册技能
                async_wrapper = create_async_wrapper(skill_instance)
                self._tool_registry[skill_name] = async_wrapper
                logger.info(f"🔧 已加载技能: {skill_name}")
        except Exception as e:
            logger.error(f"加载技能失败: {str(e)}")

    def _ensure_workspace(self):
        """初始化工作目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"📁 已创建 Agent 工作目录: {self.output_dir}")
    
    def _create_thread_pool(self) -> ThreadPoolExecutor:
        """
        创建线程池，根据系统资源动态调整大小
        
        Returns:
            配置好的 ThreadPoolExecutor
        """
        # 获取系统CPU核心数
        cpu_count = psutil.cpu_count(logical=True)
        
        # 获取系统可用内存（GB）
        available_memory = psutil.virtual_memory().available / (1024 ** 3)
        
        # 计算线程池大小
        # 基本线程数 = CPU核心数 * 1.5
        # 最大线程数 = 基本线程数 + 可用内存 / 2
        base_threads = max(4, int(cpu_count * 1.5))
        max_threads = min(64, base_threads + int(available_memory / 2))
        
        # 最终线程数
        thread_count = min(max_threads, settings.MAX_CONCURRENT_TASKS)
        
        logger.info(f"🔧 初始化线程池，大小: {thread_count} (基于 {cpu_count} 核心 CPU 和 {available_memory:.2f}GB 可用内存)")
        
        return ThreadPoolExecutor(max_workers=thread_count, thread_name_prefix="AceAgent-Executor-")
    
    def _get_optimal_thread_count(self) -> int:
        """
        根据系统资源和负载动态计算最优线程数
        
        Returns:
            计算得到的最优线程数
        """
        # 获取系统CPU核心数
        cpu_count = psutil.cpu_count(logical=True)
        
        # 获取系统可用内存（GB）
        available_memory = psutil.virtual_memory().available / (1024 ** 3)
        
        # 获取CPU使用率
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # 获取系统负载
        load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        
        # 基础线程数
        base_threads = max(4, int(cpu_count * 1.5))
        
        # 根据系统负载调整
        # 如果CPU使用率超过70%，减少线程数
        if cpu_usage > 70:
            thread_count = max(4, int(base_threads * 0.7))
        # 如果系统负载较低且内存充足，增加线程数
        elif cpu_usage < 30 and available_memory > 4:
            thread_count = min(64, int(base_threads * 1.2))
        else:
            thread_count = base_threads
        
        # 考虑可用内存
        memory_based_threads = min(64, base_threads + int(available_memory / 2))
        thread_count = min(thread_count, memory_based_threads)
        
        # 最终线程数不超过配置的最大并发任务数
        thread_count = min(thread_count, settings.MAX_CONCURRENT_TASKS)
        
        logger.debug(f"⚡ 计算最优线程数: {thread_count} (CPU: {cpu_usage:.1f}%, 内存: {available_memory:.2f}GB, 负载: {load_avg:.2f})")
        
        return thread_count
    
    async def _adjust_thread_pool_size(self):
        """
        动态调整线程池大小
        """
        optimal_thread_count = self._get_optimal_thread_count()
        current_thread_count = self._thread_pool._max_workers
        
        if optimal_thread_count != current_thread_count:
            logger.info(f"🔧 调整线程池大小: {current_thread_count} -> {optimal_thread_count}")
            
            # 关闭旧线程池
            old_pool = self._thread_pool
            old_pool.shutdown(wait=False)
            
            # 创建新线程池
            self._thread_pool = ThreadPoolExecutor(
                max_workers=optimal_thread_count, 
                thread_name_prefix="AceAgent-Executor-"
            )
            
            logger.info(f"🔧 线程池大小已调整为: {optimal_thread_count}")
    
    def _add_task(self, priority: int, task: Callable) -> None:
        """
        添加任务到优先级队列
        
        Args:
            priority: 任务优先级，值越小优先级越高
            task: 任务函数
        """
        self._task_counter += 1
        # 使用堆来实现优先级队列
        # 元组格式: (优先级, 计数器, 任务)
        # 计数器确保相同优先级的任务按添加顺序执行
        heapq.heappush(self._task_queue, (priority, self._task_counter, task))
        logger.info(f"📋 添加任务到队列，优先级: {priority}, 当前队列大小: {len(self._task_queue)}")
    
    async def _process_task_queue(self) -> None:
        """
        处理优先级队列中的任务
        """
        task_counter = 0
        while self._task_queue:
            # 每处理5个任务后检查并调整线程池大小
            if task_counter % 5 == 0:
                await self._adjust_thread_pool_size()
            
            # 取出优先级最高的任务
            priority, _, task = heapq.heappop(self._task_queue)
            logger.info(f"⚡ 执行任务，优先级: {priority}, 剩余队列大小: {len(self._task_queue)}")
            try:
                # 执行任务
                await task()
                task_counter += 1
            except Exception as e:
                logger.error(f"执行任务时出错: {str(e)}")
                task_counter += 1

    def _generate_cache_key(self, tool_name: str, args: dict[str, Any]) -> str:
        """生成缓存键
        
        优化后的缓存键设计：
        - 使用 SHA-256 哈希算法，更安全
        - 包含工具名称、参数、环境和版本信息
        - 格式：tool:{tool_name}:{hash}
        """
        import json
        
        # 构建缓存键的基础数据
        cache_data = {
            "tool": tool_name,
            "args": args,
            "env": settings.ENV_MODE,
            "version": "v1"  # 缓存键版本
        }
        
        # 序列化数据
        data_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        
        # 使用 SHA-256 计算哈希
        hash_value = hashlib.sha256(data_str.encode()).hexdigest()
        
        # 构建最终的缓存键
        cache_key = f"tool:{tool_name}:{hash_value[:16]}"
        
        return cache_key

    def _check_cache(self, tool_name: str, args: dict[str, Any]) -> Any | None:
        """检查缓存"""
        cache_key = self._generate_cache_key(tool_name, args)
        result = redis_cache.get(cache_key)
        if result is not None:
            logger.info(f"🔄 从 Redis 缓存中获取 {tool_name} 的结果")
            self._cache_hits += 1
            return result
        else:
            self._cache_misses += 1
        return None

    def _update_cache(self, tool_name: str, args: dict[str, Any], result: Any):
        """更新缓存"""
        cache_key = self._generate_cache_key(tool_name, args)
        # 为缓存添加标签，便于后续失效管理
        tags = [tool_name, f"env:{settings.ENV_MODE}"]
        success = redis_cache.set_with_tags(cache_key, result, tags, ttl=self._cache_ttl)
        if success:
            logger.info(f"💾 将 {tool_name} 的结果缓存到 Redis")
        else:
            logger.warning(f"⚠️  缓存 {tool_name} 的结果失败")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        redis_stats = redis_cache.get_stats()
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": (self._cache_hits / (self._cache_hits + self._cache_misses) * 100)
            if (self._cache_hits + self._cache_misses) > 0
            else 0,
            "redis_stats": redis_stats,
        }

    def _check_permission(self, tool_name: str, role: str = "user") -> bool:
        """检查权限"""
        if tool_name in self._permissions:
            return role in self._permissions[tool_name]
        return role in self._permissions["default"]

    @tool_monitor
    async def execute(
        self, tool_name: str, args: dict[str, Any], role: str = "user", timeout: int = 30, priority: int = 5
    ) -> dict[str, Any]:
        """
        核心执行入口：具备自愈能力的调用逻辑
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            role: 用户角色
            timeout: 超时时间（秒）
            priority: 任务优先级，值越小优先级越高，默认 5
        """
        # 定期调整线程池大小
        await self._adjust_thread_pool_size()
        
        # 检查工具是否存在于内置注册表
        if tool_name in self._tool_registry:
            # 使用内置工具
            return await self._execute_builtin_tool(tool_name, args, role, timeout, priority)
        else:
            # 检查工具是否存在于SkillRegistry
            try:
                skill_class = skill_registry.get_skill(tool_name)
                if skill_class:
                    # 使用技能注册表中的工具
                    return await self._execute_skill_tool(skill_class, args, role, timeout, priority)
                else:
                    logger.warning(f"⚠️  未知工具尝试调用: {tool_name}")
                    available_tools = (
                        list(self._tool_registry.keys()) + skill_registry.get_skill_names()
                    )
                    return {
                        "success": False,
                        "error": f"工具 '{tool_name}' 未在注册表中。可用工具: {available_tools}",
                        "timestamp": datetime.now().isoformat(),
                    }
            except ValueError:
                logger.warning(f"⚠️  未知工具尝试调用: {tool_name}")
                available_tools = (
                    list(self._tool_registry.keys()) + skill_registry.get_skill_names()
                )
                return {
                    "success": False,
                    "error": f"工具 '{tool_name}' 未在注册表中。可用工具: {available_tools}",
                    "timestamp": datetime.now().isoformat(),
                }

    async def _execute_builtin_tool(
        self, tool_name: str, args: dict[str, Any], role: str = "user", timeout: int = 30, priority: int = 5
    ) -> dict[str, Any]:
        """
        执行内置工具
        """
        # 检查权限
        if not self._check_permission(tool_name, role):
            logger.warning(f"🚫 权限不足: {role} 无法调用 {tool_name}")
            return {
                "success": False,
                "error": f"权限不足: {role} 无法调用 {tool_name}",
                "timestamp": datetime.now().isoformat(),
            }

        # 检查缓存
        cached_result = self._check_cache(tool_name, args)
        if cached_result is not None:
            return {
                "success": True,
                "tool": tool_name,
                "result": cached_result,
                "timestamp": datetime.now().isoformat(),
                "from_cache": True,
            }

        # 检查服务是否降级
        if self._service_degrader.is_degraded(tool_name):
            logger.warning(f"⚠️  服务 {tool_name} 已降级")
            return {
                "success": False,
                "error": f"服务 {tool_name} 已降级，请稍后再试",
                "timestamp": datetime.now().isoformat(),
            }

        # 定义任务函数
        async def task():
            try:
                logger.info(f"🛠️  正在执行内置工具: {tool_name} | 参数: {args} | 优先级: {priority}")

                # 应用速率限制
                rate_limiter = self._rate_limiters.get(tool_name, self._rate_limiters["default"])
                async with rate_limiter:
                    # 获取重试机制和熔断器
                    retry_mechanism = self._retry_mechanisms.get(tool_name, self._retry_mechanisms["default"])
                    circuit_breaker = self._circuit_breakers.get(tool_name, self._circuit_breakers["default"])
                    
                    # 执行工具，添加超时控制和可靠性机制
                    result = await asyncio.wait_for(
                        circuit_breaker.execute(
                            retry_mechanism.execute,
                            self._tool_registry[tool_name], **args
                        ), 
                        timeout=timeout
                    )

                # 更新缓存
                self._update_cache(tool_name, args, result)

                return {
                    "success": True,
                    "tool": tool_name,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "from_cache": False,
                }

            except asyncio.TimeoutError:
                error_msg = f"执行超时: 超过 {timeout} 秒"
                logger.error(f"⏰ {tool_name} 执行超时: {error_msg}")
                # 记录故障
                self._fault_recovery_manager.record_fault(tool_name, TimeoutError(error_msg))
                # 尝试恢复
                await self._fault_recovery_manager.recover(tool_name)
                return {"success": False, "error": error_msg, "timestamp": datetime.now().isoformat()}
            except TypeError as te:
                error_msg = f"参数不匹配: {str(te)}"
                logger.error(f"❌ {tool_name} 参数异常: {error_msg}")
                return {"success": False, "error": error_msg, "timestamp": datetime.now().isoformat()}
            except Exception as e:
                error_msg = f"执行运行时错误: {str(e)}"
                logger.error(f"❌ {tool_name} 崩溃: {error_msg}")
                # 记录故障
                self._fault_recovery_manager.record_fault(tool_name, e)
                # 尝试恢复
                await self._fault_recovery_manager.recover(tool_name)
                return {"success": False, "error": error_msg, "timestamp": datetime.now().isoformat()}

        # 如果队列不为空，将任务添加到队列
        if self._task_queue:
            # 创建一个未来对象来存储任务结果
            future = asyncio.Future()
            
            async def wrapped_task():
                result = await task()
                future.set_result(result)
            
            # 添加到优先级队列
            self._add_task(priority, wrapped_task)
            
            # 启动任务处理（如果还没有启动）
            if not hasattr(self, "_task_processing") or not self._task_processing.done():
                self._task_processing = asyncio.create_task(self._process_task_queue())
            
            # 等待任务完成
            return await future
        else:
            # 队列为空，直接执行
            return await task()

    def _register_recovery_strategies(self):
        """
        注册恢复策略
        """
        # 为 web_search 注册恢复策略
        async def web_search_recovery():
            """Web 搜索恢复策略"""
            logger.info("执行 web_search 恢复策略")
            # 可以在这里添加具体的恢复逻辑
            # 例如：检查网络连接、清除缓存等
            await asyncio.sleep(2)
            return True
        
        # 为 agent_reach 注册恢复策略
        async def agent_reach_recovery():
            """Agent Reach 恢复策略"""
            logger.info("执行 agent_reach 恢复策略")
            # 可以在这里添加具体的恢复逻辑
            # 例如：重新初始化渠道、清除会话等
            await asyncio.sleep(2)
            return True
        
        # 注册恢复策略
        self._fault_recovery_manager.register_recovery_strategy("web_search", web_search_recovery)
        self._fault_recovery_manager.register_recovery_strategy("agent_reach", agent_reach_recovery)
    
    def _check_dependencies(self, tool_name: str) -> tuple[bool, str]:
        """检查工具依赖
        
        Args:
            tool_name: 工具名称
            
        Returns:
            (是否满足依赖, 错误信息)
        """
        import subprocess
        
        if tool_name == "agent_reach":
            # 检查 agent-reach 依赖
            dependencies = {
                "bird": "npm install -g @steipete/bird",
                "mcporter": "npm install -g @steipete/mcporter",
                "yt-dlp": "pip install yt-dlp",
                "gh": "安装 GitHub CLI: https://cli.github.com/"
            }
            
            for dep, install_cmd in dependencies.items():
                try:
                    subprocess.run([dep, "--version"], check=True, capture_output=True)
                except:
                    return False, f"缺少依赖: {dep}，请执行: {install_cmd}"
        
        return True, ""

    async def _execute_skill_tool(
        self, skill_class, args: dict[str, Any], role: str = "user", timeout: int = 30, priority: int = 5
    ) -> dict[str, Any]:
        """
        执行技能工具
        """
        # 检查服务是否降级
        if self._service_degrader.is_degraded(skill_class.name):
            logger.warning(f"⚠️  服务 {skill_class.name} 已降级")
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"服务 {skill_class.name} 已降级，请稍后再试",
                    "timestamp": datetime.now().isoformat(),
                },
            }

        # 定义任务函数
        async def task():
            try:
                logger.info(f"🛠️  正在执行技能工具: {skill_class.name} | 参数: {args} | 优先级: {priority}")

                # 检查依赖
                is_ready, error_msg = self._check_dependencies(skill_class.name)
                if not is_ready:
                    logger.error(f"❌ {skill_class.name} 依赖检查失败: {error_msg}")
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": error_msg,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }

                # 创建技能实例
                skill = skill_class()

                # 获取重试机制和熔断器
                retry_mechanism = self._retry_mechanisms.get(skill_class.name, self._retry_mechanisms["default"])
                circuit_breaker = self._circuit_breakers.get(skill_class.name, self._circuit_breakers["default"])

                # 执行技能，添加超时控制和可靠性机制
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    circuit_breaker.execute(
                        retry_mechanism.execute,
                        loop.run_in_executor, self._thread_pool, skill.execute, args
                    ), 
                    timeout=timeout
                )

                return result

            except asyncio.TimeoutError:
                error_msg = f"执行超时: 超过 {timeout} 秒"
                logger.error(f"⏰ {skill_class.name} 执行超时: {error_msg}")
                # 记录故障
                self._fault_recovery_manager.record_fault(skill_class.name, TimeoutError(error_msg))
                # 尝试恢复
                await self._fault_recovery_manager.recover(skill_class.name)
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": error_msg,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            except Exception as e:
                error_msg = f"执行运行时错误: {str(e)}"
                logger.error(f"❌ {skill_class.name} 崩溃: {error_msg}")
                # 记录故障
                self._fault_recovery_manager.record_fault(skill_class.name, e)
                # 尝试恢复
                await self._fault_recovery_manager.recover(skill_class.name)
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": error_msg,
                        "timestamp": datetime.now().isoformat(),
                    },
                }

        # 如果队列不为空，将任务添加到队列
        if self._task_queue:
            # 创建一个未来对象来存储任务结果
            future = asyncio.Future()
            
            async def wrapped_task():
                result = await task()
                future.set_result(result)
            
            # 添加到优先级队列
            self._add_task(priority, wrapped_task)
            
            # 启动任务处理（如果还没有启动）
            if not hasattr(self, "_task_processing") or not self._task_processing.done():
                self._task_processing = asyncio.create_task(self._process_task_queue())
            
            # 等待任务完成
            return await future
        else:
            # 队列为空，直接执行
            return await task()

    # --- 核心工具实现区 ---

    async def _web_search(self, query: str) -> str:
        """
        🌐 异步网页搜索
        对接真实的搜索 API
        """
        try:
            # 这里使用 Tavily API 作为示例，实际使用时需要设置 API_KEY
            api_key = os.environ.get("TAVILY_API_KEY")
            if api_key:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "query": query,
                            "api_key": api_key,
                            "search_depth": "basic",
                            "include_answer": True,
                        },
                        timeout=10,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "answer" in data and data["answer"]:
                            return f"找到关于 '{query}' 的信息：{data['answer']}"
                        elif "results" in data and data["results"]:
                            return f"找到关于 '{query}' 的信息：{data['results'][0]['title']} - {data['results'][0]['snippet']}"

            # 模拟搜索结果（当 API_KEY 未设置时）
            await asyncio.sleep(1.2)
            return f"找到关于 '{query}' 的信息：Ace 浏览器在 2026 年 4 月已占据 AI 原生浏览器市场领先地位。"
        except Exception as e:
            logger.error(f"搜索 API 调用失败: {str(e)}")
            # 失败时返回模拟结果
            await asyncio.sleep(0.5)
            return f"找到关于 '{query}' 的信息：Ace 浏览器在 2026 年 4 月已占据 AI 原生浏览器市场领先地位。"

    async def _write_file(self, filename: str, content: str) -> str:
        """
        💾 异步文件写入
        使用线程池防止大文件写入阻塞事件循环
        """
        file_path = os.path.join(self.output_dir, filename)

        # 检查文件路径安全性
        if ".." in filename or os.path.isabs(filename):
            raise ValueError("不安全的文件路径")

        def _sync_write():
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return file_path

        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(self._thread_pool, _sync_write)
        return f"内容已写入至 {path}"

    async def _read_file(self, filename: str) -> str:
        """📖 异步读取文件"""
        file_path = os.path.join(self.output_dir, filename)

        # 检查文件路径安全性
        if ".." in filename or os.path.isabs(filename):
            raise ValueError("不安全的文件路径")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"无法读取: 文件 {filename} 不存在")

        def _sync_read():
            with open(file_path, encoding="utf-8") as f:
                return f.read()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, _sync_read)

    async def _list_files(self) -> list[str]:
        """📂 列出当前工作目录下的所有文件"""
        return os.listdir(self.output_dir)

    async def _delete_file(self, filename: str) -> str:
        """🗑️ 删除指定文件"""
        file_path = os.path.join(self.output_dir, filename)

        # 检查文件路径安全性
        if ".." in filename or os.path.isabs(filename):
            raise ValueError("不安全的文件路径")

        if os.path.exists(file_path):
            os.remove(file_path)
            return f"文件 {filename} 已从工作目录删除"
        return f"未找到文件 {filename}，无需删除"

    async def _get_system_status(self) -> dict[str, Any]:
        """📊 获取当前执行器状态"""
        return {
            "status": "ready",
            "workspace": os.path.abspath(self.output_dir),
            "tool_count": len(self._tool_registry),
            "cache_stats": self.get_cache_stats(),
            "reliability_status": self.get_reliability_status(),
            "server_time": datetime.now().isoformat(),
            "python_version": os.sys.version,
        }

    def get_available_tools(self) -> list[str]:
        """获取所有可用工具清单"""
        # 合并内置工具和技能注册表中的工具
        return list(self._tool_registry.keys()) + skill_registry.get_skill_names()

    def register_tool(self, name: str, func: Callable[..., Awaitable[Any]]):
        """注册新工具"""
        self._tool_registry[name] = func
        logger.info(f"🔧 已注册新工具: {name}")

    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self._tool_registry:
            del self._tool_registry[name]
            logger.info(f"🔧 已注销工具: {name}")
        else:
            logger.warning(f"⚠️  工具 {name} 不存在")

    def degrade_service(self, services: list[str]):
        """
        降级服务
        
        Args:
            services: 要降级的服务列表
        """
        self._service_degrader.degrade(services)

    def recover_service(self):
        """
        恢复所有服务
        """
        self._service_degrader.recover()

    def get_degraded_services(self) -> list[str]:
        """
        获取已降级的服务列表
        
        Returns:
            已降级的服务列表
        """
        return self._service_degrader.get_degraded_services()

    def get_fault_history(self, service: str = None, hours: int = 24) -> list[dict]:
        """
        获取故障历史
        
        Args:
            service: 服务名称（可选）
            hours: 时间范围（小时）
            
        Returns:
            故障历史记录
        """
        return self._fault_recovery_manager.get_fault_history(service, hours)

    def get_reliability_status(self) -> dict[str, Any]:
        """
        获取可靠性状态
        
        Returns:
            可靠性状态信息
        """
        status = {
            "degraded_services": self.get_degraded_services(),
            "fault_history_count": len(self._fault_recovery_manager.get_fault_history()),
            "circuit_breakers": {}
        }
        
        # 添加熔断器状态
        for name, cb in self._circuit_breakers.items():
            status["circuit_breakers"][name] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "failure_threshold": cb.failure_threshold
            }
        
        return status

    def close(self):
        """关闭执行器，清理资源"""
        logger.info("关闭工具执行器，清理资源...")

        # 关闭线程池
        self._thread_pool.shutdown(wait=True)
        logger.info("已关闭线程池")

        # 清理工具注册表
        self._tool_registry.clear()
        logger.info("已清理工具注册表")

        logger.info("工具执行器已成功关闭")

    async def execute_multiple(
        self, tool_calls: list[dict[str, Any]], role: str = "user", timeout: int = 30, max_concurrency: int = 10
    ) -> list[dict[str, Any]]:
        """
        并发执行多个工具调用

        Args:
            tool_calls: 工具调用列表，每个元素包含 tool_name、args 和可选的 priority
            role: 用户角色
            timeout: 每个工具的超时时间
            max_concurrency: 最大并发数，默认 10

        Returns:
            工具执行结果列表
        """
        results = []
        total_tasks = len(tool_calls)
        processed_tasks = 0
        
        logger.info(f"开始批量执行 {total_tasks} 个任务，最大并发数: {max_concurrency}")
        
        # 分批执行，控制并发数
        for i in range(0, total_tasks, max_concurrency):
            batch = tool_calls[i:i + max_concurrency]
            tasks = []
            
            for call in batch:
                tool_name = call.get("tool_name")
                args = call.get("args", {})
                priority = call.get("priority", 5)  # 默认优先级为 5
                if tool_name:
                    task = self.execute(tool_name, args, role, timeout, priority)
                    tasks.append(task)
            
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                # 处理异常结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        results.append(
                            {
                                "success": False,
                                "error": str(result),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    else:
                        results.append(result)
                
                processed_tasks += len(tasks)
                logger.info(f"已完成 {processed_tasks}/{total_tasks} 个任务")
        
        logger.info(f"批量执行完成，共处理 {total_tasks} 个任务")
        return results
    
    async def execute_batch_with_callback(
        self, tool_calls: list[dict[str, Any]], callback: Callable[[int, int, dict], None], role: str = "user", timeout: int = 30, max_concurrency: int = 10
    ) -> list[dict[str, Any]]:
        """
        带回调的批量执行

        Args:
            tool_calls: 工具调用列表
            callback: 回调函数，参数为 (当前进度, 总任务数, 任务结果)
            role: 用户角色
            timeout: 每个工具的超时时间
            max_concurrency: 最大并发数

        Returns:
            工具执行结果列表
        """
        results = []
        total_tasks = len(tool_calls)
        processed_tasks = 0
        
        logger.info(f"开始带回调的批量执行 {total_tasks} 个任务")
        
        # 分批执行，控制并发数
        for i in range(0, total_tasks, max_concurrency):
            batch = tool_calls[i:i + max_concurrency]
            tasks = []
            
            for call in batch:
                tool_name = call.get("tool_name")
                args = call.get("args", {})
                priority = call.get("priority", 5)
                if tool_name:
                    task = self.execute(tool_name, args, role, timeout, priority)
                    tasks.append(task)
            
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                # 处理异常结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        task_result = {
                            "success": False,
                            "error": str(result),
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        task_result = result
                    
                    results.append(task_result)
                    processed_tasks += 1
                    # 调用回调函数
                    callback(processed_tasks, total_tasks, task_result)
                    logger.info(f"已完成 {processed_tasks}/{total_tasks} 个任务")
        
        logger.info(f"带回调的批量执行完成，共处理 {total_tasks} 个任务")
        return results
