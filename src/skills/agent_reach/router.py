import re
from typing import Any

from src.skills.agent_reach.interface import BaseReachChannel


class ChannelRouter:
    """渠道路由器，负责智能语义路由和降级机制"""
    
    def __init__(self, channel_manager):
        self.channel_manager = channel_manager
        self.url_patterns = {
            "twitter": [r"twitter\.com", r"x\.com"],
            "youtube": [r"youtube\.com", r"youtu\.be"],
            "bilibili": [r"bilibili\.com"],
            "github": [r"github\.com"],
            "reddit": [r"reddit\.com"],
            "linkedin": [r"linkedin\.com"],
            "v2ex": [r"v2ex\.com"],
            "weibo": [r"weibo\.com"],
            "xiaohongshu": [r"xiaohongshu\.com"],
            "douyin": [r"douyin\.com", r"tiktok\.com"]
        }
    
    def route_by_intent(self, intent: dict[str, Any]) -> BaseReachChannel | None:
        """基于意图智能路由到最合适的渠道
        
        Args:
            intent: 包含 target_platform 和 content_type 的意图字典
            
        Returns:
            匹配的渠道实例，如果没有匹配则返回 None
        """
        target_platform = intent.get("target_platform")
        content_type = intent.get("content_type")
        url = intent.get("url")
        
        # 优先通过 URL 检测渠道
        if url:
            channel = self.detect_channel_by_url(url)
            if channel:
                return channel
        
        # 通过目标平台匹配
        if target_platform:
            channel = self.channel_manager.get_channel_by_name(target_platform)
            if channel:
                return channel
        
        # 通过内容类型匹配
        if content_type:
            return self._match_by_content_type(content_type)
        
        return None
    
    def detect_channel_by_url(self, url: str) -> BaseReachChannel | None:
        """通过 URL 自动检测渠道
        
        Args:
            url: 要检测的 URL
            
        Returns:
            匹配的渠道实例，如果没有匹配则返回 None
        """
        for channel_name, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return self.channel_manager.get_channel_by_name(channel_name)
        return None
    
    def _match_by_content_type(self, content_type: str) -> BaseReachChannel | None:
        """通过内容类型匹配渠道
        
        Args:
            content_type: 内容类型
            
        Returns:
            匹配的渠道实例，如果没有匹配则返回 None
        """
        content_type_map = {
            "social_media": ["twitter", "xiaohongshu", "weibo", "linkedin"],
            "video": ["youtube", "bilibili", "douyin"],
            "code": ["github"],
            "search": ["exa", "web"],
            "news": ["web", "rss"],
            "finance": ["xueqiu"],
            "forum": ["reddit", "v2ex"]
        }
        
        for category, channels in content_type_map.items():
            if category in content_type.lower():
                for channel_name in channels:
                    channel = self.channel_manager.get_channel_by_name(channel_name)
                    if channel:
                        return channel
        
        return None
    
    def get_fallback_channel(self, original_channel_name: str) -> BaseReachChannel | None:
        """获取降级渠道
        
        Args:
            original_channel_name: 原始渠道名称
            
        Returns:
            降级渠道实例，如果没有降级渠道则返回 None
        """
        fallback_map = {
            "exa": ["web"],  # Exa 配额耗尽时降级到 Web
            "twitter": ["web"],  # Twitter 认证失败时降级到 Web
            "github": ["web"],  # GitHub API 限制时降级到 Web
            "youtube": ["web"],  # YouTube 解析失败时降级到 Web
            "bilibili": ["web"],  # Bilibili 代理问题时降级到 Web
            "reddit": ["web"]  # Reddit 代理问题时降级到 Web
        }
        
        if original_channel_name in fallback_map:
            for fallback_name in fallback_map[original_channel_name]:
                channel = self.channel_manager.get_channel_by_name(fallback_name)
                if channel and channel.validate_config():
                    return channel
        
        return None
    
    def get_available_channels(self, action: str) -> list[BaseReachChannel]:
        """获取支持特定操作的可用渠道
        
        Args:
            action: 操作名称
            
        Returns:
            支持该操作的可用渠道列表
        """
        available_channels = []
        for channel in self.channel_manager.get_all_channels():
            if action in channel.capabilities and channel.validate_config():
                available_channels.append(channel)
        return available_channels
