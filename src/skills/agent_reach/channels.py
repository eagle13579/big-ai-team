"""
Channel Manager - 管理 Agent-Reach 的平台渠道
提供统一的渠道发现和路由能力
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlatformType(Enum):
    """平台类型枚举"""

    SOCIAL = "social"  # 社交媒体
    VIDEO = "video"  # 视频平台
    CODE = "code"  # 代码平台
    SEARCH = "search"  # 搜索引擎
    NEWS = "news"  # 新闻资讯
    FINANCE = "finance"  # 金融财经
    FORUM = "forum"  # 论坛社区


@dataclass
class Channel:
    """渠道定义"""

    name: str
    description: str
    platform_type: PlatformType
    requires_auth: bool
    requires_proxy: bool
    upstream_tool: str
    url_patterns: list[str]
    capabilities: list[str]


class ChannelManager:
    """
    渠道管理器
    负责渠道注册、发现和路由
    """

    def __init__(self):
        self.channels: dict[str, Channel] = {}
        self._register_default_channels()

    def _register_default_channels(self):
        """注册默认渠道"""
        default_channels = [
            Channel(
                name="web",
                description="任意网页读取",
                platform_type=PlatformType.SEARCH,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="jina_reader",
                url_patterns=[r"^https?://.*"],
                capabilities=["read", "extract"],
            ),
            Channel(
                name="twitter",
                description="Twitter/X 推文搜索与读取",
                platform_type=PlatformType.SOCIAL,
                requires_auth=True,
                requires_proxy=False,
                upstream_tool="bird",
                url_patterns=[
                    r"twitter\.com/\w+/status/\d+",
                    r"x\.com/\w+/status/\d+",
                    r"twitter\.com/\w+$",
                    r"x\.com/\w+$",
                ],
                capabilities=["search", "read", "timeline"],
            ),
            Channel(
                name="youtube",
                description="YouTube 视频字幕提取与搜索",
                platform_type=PlatformType.VIDEO,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="yt-dlp",
                url_patterns=[r"youtube\.com/watch\?v=", r"youtu\.be/", r"youtube\.com/shorts/"],
                capabilities=["transcript", "search", "metadata"],
            ),
            Channel(
                name="bilibili",
                description="Bilibili 视频字幕提取",
                platform_type=PlatformType.VIDEO,
                requires_auth=False,
                requires_proxy=True,
                upstream_tool="yt-dlp",
                url_patterns=[r"bilibili\.com/video/", r"b23\.tv/"],
                capabilities=["transcript", "metadata"],
            ),
            Channel(
                name="reddit",
                description="Reddit 帖子搜索与读取",
                platform_type=PlatformType.FORUM,
                requires_auth=False,
                requires_proxy=True,
                upstream_tool="reddit_api",
                url_patterns=[r"reddit\.com/r/\w+/", r"reddit\.com/user/\w+"],
                capabilities=["search", "read", "hot"],
            ),
            Channel(
                name="github",
                description="GitHub 仓库与代码搜索",
                platform_type=PlatformType.CODE,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="gh_cli",
                url_patterns=[r"github\.com/[^/]+/[^/]+", r"github\.com/[^/]+$"],
                capabilities=["search_repos", "search_code", "view_repo", "issues"],
            ),
            Channel(
                name="xiaohongshu",
                description="小红书笔记搜索与详情",
                platform_type=PlatformType.SOCIAL,
                requires_auth=True,
                requires_proxy=False,
                upstream_tool="mcporter",
                url_patterns=[r"xiaohongshu\.com/explore/", r"xhslink\.com/"],
                capabilities=["search", "detail", "publish"],
            ),
            Channel(
                name="douyin",
                description="抖音视频解析",
                platform_type=PlatformType.VIDEO,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="mcporter",
                url_patterns=[r"douyin\.com/", r"iesdouyin\.com/"],
                capabilities=["parse", "download"],
            ),
            Channel(
                name="wechat",
                description="微信公众号文章搜索与阅读",
                platform_type=PlatformType.NEWS,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="miku_ai",
                url_patterns=[r"mp\.weixin\.qq\.com/s/"],
                capabilities=["search", "read"],
            ),
            Channel(
                name="weibo",
                description="微博热搜、搜索与用户动态",
                platform_type=PlatformType.SOCIAL,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="mcporter",
                url_patterns=[r"weibo\.com/\d+", r"weibo\.com/u/\d+"],
                capabilities=["trending", "search", "feeds", "comments"],
            ),
            Channel(
                name="linkedin",
                description="LinkedIn Profile 搜索",
                platform_type=PlatformType.SOCIAL,
                requires_auth=True,
                requires_proxy=False,
                upstream_tool="mcporter",
                url_patterns=[r"linkedin\.com/in/", r"linkedin\.com/company/"],
                capabilities=["profile", "search_people", "company"],
            ),
            Channel(
                name="v2ex",
                description="V2EX 热门帖子与节点",
                platform_type=PlatformType.FORUM,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="v2ex_api",
                url_patterns=[r"v2ex\.com/t/\d+", r"v2ex\.com/go/"],
                capabilities=["hot", "node", "topic", "replies"],
            ),
            Channel(
                name="xueqiu",
                description="雪球股票行情与热门帖子",
                platform_type=PlatformType.FINANCE,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="xueqiu_api",
                url_patterns=[r"xueqiu\.com/S/", r"xueqiu\.com/\d+"],
                capabilities=["quote", "search_stock", "hot_posts"],
            ),
            Channel(
                name="rss",
                description="RSS 订阅源解析",
                platform_type=PlatformType.NEWS,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="feedparser",
                url_patterns=[r"\.rss$", r"\.xml$", r"feed"],
                capabilities=["parse", "entries"],
            ),
            Channel(
                name="exa",
                description="Exa AI 语义搜索",
                platform_type=PlatformType.SEARCH,
                requires_auth=False,
                requires_proxy=False,
                upstream_tool="mcporter",
                url_patterns=[],
                capabilities=["web_search", "code_search"],
            ),
        ]

        for channel in default_channels:
            self.channels[channel.name] = channel

    def get_channel(self, name: str) -> Channel | None:
        """获取指定渠道"""
        return self.channels.get(name)

    def get_all_channels(self) -> list[Channel]:
        """获取所有渠道"""
        return list(self.channels.values())

    def get_channels_by_type(self, platform_type: PlatformType) -> list[Channel]:
        """根据类型获取渠道"""
        return [ch for ch in self.channels.values() if ch.platform_type == platform_type]

    def detect_channel_by_url(self, url: str) -> Channel | None:
        """根据 URL 检测对应的渠道"""
        for channel in self.channels.values():
            for pattern in channel.url_patterns:
                try:
                    if re.search(pattern, url, re.IGNORECASE):
                        return channel
                except re.error:
                    continue
        return None

    def get_channel_capabilities(self, name: str) -> list[str]:
        """获取渠道能力列表"""
        channel = self.get_channel(name)
        return channel.capabilities if channel else []

    def is_auth_required(self, name: str) -> bool:
        """检查渠道是否需要认证"""
        channel = self.get_channel(name)
        return channel.requires_auth if channel else False

    def is_proxy_required(self, name: str) -> bool:
        """检查渠道是否需要代理"""
        channel = self.get_channel(name)
        return channel.requires_proxy if channel else False

    def get_upstream_tool(self, name: str) -> str | None:
        """获取渠道使用的上游工具"""
        channel = self.get_channel(name)
        return channel.upstream_tool if channel else None

    def get_channel_stats(self) -> dict[str, Any]:
        """获取渠道统计信息"""
        total = len(self.channels)
        by_type = {}
        auth_required = 0
        proxy_required = 0

        for channel in self.channels.values():
            type_name = channel.platform_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            if channel.requires_auth:
                auth_required += 1
            if channel.requires_proxy:
                proxy_required += 1

        return {
            "total_channels": total,
            "by_type": by_type,
            "auth_required": auth_required,
            "proxy_required": proxy_required,
            "no_config_required": total - auth_required,
        }


# 全局渠道管理器实例
channel_manager = ChannelManager()
