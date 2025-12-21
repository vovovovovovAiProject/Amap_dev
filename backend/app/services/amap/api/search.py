from typing import Optional, List, Dict, Any
from typing import Optional, List, Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient
from ..types import Poi

class SearchMixin:
    """
    搜索 (POI) 相关 API
    """
    
    async def search_text(self: "AmapClient", keywords: str, types: Optional[str] = None,
                         city: Optional[str] = None, citylimit: bool = False,
                         children: int = 0, offset: int = 20, page: int = 1,
                         extensions: str = "base") -> Dict[str, Any]:
        """
        关键字搜索/文本搜索
        
        :param keywords: 查询关键字
        :param types: POI类型
        :param city: 查询城市
        :param citylimit: 仅返回指定城市数据
        :param children: 是否返回子POI
        :param offset: 每页记录数
        :param page: 当前页数
        :param extensions: 返回结果控制
        :return: 搜索结果 (包含 pois 列表和 total 计数)
        """
        path = "/place/text"
        params = {
            "keywords": keywords,
            "offset": offset,
            "page": page,
            "extensions": extensions,
            "children": children,
            "citylimit": "true" if citylimit else "false"
        }
        if types:
            params["types"] = types
        if city:
            params["city"] = city
            
        data = await self._request("GET", path, params)
        
        pois = []
        if data.get("pois"):
            for item in data["pois"]:
                pois.append(Poi(**item))
                
        return {
            "count": int(data.get("count", 0)),
            "pois": pois,
            "suggestion": data.get("suggestion", {})
        }

    async def search_around(self: "AmapClient", location: str, keywords: Optional[str] = None,
                           types: Optional[str] = None, city: Optional[str] = None,
                           radius: int = 3000, sortrule: str = "distance",
                           offset: int = 20, page: int = 1, extensions: str = "base") -> Dict[str, Any]:
        """
        周边搜索
        
        :param location: 中心点坐标
        :param keywords: 查询关键字
        :param types: POI类型
        :param city: 查询城市
        :param radius: 查询半径
        :param sortrule: 排序规则
        :param offset: 每页记录数
        :param page: 当前页数
        :param extensions: 返回结果控制
        """
        path = "/place/around"
        params = {
            "location": location,
            "radius": radius,
            "sortrule": sortrule,
            "offset": offset,
            "page": page,
            "extensions": extensions
        }
        if keywords:
            params["keywords"] = keywords
        if types:
            params["types"] = types
        if city:
            params["city"] = city
            
        data = await self._request("GET", path, params)
        
        pois = []
        if data.get("pois"):
            for item in data["pois"]:
                pois.append(Poi(**item))
                
        return {
            "count": int(data.get("count", 0)),
            "pois": pois
        }

    async def inputtips(self: "AmapClient", keywords: str, city: Optional[str] = None,
                       location: Optional[str] = None, datatype: str = "all",
                       citylimit: bool = False) -> List[Dict[str, Any]]:
        """
        输入提示
        
        :param keywords: 查询关键字
        :param city: 查询城市
        :param location: 经纬度
        :param datatype: 返回数据类型 (all/poi/bus/busline)
        :param citylimit: 仅搜索当前城市
        """
        path = "/assistant/inputtips"
        params = {
            "keywords": keywords,
            "datatype": datatype,
            "citylimit": "true" if citylimit else "false"
        }
        if city:
            params["city"] = city
        if location:
            params["location"] = location
            
        data = await self._request("GET", path, params)
        return data.get("tips", [])
