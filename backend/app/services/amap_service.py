"""
高德地图API服务封装
基于高德MCP Server实现LBS功能
"""

import os
import logging
import math
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from app.services.amap import AmapClient

# 加载环境变量
load_dotenv()
logger = logging.getLogger(__name__)

# 需要过滤的POI类型关键词
EXCLUDED_POI_KEYWORDS = [
    "停车场", "停车", "加油站", "充电站", "公厕", "厕所", "卫生间",
    "ATM", "银行", "药店", "医院", "诊所", "派出所", "警察",
    "汽车站", "火车站", "机场", "地铁站",  # 交通枢纽单独处理
    "写字楼", "办公", "工厂", "仓库", "物流",
    "小区", "住宅", "公寓",  # 住宅区
    "超市", "便利店", "商场",  # 购物单独处理
]

# POI类型分类
POI_CATEGORIES = {
    "景点": ["风景名胜", "公园广场", "动植物园", "游乐园", "博物馆", "展览馆", "纪念馆", "寺庙", "教堂", "古迹", "海滨浴场"],
    "餐饮": ["中餐厅", "西餐厅", "快餐", "小吃", "火锅", "烧烤", "海鲜", "咖啡厅", "茶馆", "甜品店"],
    "住宿": ["酒店", "宾馆", "民宿", "客栈", "度假村"],
    "购物": ["商场", "购物中心", "特产店", "免税店"],
    "娱乐": ["KTV", "酒吧", "电影院", "剧院", "演出"],
}

# POI类型对应的游览时长（分钟）
POI_DURATION_MAP = {
    "风景名胜": 120,
    "公园广场": 90,
    "动植物园": 150,
    "游乐园": 180,
    "博物馆": 120,
    "展览馆": 90,
    "纪念馆": 60,
    "寺庙": 60,
    "教堂": 45,
    "古迹": 90,
    "海滨浴场": 180,
    "中餐厅": 60,
    "西餐厅": 75,
    "快餐": 30,
    "小吃": 45,
    "火锅": 90,
    "烧烤": 75,
    "海鲜": 90,
    "咖啡厅": 45,
    "茶馆": 60,
    "甜品店": 30,
    "酒店": 0,
    "宾馆": 0,
    "民宿": 0,
    "商场": 120,
    "购物中心": 150,
    "特产店": 45,
}

# POI类型对应的参考费用（元/人）
POI_COST_MAP = {
    "风景名胜": 80,
    "公园广场": 0,
    "动植物园": 60,
    "游乐园": 150,
    "博物馆": 30,
    "展览馆": 40,
    "纪念馆": 0,
    "寺庙": 20,
    "教堂": 0,
    "古迹": 50,
    "海滨浴场": 0,
    "中餐厅": 60,
    "西餐厅": 100,
    "快餐": 30,
    "小吃": 25,
    "火锅": 80,
    "烧烤": 70,
    "海鲜": 120,
    "咖啡厅": 40,
    "茶馆": 50,
    "甜品店": 35,
    "酒店": 300,
    "宾馆": 150,
    "民宿": 200,
    "商场": 0,
    "购物中心": 0,
    "特产店": 100,
}


