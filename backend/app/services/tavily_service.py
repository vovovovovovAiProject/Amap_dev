"""
Tavily 联网搜索服务
用于获取实时旅游信息、景点攻略等
"""

import os
import httpx
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class TavilyService:
    """Tavily 搜索服务"""

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        self.base_url = "https://api.tavily.com"

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> dict:
        """
        执行搜索查询

        Args:
            query: 搜索关键词
            search_depth: 搜索深度 "basic" 或 "advanced"
            max_results: 最大结果数
            include_domains: 只搜索这些域名
            exclude_domains: 排除这些域名

        Returns:
            搜索结果字典
        """
        if not self.api_key:
            return {"error": "Tavily API key not configured", "results": []}

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {"error": str(e), "results": []}

    async def search_travel_info(self, city: str, topic: str = None) -> dict:
        """
        搜索旅游相关信息

        Args:
            city: 城市名
            topic: 主题（如 "美食"、"景点"、"攻略"）

        Returns:
            搜索结果
        """
        if topic:
            query = f"{city} {topic} 旅游攻略 推荐"
        else:
            query = f"{city} 旅游攻略 必去景点 推荐"

        # 优先搜索旅游相关网站
        include_domains = [
            "mafengwo.cn",      # 马蜂窝
            "ctrip.com",        # 携程
            "dianping.com",     # 大众点评
            "xiaohongshu.com",  # 小红书
            "zhihu.com",        # 知乎
            "sohu.com",
            "163.com"
        ]

        return await self.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_domains=include_domains
        )

    async def search_restaurant(self, city: str, cuisine: str = None) -> dict:
        """搜索餐厅推荐"""
        if cuisine:
            query = f"{city} {cuisine} 餐厅推荐 必吃"
        else:
            query = f"{city} 美食 餐厅推荐 必吃 特色"

        return await self.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

    async def search_attraction(self, city: str, attraction_type: str = None) -> dict:
        """搜索景点信息"""
        if attraction_type:
            query = f"{city} {attraction_type} 景点 攻略"
        else:
            query = f"{city} 必去景点 旅游攻略 推荐"

        return await self.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

    async def search_travel_tips(self, city: str) -> dict:
        """搜索旅行贴士"""
        query = f"{city} 旅游注意事项 避坑指南 实用攻略"

        return await self.search(
            query=query,
            search_depth="basic",
            max_results=3
        )

    def format_search_results(self, results: dict) -> str:
        """
        格式化搜索结果为可读文本

        Args:
            results: Tavily 返回的搜索结果

        Returns:
            格式化的文本
        """
        if results.get("error"):
            return f"搜索出错: {results['error']}"

        output = []

        # 如果有直接答案
        if results.get("answer"):
            output.append(f"📝 {results['answer']}\n")

        # 搜索结果
        search_results = results.get("results", [])
        if search_results:
            output.append("🔍 相关信息：")
            for i, result in enumerate(search_results[:5], 1):
                title = result.get("title", "")
                content = result.get("content", "")[:200]  # 截取前200字
                url = result.get("url", "")

                output.append(f"\n{i}. **{title}**")
                output.append(f"   {content}...")
                if url:
                    output.append(f"   来源: {url}")

        return "\n".join(output) if output else "未找到相关信息"
