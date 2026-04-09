# -*- coding: utf-8 -*-
"""
Agent-Reach Skill 主类
集成 Agent-Reach 的 17+ 平台能力到 Big-AI-Team
"""

import asyncio
import json
import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.shared.base import BaseSkill
from src.shared.logging import logger

logger = logger.bind(name="AgentReach.Skill")


class AgentReachSkill(BaseSkill):
    """
    Agent-Reach Skill - 互联网能力扩展
    
    支持平台:
    - Web: 任意网页读取 (Jina Reader)
    - Twitter/X: 推文搜索、读取、时间线 (bird CLI)
    - YouTube: 视频字幕提取、搜索 (yt-dlp)
    - Bilibili: 视频字幕提取 (yt-dlp)
    - Reddit: 帖子搜索、读取
    - GitHub: 仓库搜索、代码搜索 (gh CLI)
    - 小红书: 笔记搜索、详情 (mcporter)
    - 抖音: 视频解析 (mcporter)
    - 微信公众号: 文章搜索、阅读
    - 微博: 热搜、搜索、用户动态
    - LinkedIn: Profile 搜索
    - V2EX: 热门帖子、节点
    - 雪球: 股票行情
    - RSS: 订阅源解析
    - Exa: AI 语义搜索
    """
    
    name = "agent_reach"
    description = "互联网多平台搜索与内容获取能力"
    version = "1.0.0"
    
    # 平台到工具的映射
    PLATFORM_TOOLS = {
        "web": "read_webpage",
        "twitter": "search_twitter",
        "youtube": "get_youtube_transcript",
        "bilibili": "get_bilibili_transcript",
        "reddit": "search_reddit",
        "github": "search_github",
        "xiaohongshu": "search_xiaohongshu",
        "douyin": "parse_douyin",
        "wechat": "search_wechat",
        "weibo": "search_weibo",
        "linkedin": "search_linkedin",
        "v2ex": "get_v2ex_topics",
        "xueqiu": "get_stock_quote",
        "rss": "parse_rss",
        "exa": "web_search_exa",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.output_dir = self.config.get("output_dir", "output/agent_reach")
        self._ensure_workspace()
        
    def _ensure_workspace(self):
        """初始化工作目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"📁 已创建 Agent-Reach 工作目录: {self.output_dir}")
    
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent-Reach 工具调用
        
        Args:
            args: {
                "action": "search_twitter" | "read_webpage" | ...,
                "params": {...}
            }
        """
        action = args.get("action")
        params = args.get("params", {})
        
        if not action:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": "缺少 action 参数",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 映射到具体方法
        method_map = {
            # Web
            "read_webpage": self._read_webpage,
            # Twitter
            "search_twitter": self._search_twitter,
            "read_tweet": self._read_tweet,
            "get_user_tweets": self._get_user_tweets,
            # YouTube
            "get_youtube_transcript": self._get_youtube_transcript,
            "search_youtube": self._search_youtube,
            # Bilibili
            "get_bilibili_transcript": self._get_bilibili_transcript,
            # Reddit
            "search_reddit": self._search_reddit,
            # GitHub
            "search_github_repos": self._search_github_repos,
            "search_github_code": self._search_github_code,
            "view_github_repo": self._view_github_repo",
            # 小红书
            "search_xiaohongshu": self._search_xiaohongshu,
            "get_xiaohongshu_detail": self._get_xiaohongshu_detail,
            # 抖音
            "parse_douyin": self._parse_douyin,
            # 微博
            "search_weibo": self._search_weibo,
            "get_weibo_trending": self._get_weibo_trending,
            # Exa 搜索
            "web_search_exa": self._web_search_exa,
            # 诊断
            "doctor": self._doctor_check,
        }
        
        method = method_map.get(action)
        if not method:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"未知的 action: {action}。可用: {list(method_map.keys())}",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        try:
            result = method(**params)
            return {
                "status": "success",
                "observation": {
                    "data": result,
                    "message": f"成功执行 {action}",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Agent-Reach 执行失败: {action} - {str(e)}")
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"执行失败: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    # ───────────────────────────────────────────
    # Web 读取 (Jina Reader)
    # ───────────────────────────────────────────
    def _read_webpage(self, url: str, **kwargs) -> Dict[str, Any]:
        """读取任意网页内容"""
        import httpx
        
        jina_url = f"https://r.jina.ai/{url}"
        
        try:
            response = httpx.get(jina_url, timeout=30)
            response.raise_for_status()
            
            return {
                "url": url,
                "content": response.text,
                "length": len(response.text),
                "method": "jina_reader"
            }
        except Exception as e:
            # Fallback: 直接请求
            try:
                response = httpx.get(url, timeout=30, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                return {
                    "url": url,
                    "content": response.text[:5000],  # 限制长度
                    "length": len(response.text),
                    "method": "direct",
                    "warning": "使用直接请求，可能包含 HTML"
                }
            except Exception as e2:
                raise Exception(f"无法读取网页: {str(e)}, fallback: {str(e2)}")
    
    # ───────────────────────────────────────────
    # Twitter/X (bird CLI)
    # ───────────────────────────────────────────
    def _search_twitter(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索 Twitter 推文"""
        try:
            result = subprocess.run(
                ["bird", "search", query, "-n", str(limit)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"bird CLI 错误: {result.stderr}")
            
            # 解析输出
            tweets = self._parse_bird_output(result.stdout)
            
            return {
                "query": query,
                "tweets": tweets,
                "count": len(tweets),
                "platform": "twitter"
            }
        except FileNotFoundError:
            raise Exception("bird CLI 未安装。请运行: npm install -g @steipete/bird")
        except Exception as e:
            raise Exception(f"Twitter 搜索失败: {str(e)}")
    
    def _read_tweet(self, url_or_id: str, **kwargs) -> Dict[str, Any]:
        """读取单条推文"""
        try:
            result = subprocess.run(
                ["bird", "read", url_or_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"bird CLI 错误: {result.stderr}")
            
            return {
                "tweet": result.stdout,
                "platform": "twitter"
            }
        except FileNotFoundError:
            raise Exception("bird CLI 未安装")
    
    def _get_user_tweets(self, username: str, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """获取用户时间线"""
        try:
            result = subprocess.run(
                ["bird", "user-tweets", f"@{username}", "-n", str(limit)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"bird CLI 错误: {result.stderr}")
            
            tweets = self._parse_bird_output(result.stdout)
            
            return {
                "username": username,
                "tweets": tweets,
                "count": len(tweets),
                "platform": "twitter"
            }
        except FileNotFoundError:
            raise Exception("bird CLI 未安装")
    
    def _parse_bird_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 bird CLI 输出"""
        tweets = []
        # 简单解析，实际可能需要更复杂的逻辑
        lines = output.strip().split("\n")
        for line in lines:
            if line.strip():
                tweets.append({"text": line.strip()})
        return tweets
    
    # ───────────────────────────────────────────
    # YouTube (yt-dlp)
    # ───────────────────────────────────────────
    def _get_youtube_transcript(self, url: str, languages: List[str] = None, **kwargs) -> Dict[str, Any]:
        """获取 YouTube 视频字幕"""
        import tempfile
        
        languages = languages or ["zh-Hans", "zh", "en"]
        lang_str = ",".join(languages)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # 下载字幕
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "--write-sub",
                        "--write-auto-sub",
                        "--sub-langs", lang_str,
                        "--skip-download",
                        "--output", f"{tmpdir}/%(id)s",
                        url
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # 查找生成的字幕文件
                subtitle_files = [f for f in os.listdir(tmpdir) if f.endswith(('.vtt', '.srt'))]
                
                if not subtitle_files:
                    # 尝试获取视频信息
                    info_result = subprocess.run(
                        ["yt-dlp", "--dump-json", url],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if info_result.returncode == 0:
                        video_info = json.loads(info_result.stdout)
                        return {
                            "url": url,
                            "title": video_info.get("title"),
                            "description": video_info.get("description", "")[:500],
                            "subtitles": None,
                            "message": "该视频没有字幕",
                            "platform": "youtube"
                        }
                    else:
                        raise Exception("无法获取视频信息")
                
                # 读取字幕内容
                subtitle_path = os.path.join(tmpdir, subtitle_files[0])
                with open(subtitle_path, "r", encoding="utf-8") as f:
                    subtitle_content = f.read()
                
                # 清理字幕格式
                cleaned_text = self._clean_subtitle(subtitle_content)
                
                return {
                    "url": url,
                    "subtitles": cleaned_text,
                    "subtitle_file": subtitle_files[0],
                    "length": len(cleaned_text),
                    "platform": "youtube"
                }
                
            except FileNotFoundError:
                raise Exception("yt-dlp 未安装。请运行: pip install yt-dlp")
    
    def _search_youtube(self, query: str, limit: int = 5, **kwargs) -> Dict[str, Any]:
        """搜索 YouTube 视频"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", f"ytsearch{limit}:{query}"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"yt-dlp 错误: {result.stderr}")
            
            # 解析每行 JSON
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        video = json.loads(line)
                        videos.append({
                            "title": video.get("title"),
                            "url": video.get("webpage_url"),
                            "duration": video.get("duration_string"),
                            "channel": video.get("channel"),
                            "description": video.get("description", "")[:200]
                        })
                    except json.JSONDecodeError:
                        continue
            
            return {
                "query": query,
                "videos": videos,
                "count": len(videos),
                "platform": "youtube"
            }
            
        except FileNotFoundError:
            raise Exception("yt-dlp 未安装")
    
    def _get_bilibili_transcript(self, url: str, **kwargs) -> Dict[str, Any]:
        """获取 Bilibili 视频字幕"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "--write-sub",
                        "--write-auto-sub",
                        "--sub-langs", "zh-Hans,zh,en",
                        "--convert-subs", "vtt",
                        "--skip-download",
                        "--output", f"{tmpdir}/%(id)s",
                        url
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                subtitle_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]
                
                if subtitle_files:
                    subtitle_path = os.path.join(tmpdir, subtitle_files[0])
                    with open(subtitle_path, "r", encoding="utf-8") as f:
                        subtitle_content = f.read()
                    cleaned_text = self._clean_subtitle(subtitle_content)
                    
                    return {
                        "url": url,
                        "subtitles": cleaned_text,
                        "platform": "bilibili"
                    }
                else:
                    return {
                        "url": url,
                        "subtitles": None,
                        "message": "该视频没有字幕",
                        "platform": "bilibili"
                    }
                    
            except FileNotFoundError:
                raise Exception("yt-dlp 未安装")
    
    def _clean_subtitle(self, subtitle_text: str) -> str:
        """清理字幕格式，提取纯文本"""
        import re
        
        # 移除 VTT/SRT 时间戳和标记
        lines = subtitle_text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # 跳过空行和时间戳行
            if not line.strip():
                continue
            if re.match(r"^\d+$", line.strip()):  # 序号
                continue
            if "-->" in line:  # 时间戳
                continue
            if line.startswith("WEBVTT"):
                continue
            
            # 移除 HTML 标签
            line = re.sub(r"<[^>]+>", "", line)
            
            if line.strip():
                cleaned_lines.append(line.strip())
        
        return "\n".join(cleaned_lines)
    
    # ───────────────────────────────────────────
    # Reddit
    # ───────────────────────────────────────────
    def _search_reddit(self, query: str, subreddit: str = None, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索 Reddit"""
        import httpx
        
        headers = {"User-Agent": "agent-reach/1.0"}
        
        try:
            if subreddit:
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&limit={limit}"
            else:
                url = f"https://www.reddit.com/search.json?q={query}&limit={limit}"
            
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "title": post.get("title"),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "author": post.get("author"),
                    "score": post.get("score"),
                    "subreddit": post.get("subreddit"),
                    "selftext": post.get("selftext", "")[:500]
                })
            
            return {
                "query": query,
                "subreddit": subreddit,
                "posts": posts,
                "count": len(posts),
                "platform": "reddit"
            }
            
        except Exception as e:
            raise Exception(f"Reddit 搜索失败: {str(e)}")
    
    # ───────────────────────────────────────────
    # GitHub (gh CLI)
    # ───────────────────────────────────────────
    def _search_github_repos(self, query: str, language: str = None, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索 GitHub 仓库"""
        try:
            cmd = ["gh", "search", "repos", query, "--limit", str(limit)]
            if language:
                cmd.extend(["--language", language])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"gh CLI 错误: {result.stderr}")
            
            return {
                "query": query,
                "language": language,
                "output": result.stdout,
                "platform": "github"
            }
            
        except FileNotFoundError:
            raise Exception("gh CLI 未安装。请访问: https://cli.github.com")
    
    def _search_github_code(self, query: str, language: str = None, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索 GitHub 代码"""
        try:
            cmd = ["gh", "search", "code", query, "--limit", str(limit)]
            if language:
                cmd.extend(["--language", language])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"gh CLI 错误: {result.stderr}")
            
            return {
                "query": query,
                "language": language,
                "output": result.stdout,
                "platform": "github"
            }
            
        except FileNotFoundError:
            raise Exception("gh CLI 未安装")
    
    def _view_github_repo(self, owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """查看 GitHub 仓库详情"""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", f"{owner}/{repo}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"gh CLI 错误: {result.stderr}")
            
            return {
                "owner": owner,
                "repo": repo,
                "info": result.stdout,
                "platform": "github"
            }
            
        except FileNotFoundError:
            raise Exception("gh CLI 未安装")
    
    # ───────────────────────────────────────────
    # 小红书 (mcporter MCP)
    # ───────────────────────────────────────────
    def _search_xiaohongshu(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索小红书笔记"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"xiaohongshu.search_feeds(keyword: '{keyword}')"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            # 尝试解析 JSON
            try:
                data = json.loads(result.stdout)
                return {
                    "keyword": keyword,
                    "feeds": data,
                    "platform": "xiaohongshu"
                }
            except json.JSONDecodeError:
                return {
                    "keyword": keyword,
                    "raw_output": result.stdout,
                    "platform": "xiaohongshu"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装。请运行: npm install -g @steipete/mcporter")
    
    def _get_xiaohongshu_detail(self, feed_id: str, xsec_token: str, **kwargs) -> Dict[str, Any]:
        """获取小红书笔记详情"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"xiaohongshu.get_feed_detail(feed_id: '{feed_id}', xsec_token: '{xsec_token}')"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            try:
                data = json.loads(result.stdout)
                return {
                    "feed_id": feed_id,
                    "detail": data,
                    "platform": "xiaohongshu"
                }
            except json.JSONDecodeError:
                return {
                    "feed_id": feed_id,
                    "raw_output": result.stdout,
                    "platform": "xiaohongshu"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装")
    
    # ───────────────────────────────────────────
    # 抖音 (mcporter MCP)
    # ───────────────────────────────────────────
    def _parse_douyin(self, share_link: str, **kwargs) -> Dict[str, Any]:
        """解析抖音视频"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"douyin.parse_douyin_video_info(share_link: '{share_link}')"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            try:
                data = json.loads(result.stdout)
                return {
                    "share_link": share_link,
                    "video_info": data,
                    "platform": "douyin"
                }
            except json.JSONDecodeError:
                return {
                    "share_link": share_link,
                    "raw_output": result.stdout,
                    "platform": "douyin"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装")
    
    # ───────────────────────────────────────────
    # 微博 (mcporter MCP)
    # ───────────────────────────────────────────
    def _search_weibo(self, keyword: str, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """搜索微博内容"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"weibo.search_content(keyword: '{keyword}', limit: {limit})"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            try:
                data = json.loads(result.stdout)
                return {
                    "keyword": keyword,
                    "feeds": data,
                    "platform": "weibo"
                }
            except json.JSONDecodeError:
                return {
                    "keyword": keyword,
                    "raw_output": result.stdout,
                    "platform": "weibo"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装")
    
    def _get_weibo_trending(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """获取微博热搜"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"weibo.get_trendings(limit: {limit})"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            try:
                data = json.loads(result.stdout)
                return {
                    "trendings": data,
                    "platform": "weibo"
                }
            except json.JSONDecodeError:
                return {
                    "raw_output": result.stdout,
                    "platform": "weibo"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装")
    
    # ───────────────────────────────────────────
    # Exa AI 搜索 (mcporter MCP)
    # ───────────────────────────────────────────
    def _web_search_exa(self, query: str, num_results: int = 5, **kwargs) -> Dict[str, Any]:
        """使用 Exa 进行 AI 语义搜索"""
        try:
            result = subprocess.run(
                ["mcporter", "call", f"exa.web_search_exa(query: '{query}', numResults: {num_results})"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"mcporter 错误: {result.stderr}")
            
            try:
                data = json.loads(result.stdout)
                return {
                    "query": query,
                    "results": data,
                    "platform": "exa"
                }
            except json.JSONDecodeError:
                return {
                    "query": query,
                    "raw_output": result.stdout,
                    "platform": "exa"
                }
                
        except FileNotFoundError:
            raise Exception("mcporter 未安装")
    
    # ───────────────────────────────────────────
    # 诊断检查
    # ───────────────────────────────────────────
    def _doctor_check(self, **kwargs) -> Dict[str, Any]:
        """运行 Agent-Reach 诊断检查"""
        try:
            result = subprocess.run(
                ["agent-reach", "doctor"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "status": "completed",
                "output": result.stdout,
                "errors": result.stderr if result.stderr else None,
                "returncode": result.returncode
            }
            
        except FileNotFoundError:
            return {
                "status": "not_installed",
                "message": "agent-reach 未安装。请运行: pip install agent-reach"
            }
