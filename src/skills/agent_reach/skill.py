import asyncio
import json
import os
from datetime import datetime
from typing import Any

from src.shared.base import BaseSkill
from src.skills.agent_reach.channels import channel_manager
from src.skills.agent_reach.interface import ResultWrapper
from src.skills.agent_reach.router import ChannelRouter


class AgentReachSkill(BaseSkill):
    """Agent-Reach 技能实现"""
    
    name = "agent_reach"
    description = "Agent-Reach 多平台互联网访问能力"
    
    def __init__(self):
        super().__init__()
        self.channel_router = ChannelRouter(channel_manager)
        self.runtime_state_path = "memory/agent_reach/runtime_state.json"
        self.trace_log_path = "memory/agent_reach/reach_trace.md"
        self._ensure_memory_structure()
    
    def _ensure_memory_structure(self):
        """确保内存结构存在"""
        os.makedirs("memory/agent_reach", exist_ok=True)
        if not os.path.exists(self.runtime_state_path):
            with open(self.runtime_state_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "api_rate_limits": {},
                    "cookie_status": {},
                    "last_used": {}
                }, f, ensure_ascii=False, indent=2)
        if not os.path.exists(self.trace_log_path):
            with open(self.trace_log_path, 'w', encoding='utf-8') as f:
                f.write("# Agent-Reach Trace Log\n\n")
                f.write("| Timestamp | Channel | Action | Status |\n")
                f.write("|-----------|---------|--------|--------|\n")
    
    def _update_runtime_state(self, channel_name: str, action: str, status: str):
        """更新运行时状态"""
        with open(self.runtime_state_path, encoding='utf-8') as f:
            state = json.load(f)
        
        # 更新 API 速率限制
        if channel_name not in state["api_rate_limits"]:
            state["api_rate_limits"][channel_name] = {
                "count": 0,
                "last_reset": datetime.utcnow().isoformat()
            }
        state["api_rate_limits"][channel_name]["count"] += 1
        
        # 更新最后使用时间
        state["last_used"][channel_name] = datetime.utcnow().isoformat()
        
        with open(self.runtime_state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def _log_trace(self, channel_name: str, action: str, status: str):
        """记录操作轨迹"""
        timestamp = datetime.utcnow().isoformat()
        with open(self.trace_log_path, 'a', encoding='utf-8') as f:
            f.write(f"| {timestamp} | {channel_name} | {action} | {status} |\n")
    
    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent-Reach 操作（同步）
        
        Args:
            params: 操作参数，包含 action 和 params 字段
            
        Returns:
            执行结果
        """
        import asyncio
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在事件循环中，使用 create_task
                return loop.run_until_complete(self._execute_async(params))
            else:
                # 不在事件循环中，使用 asyncio.run
                return asyncio.run(self._execute_async(params))
        except RuntimeError:
            # 没有事件循环，创建一个新的
            return asyncio.run(self._execute_async(params))
    
    async def _execute_async(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent-Reach 操作（异步）
        
        Args:
            params: 操作参数，包含 action 和 params 字段
            
        Returns:
            执行结果
        """
        action = params.get("action")
        action_params = params.get("params", {})
        
        if not action:
            return ResultWrapper.wrap_error("agent_reach", "execute", "Action is required")
        
        # 解析意图，确定目标渠道
        intent = self._parse_intent(action, action_params)
        channel = self.channel_router.route_by_intent(intent)
        
        if not channel:
            # 尝试根据操作名称匹配渠道
            channel = self._match_channel_by_action(action)
        
        if not channel:
            return ResultWrapper.wrap_error("agent_reach", action, "No suitable channel found")
        
        # 验证渠道配置
        if not channel.validate_config():
            # 尝试降级
            fallback_channel = self.channel_router.get_fallback_channel(channel.name)
            if fallback_channel:
                channel = fallback_channel
            else:
                return ResultWrapper.wrap_error(
                    channel.name, 
                    action, 
                    "Channel configuration is invalid. Please check dependencies."
                )
        
        try:
            # 执行渠道操作
            result = await channel.execute(action, action_params)
            status = result.get("status", "success")
            
            # 更新运行时状态和轨迹
            self._update_runtime_state(channel.name, action, status)
            self._log_trace(channel.name, action, status)
            
            return result
        except Exception as e:
            # 记录错误
            self._log_trace(channel.name, action, "error")
            return ResultWrapper.wrap_error(channel.name, action, str(e))
    
    async def execute_batch(self, batch_params: list[dict[str, Any]], max_concurrency: int = 10) -> list[dict[str, Any]]:
        """批量执行操作
        
        Args:
            batch_params: 批量操作参数列表
            max_concurrency: 最大并发数，默认 10
            
        Returns:
            批量执行结果列表
        """
        results = []
        # 分批执行，控制并发数
        for i in range(0, len(batch_params), max_concurrency):
            batch = batch_params[i:i + max_concurrency]
            tasks = []
            for params in batch:
                tasks.append(self._execute_async(params))
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    async def execute_batch_with_priority(self, batch_params: list[dict[str, Any]], max_concurrency: int = 10) -> list[dict[str, Any]]:
        """带优先级的批量执行操作
        
        Args:
            batch_params: 批量操作参数列表，每个参数可包含 priority 字段
            max_concurrency: 最大并发数，默认 10
            
        Returns:
            批量执行结果列表
        """
        # 按优先级排序
        sorted_params = sorted(batch_params, key=lambda x: x.get("priority", 5))
        
        results = []
        # 分批执行，控制并发数
        for i in range(0, len(sorted_params), max_concurrency):
            batch = sorted_params[i:i + max_concurrency]
            tasks = []
            for params in batch:
                # 移除 priority 字段，因为 _execute_async 不接受这个参数
                params_copy = params.copy()
                params_copy.pop("priority", None)
                tasks.append(self._execute_async(params_copy))
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    def _parse_intent(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """解析操作意图
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            意图字典
        """
        intent = {
            "action": action,
            "params": params
        }
        
        # 从操作名称中提取目标平台
        platform_map = {
            "twitter": ["twitter", "x"],
            "youtube": ["youtube"],
            "bilibili": ["bilibili"],
            "github": ["github"],
            "web": ["web", "read"],
            "exa": ["exa"],
            "reddit": ["reddit"],
            "v2ex": ["v2ex"],
            "xiaohongshu": ["xiaohongshu"],
            "weibo": ["weibo"],
            "douyin": ["douyin"],
            "linkedin": ["linkedin"],
            "rss": ["rss"],
            "xueqiu": ["xueqiu"]
        }
        
        for platform, keywords in platform_map.items():
            for keyword in keywords:
                if keyword in action.lower():
                    intent["target_platform"] = platform
                    break
            if "target_platform" in intent:
                break
        
        # 从参数中提取 URL
        if "url" in params:
            intent["url"] = params["url"]
        
        return intent
    
    def _match_channel_by_action(self, action: str) -> Any:
        """根据操作名称匹配渠道
        
        Args:
            action: 操作名称
            
        Returns:
            匹配的渠道实例
        """
        action_channel_map = {
            "search_twitter": "twitter",
            "get_twitter_user": "twitter",
            "get_twitter_timeline": "twitter",
            "get_youtube_transcript": "youtube",
            "search_youtube": "youtube",
            "get_youtube_video": "youtube",
            "get_bilibili_transcript": "bilibili",
            "get_bilibili_video": "bilibili",
            "search_github_repos": "github",
            "search_github_code": "github",
            "get_github_repo": "github",
            "read_webpage": "web",
            "search_web": "web",
            "search_exa": "exa",
            "search_reddit": "reddit",
            "get_reddit_post": "reddit",
            "search_v2ex": "v2ex",
            "get_v2ex_post": "v2ex",
            "search_xiaohongshu": "xiaohongshu",
            "get_xiaohongshu_note": "xiaohongshu",
            "search_weibo": "weibo",
            "get_weibo_hot": "weibo",
            "get_weibo_user": "weibo",
            "get_douyin_video": "douyin",
            "search_linkedin": "linkedin",
            "get_linkedin_profile": "linkedin",
            "read_rss": "rss",
            "search_xueqiu": "xueqiu",
            "get_xueqiu_stock": "xueqiu"
        }
        
        channel_name = action_channel_map.get(action)
        if channel_name:
            return channel_manager.get_channel_by_name(channel_name)
        
        return None
    
    def get_capabilities(self) -> list[str]:
        """获取技能能力列表
        
        Returns:
            能力列表
        """
        capabilities = []
        for channel in channel_manager.get_all_channels():
            capabilities.extend(channel.capabilities)
        return list(set(capabilities))
