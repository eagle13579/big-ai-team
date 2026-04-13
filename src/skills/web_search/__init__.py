import asyncio
import os
from typing import Any, Dict, List

import httpx

from src.shared.logging import logger
from src.skills.registry import register_skill


class WebSearchSkill:
    """网络搜索技能，用于执行高级网络搜索"""
    
    def __init__(self):
        self.skill_name = "web_search"
        self.description = "执行网络搜索并返回结果"
        self.logger = logger.bind(skill=self.skill_name)
        # 获取 SerpAPI API key
        self.serpapi_key = os.environ.get("SERPAPI_KEY")
    
    async def execute(self, query: str, **kwargs):
        """
        执行网络搜索
        
        Args:
            query: 搜索查询词
            **kwargs: 额外参数
                - num: 返回结果数量（默认5）
                - lang: 语言限制
                - timeout: 超时时间（秒）
            
        Returns:
            dict: 搜索结果
        """
        try:
            self.logger.info(f"执行搜索: {query}")
            
            # 处理参数
            num = kwargs.get('num', 5)
            lang = kwargs.get('lang')
            timeout = kwargs.get('timeout', 30)
            
            # 构建搜索参数
            search_params = {
                "q": query,
                "num": num,
                "hl": lang if lang else "zh-CN"
            }
            
            # 执行搜索
            if self.serpapi_key:
                # 使用 SerpAPI 执行真实搜索
                results = await self._serpapi_search(search_params, timeout)
            else:
                # 使用模拟数据
                results = self._mock_search(query, num)
            
            # 处理搜索结果
            processed_results = self._process_results(results)
            
            self.logger.info(f"搜索完成，找到 {len(processed_results)} 个结果")
            
            return {
                "status": "success",
                "query": query,
                "results": processed_results,
                "total_results": len(processed_results)
            }
            
        except Exception as e:
            self.logger.error(f"搜索时发生错误: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _serpapi_search(self, params: dict[str, Any], timeout: int) -> list[dict[str, Any]]:
        """
        使用 SerpAPI 执行搜索
        
        Args:
            params: 搜索参数
            timeout: 超时时间
            
        Returns:
            搜索结果
        """
        url = "https://serpapi.com/search.json"
        
        # 添加 API key
        params["api_key"] = self.serpapi_key
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
        # 提取搜索结果
        results = []
        if "organic_results" in data:
            for item in data["organic_results"]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
        
        return results
    
    def _mock_search(self, query: str, num: int) -> list[dict[str, Any]]:
        """
        模拟搜索结果
        
        Args:
            query: 搜索查询词
            num: 返回结果数量
            
        Returns:
            模拟搜索结果
        """
        mock_results = []
        for i in range(num):
            mock_results.append({
                "title": f"搜索结果 {i+1} for {query}",
                "url": f"https://example.com/result/{i+1}",
                "snippet": f"这是关于 {query} 的搜索结果 {i+1} 的摘要信息"
            })
        return mock_results
    
    def _process_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        处理搜索结果
        
        Args:
            results: 原始搜索结果
            
        Returns:
            处理后的搜索结果
        """
        processed = []
        
        for result in results:
            # 提取关键信息
            item = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "rank": len(processed) + 1
            }
            processed.append(item)
        
        return processed
    
    def get_info(self):
        """
        获取技能信息
        
        Returns:
            dict: 技能信息
        """
        return {
            "name": self.skill_name,
            "description": self.description,
            "parameters": {
                "query": "string, 搜索查询词",
                "num": "int, 返回结果数量（默认5）",
                "lang": "string, 语言限制",
                "timeout": "int, 超时时间（秒）"
            }
        }


# 注册技能
register_skill("web_search", WebSearchSkill())