class AmapService:
    """高德地图服务 (Refactored to use AmapClient SDK)"""

    def __init__(self):
        self.api_key = os.getenv("AMAP_API_KEY", "")
        if not self.api_key:
            logger.warning("AMAP_API_KEY not found in environment variables.")

    def _filter_pois(self, pois: List[dict]) -> List[dict]:
        """过滤掉不适合旅游的POI"""
        filtered = []
        for poi in pois:
            name = poi.get("name", "")
            poi_type = poi.get("type", "")

            # 检查是否包含排除关键词
            should_exclude = False
            for keyword in EXCLUDED_POI_KEYWORDS:
                if keyword in name or keyword in poi_type:
                    should_exclude = True
                    break

            if not should_exclude:
                filtered.append(poi)

        return filtered

    def _categorize_poi(self, poi: dict) -> str:
        """判断POI的类别"""
        poi_type = poi.get("type", "")
        name = poi.get("name", "")

        for category, keywords in POI_CATEGORIES.items():
            for keyword in keywords:
                if keyword in poi_type or keyword in name:
                    return category

        return "景点"  # 默认为景点

    def _estimate_duration(self, poi: dict) -> int:
        """根据POI类型估算游览时长（分钟）"""
        poi_type = poi.get("type", "")
        name = poi.get("name", "")

        # 先尝试从类型匹配
        for type_key, duration in POI_DURATION_MAP.items():
            if type_key in poi_type or type_key in name:
                return duration

        # 根据类别返回默认值
        category = poi.get("category", "景点")
        if category == "景点":
            return 90
        elif category == "餐饮":
            return 60
        elif category == "住宿":
            return 0
        else:
            return 60

    def _estimate_cost(self, poi: dict) -> int:
        """根据POI类型估算费用（元/人）"""
        poi_type = poi.get("type", "")
        name = poi.get("name", "")
        category = poi.get("category", "景点")

        # 如果API返回了费用信息，优先使用
        cost_str = poi.get("cost", "")
        if cost_str:
            try:
                cost_val = int(float(cost_str))
                if cost_val > 0:
                    return cost_val
            except:
                pass

        # 住宿类别特殊处理（高德API的酒店类型可能不包含"酒店"关键词）
        if category == "住宿":
            # 根据名称判断酒店档次
            if any(k in name for k in ["五星", "豪华", "国际", "希尔顿", "万豪", "香格里拉", "洲际"]):
                return 600
            elif any(k in name for k in ["四星", "商务"]):
                return 400
            elif any(k in name for k in ["快捷", "如家", "汉庭", "7天", "锦江之星"]):
                return 180
            elif "民宿" in name or "客栈" in name:
                return 200
            else:
                return 300  # 默认酒店价格

        # 从类型匹配
        for type_key, cost in POI_COST_MAP.items():
            if type_key in poi_type or type_key in name:
                return cost

        # 根据类别返回默认值
        if category == "景点":
            return 50
        elif category == "餐饮":
            return 60
        else:
            return 0

    def _calculate_distance(self, loc1: str, loc2: str) -> float:
        """计算两个坐标点之间的距离（米）"""
        try:
            lon1, lat1 = map(float, loc1.split(","))
            lon2, lat2 = map(float, loc2.split(","))

            # Haversine公式
            R = 6371000  # 地球半径（米）
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)

            a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            return R * c
        except:
            return float('inf')

    def _optimize_route_order(self, pois: List[dict]) -> List[dict]:
        """使用贪心算法优化POI访问顺序（最近邻算法）"""
        if not pois or len(pois) <= 2:
            return pois.copy() if pois else []

        # 复制列表避免修改原数据
        pois_copy = [poi.copy() for poi in pois]

        # 找到地理中心点，从最北或最西的点开始
        # 这样可以形成一个更合理的游览路线
        def get_coords(poi):
            try:
                loc = poi.get("location", "")
                lon, lat = map(float, loc.split(","))
                return (lon, lat)
            except:
                return (0, 0)

        # 按纬度排序，从北到南（或按经度从西到东）
        pois_with_coords = [(poi, get_coords(poi)) for poi in pois_copy]
        pois_with_coords.sort(key=lambda x: (-x[1][1], x[1][0]))  # 先按纬度降序，再按经度升序

        # 从最北的点开始，使用最近邻算法
        optimized = [pois_with_coords[0][0]]
        remaining = [p[0] for p in pois_with_coords[1:]]

        while remaining:
            current = optimized[-1]
            current_loc = current.get("location", "")

            if not current_loc:
                # 如果当前点没有坐标，直接添加下一个
                optimized.append(remaining.pop(0))
                continue

            # 找最近的下一个点
            min_dist = float('inf')
            nearest_idx = 0

            for i, poi in enumerate(remaining):
                poi_loc = poi.get("location", "")
                if poi_loc:
                    dist = self._calculate_distance(current_loc, poi_loc)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = i

            optimized.append(remaining.pop(nearest_idx))

        print(f"Optimized route: {[p.get('name') for p in optimized]}")
        return optimized

    async def geocode(self, address: str, city: str = "") -> dict:
        """地理编码 - 地址转坐标"""
        async with AmapClient(self.api_key) as client:
            try:
                geocodes = await client.geo(address, city=city)
                if geocodes:
                    geo = geocodes[0]
                    return {
                        "location": geo.location,
                        "formatted_address": geo.formatted_address,
                        "city": geo.city
                    }
            except Exception as e:
                logger.error(f"Geocode error: {e}")
        return {}

    async def reverse_geocode(self, location: str) -> dict:
        """逆地理编码 - 坐标转地址"""
        async with AmapClient(self.api_key) as client:
            try:
                regeo = await client.regeo(location)
                if regeo:
                    return {
                        "formatted_address": regeo.formatted_address,
                        "addressComponent": regeo.addressComponent
                    }
            except Exception as e:
                logger.error(f"Reverse geocode error: {e}")
        return {}

    async def search_pois(
        self,
        city: str,
        keywords: List[str],
        poi_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[dict]:
        """POI搜索（带过滤和分类）"""
        keyword_str = "|".join(keywords) if keywords else ""
        async with AmapClient(self.api_key) as client:
            try:
                result = await client.search_text(
                    keywords=keyword_str,
                    city=city,
                    types=poi_type,
                    offset=page_size * 2,  # 多搜一些，过滤后可能不够
                    page=page,
                    extensions="all"
                )

                pois = []
                for poi in result.get("pois", []):
                    biz_ext = poi.biz_ext or {}
                    photos = poi.photos or []

                    poi_dict = {
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "type": poi.type,
                        "tel": poi.tel if isinstance(poi.tel, str) else "",
                        "rating": biz_ext.get("rating", ""),
                        "cost": biz_ext.get("cost", ""),
                        "photos": [p.model_dump() if hasattr(p, "model_dump") else p for p in photos]
                    }

                    # 添加分类
                    poi_dict["category"] = self._categorize_poi(poi_dict)
                    pois.append(poi_dict)

                # 过滤不适合的POI
                filtered_pois = self._filter_pois(pois)

                # 返回指定数量
                return filtered_pois[:page_size]
            except Exception as e:
                logger.error(f"Search POI error: {e}")
                return []

    async def search_attractions(self, city: str, keywords: List[str] = None, page_size: int = 10) -> List[dict]:
        """专门搜索景点 - 优化版"""
        # 使用景点相关的POI类型代码
        # 110000: 风景名胜
        # 110100: 公园广场
        # 110200: 动植物园
        # 110300: 游乐园
        # 140000: 科教文化服务
        poi_types = "110000|110100|110200|110300|140000"

        # 构建更好的搜索关键词
        if keywords:
            keyword_str = "|".join(keywords)
        else:
            keyword_str = "景点|旅游|风景区|公园|博物馆|古迹"

        async with AmapClient(self.api_key) as client:
            try:
                result = await client.search_text(
                    keywords=keyword_str,
                    city=city,
                    types=poi_types,
                    offset=page_size * 3,  # 多搜一些，过滤后可能不够
                    page=1,
                    extensions="all"
                )

                pois = []
                for poi in result.get("pois", []):
                    biz_ext = poi.biz_ext or {}
                    photos = poi.photos or []

                    # 获取评分，用于排序
                    rating = biz_ext.get("rating", "0")
                    try:
                        rating_float = float(rating) if rating else 0
                    except:
                        rating_float = 0

                    poi_dict = {
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "type": poi.type,
                        "tel": poi.tel if isinstance(poi.tel, str) else "",
                        "rating": rating,
                        "rating_float": rating_float,
                        "cost": biz_ext.get("cost", ""),
                        "photos": [p.model_dump() if hasattr(p, "model_dump") else p for p in photos],
                        "category": "景点",
                    }
                    # 估算游览时长和费用
                    poi_dict["visit_duration"] = self._estimate_duration(poi_dict)
                    poi_dict["estimated_cost"] = self._estimate_cost(poi_dict)
                    pois.append(poi_dict)

                # 过滤
                filtered = self._filter_pois(pois)

                # 按评分排序，优先返回高评分景点
                filtered.sort(key=lambda x: x.get("rating_float", 0), reverse=True)

                return filtered[:page_size]
            except Exception as e:
                logger.error(f"Search attractions error: {e}")
                return []

    async def search_restaurants_nearby(self, location: str, city: str, keywords: List[str] = None, radius: int = 2000) -> List[dict]:
        """在指定位置附近搜索餐厅"""
        async with AmapClient(self.api_key) as client:
            try:
                keyword_str = "|".join(keywords) if keywords else "餐厅|美食"

                result = await client.search_around(
                    location=location,
                    keywords=keyword_str,
                    types="050000",  # 餐饮服务
                    radius=radius,
                    extensions="all"
                )

                pois = []
                for poi in result.get("pois", []):
                    biz_ext = poi.biz_ext or {}
                    photos = poi.photos or []

                    rating = biz_ext.get("rating", "0")
                    try:
                        rating_float = float(rating) if rating else 0
                    except:
                        rating_float = 0

                    poi_dict = {
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "type": poi.type,
                        "distance": poi.distance,
                        "rating": rating,
                        "rating_float": rating_float,
                        "cost": biz_ext.get("cost", ""),
                        "photos": [p.model_dump() if hasattr(p, "model_dump") else p for p in photos],
                        "category": "餐饮",
                    }
                    poi_dict["visit_duration"] = self._estimate_duration(poi_dict)
                    poi_dict["estimated_cost"] = self._estimate_cost(poi_dict)
                    pois.append(poi_dict)

                # 按评分排序
                pois.sort(key=lambda x: x.get("rating_float", 0), reverse=True)
                return pois[:5]
            except Exception as e:
                logger.error(f"Search restaurants nearby error: {e}")
                return []

    async def search_restaurants(self, city: str, keywords: List[str] = None, page_size: int = 5) -> List[dict]:
        """专门搜索餐厅"""
        # 050000: 餐饮服务
        poi_types = "050000"

        keyword_str = "|".join(keywords) if keywords else "餐厅|美食"

        async with AmapClient(self.api_key) as client:
            try:
                result = await client.search_text(
                    keywords=keyword_str,
                    city=city,
                    types=poi_types,
                    offset=page_size * 2,
                    page=1,
                    extensions="all"
                )

                pois = []
                for poi in result.get("pois", []):
                    biz_ext = poi.biz_ext or {}
                    photos = poi.photos or []

                    poi_dict = {
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "type": poi.type,
                        "tel": poi.tel if isinstance(poi.tel, str) else "",
                        "rating": biz_ext.get("rating", ""),
                        "cost": biz_ext.get("cost", ""),
                        "photos": [p.model_dump() if hasattr(p, "model_dump") else p for p in photos],
                        "category": "餐饮"
                    }
                    # 估算时长和费用
                    poi_dict["visit_duration"] = self._estimate_duration(poi_dict)
                    poi_dict["estimated_cost"] = self._estimate_cost(poi_dict)
                    pois.append(poi_dict)

                return pois[:page_size]
            except Exception as e:
                logger.error(f"Search restaurants error: {e}")
                return []

    async def search_hotels(self, city: str, keywords: List[str] = None, page_size: int = 3) -> List[dict]:
        """专门搜索酒店"""
        # 100000: 住宿服务
        poi_types = "100000"

        keyword_str = "|".join(keywords) if keywords else "酒店|宾馆"

        async with AmapClient(self.api_key) as client:
            try:
                result = await client.search_text(
                    keywords=keyword_str,
                    city=city,
                    types=poi_types,
                    offset=page_size * 2,
                    page=1,
                    extensions="all"
                )

                pois = []
                for poi in result.get("pois", []):
                    biz_ext = poi.biz_ext or {}
                    photos = poi.photos or []

                    # 尝试从biz_ext获取酒店价格
                    hotel_cost = biz_ext.get("cost", "")
                    if not hotel_cost:
                        # 高德API中酒店价格可能在其他字段
                        hotel_cost = biz_ext.get("price", "")

                    poi_dict = {
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "type": poi.type,
                        "tel": poi.tel if isinstance(poi.tel, str) else "",
                        "rating": biz_ext.get("rating", ""),
                        "cost": hotel_cost,
                        "photos": [p.model_dump() if hasattr(p, "model_dump") else p for p in photos],
                        "category": "住宿"
                    }
                    # 酒店不需要游览时长，但需要估算费用
                    poi_dict["visit_duration"] = 0
                    poi_dict["estimated_cost"] = self._estimate_cost(poi_dict)
                    pois.append(poi_dict)

                return pois[:page_size]
            except Exception as e:
                logger.error(f"Search hotels error: {e}")
                return []
    
    async def search_around(
        self,
        location: str,
        keywords: str = "",
        radius: int = 1000,
        poi_type: Optional[str] = None
    ) -> List[dict]:
        """周边搜索"""
        async with AmapClient(self.api_key) as client:
            try:
                result = await client.search_around(
                    location=location,
                    keywords=keywords,
                    types=poi_type,
                    radius=radius,
                    extensions="all"
                )
                
                pois = []
                for poi in result.get("pois", []):
                    pois.append({
                        "name": poi.name,
                        "address": poi.address if isinstance(poi.address, str) else "",
                        "location": poi.location,
                        "distance": poi.distance,
                        "type": poi.type
                    })
                return pois
            except Exception as e:
                logger.error(f"Search around error: {e}")
                return []
    
    async def get_route(
        self,
        origin: str,
        destination: str,
        mode: str = "transit",
        city: str = ""
    ) -> dict:
        """路线规划

        Args:
            origin: 起点坐标 (经度,纬度)
            destination: 终点坐标 (经度,纬度)
            mode: 出行方式 (walking/driving/bicycling/transit)
            city: 城市名称，公交路线规划时必需
        """
        async with AmapClient(self.api_key) as client:
            try:
                result = {}
                if mode == "walking":
                    result = await client.direction_walking(origin, destination)
                elif mode == "driving":
                    result = await client.direction_driving(origin, destination, strategy=10)
                elif mode == "bicycling":
                    result = await client.direction_bicycling(origin, destination)
                else:  # transit
                    result = await client.direction_transit(origin, destination, city=city or "北京", strategy=0)
                
                route_data = result.get("route", {})
                
                # 解析路线结果，保持与原有格式兼容
                if mode == "transit":
                    transits = route_data.get("transits", [])
                    if transits:
                        best_route = transits[0]
                        
                        # 提取公交路线的所有坐标点
                        coords = []
                        segments = best_route.get("segments", [])
                        for segment in segments:
                            # 步行部分
                            walking = segment.get("walking", {})
                            if walking and walking.get("steps"):
                                for step in walking.get("steps", []):
                                    if step.get("polyline"):
                                        coords.append(step.get("polyline"))
                            
                            # 公交部分
                            bus = segment.get("bus", {})
                            if bus and bus.get("buslines"):
                                for line in bus.get("buslines", []):
                                    if line.get("polyline"):
                                        coords.append(line.get("polyline"))
                                        
                        full_polyline = ";".join(coords)
                        
                        return {
                            "distance": int(route_data.get("distance", 0) or 0),
                            "duration": int(best_route.get("duration", 0) or 0),
                            "cost": float(best_route.get("cost", 0) or 0),
                            "walking_distance": int(best_route.get("walking_distance", 0) or 0),
                            "segments": segments,
                            "polyline": full_polyline
                        }
                else:
                    paths = route_data.get("paths", [])
                    if paths:
                        best_path = paths[0]
                        
                        # 提取驾车/步行/骑行的所有坐标点
                        coords = []
                        steps = best_path.get("steps", [])
                        for step in steps:
                            if step.get("polyline"):
                                coords.append(step.get("polyline"))
                                
                        full_polyline = ";".join(coords)
                        
                        return {
                            "distance": int(best_path.get("distance", 0) or 0),
                            "duration": int(best_path.get("duration", 0) or 0),
                            "steps": steps,
                            "polyline": full_polyline
                        }
            except Exception as e:
                logger.error(f"Get route error: {e}")
                
        return {}
    
    async def plan_routes(self, pois: List[dict], city: str = "") -> List[dict]:
        """规划多个POI之间的路线

        Args:
            pois: POI列表，每个POI需包含 location 和 name 字段
            city: 城市名称，公交路线规划时使用
        """
        routes = []
        for i in range(len(pois) - 1):
            origin = pois[i].get("location")
            destination = pois[i + 1].get("location")
            if origin and destination:
                try:
                    route = await self.get_route(origin, destination, "transit", city=city)
                    routes.append({
                        "from_poi": pois[i].get("name"),
                        "to_poi": pois[i + 1].get("name"),
                        "transport_mode": "transit",
                        "distance": route.get("distance", 0),
                        "duration": route.get("duration", 0),
                        "cost": route.get("cost", 0),
                        "polyline": route.get("polyline")
                    })
                except Exception as e:
                    logger.error(f"Plan route segment error: {e}")
        return routes
    
    async def get_weather(self, city: str) -> dict:
        """获取天气信息"""
        # SDK的weather返回的是WeatherInfo对象列表(实况)
        # 原有的实现是获取"extensions": "all" (预报)
        # SDK目前主要支持实况，但底层_request支持传参
        # WeatherMixin.weather 支持 extensions 参数
        # 但是 WeatherMixin.weather 返回的是 List[WeatherInfo] (只解析了 lives)
        # 如果要获取预报，我们需要扩展 SDK 或者直接使用 request
        
        # 既然 SDK 的 weather 方法只解析了 lives，我们如果传 extensions='all'，SDK 可能会忽略 forecasts
        # 让我们扩展一下 SDK functionality 或者在这里稍微 hack 一下，
        # 为了保持兼容性，我可能需要修改 SDK 的 weather 方法来支持 forecasts，或者直接在这里使用 client._request
        
        async with AmapClient(self.api_key) as client:
            try:
                # 为了获取预报，我们直接调用 API，因为 SDK 的 weather 方法目前只返回实况对象
                # 或者我们可以修改 SDK。考虑到这是一个 refactoring，修改 SDK 是更好的做法。
                # 但为了快速通过，我先用 _request，或者看下 SDK weather mixin。
                # SDK weather mixin:
                # if data.get("lives") and extensions == "base": ... return results
                # 它没有处理 forecasts。
                
                # 让我们先用 client._request 来保持完全的兼容性
                params = {
                    "city": city,
                    "extensions": "all"
                }
                result = await client._request("GET", "/weather/weatherInfo", params)
                
                forecasts = result.get("forecasts", [])
                if forecasts:
                    forecast = forecasts[0]
                    return {
                        "city": forecast.get("city"),
                        "reporttime": forecast.get("reporttime"),
                        "casts": forecast.get("casts", [])
                    }
            except Exception as e:
                logger.error(f"Get weather error: {e}")
        return {}

    async def get_ip_location(self, ip: str = "") -> dict:
        """IP定位"""
        async with AmapClient(self.api_key) as client:
            try:
                ip_info = await client.ip(ip)
                if ip_info:
                    return {
                        "city": ip_info.city,
                        "rectangle": ip_info.rectangle
                    }
            except Exception as e:
                logger.error(f"IP location error: {e}")
        return {}
