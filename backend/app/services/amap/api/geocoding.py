from typing import Optional, List, Union
from typing import Optional, List, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient
from ..types import GeoCode, ReGeoCode, AmapResponse

class GeocodingMixin:
    """
    地理编码相关 API
    """
    
    async def geo(self: "AmapClient", address: str, city: Optional[str] = None, 
                 batch: bool = False, sig: Optional[str] = None) -> List[GeoCode]:
        """
        地理编码: 将结构化地址转换为高德经纬度坐标
        
        :param address: 结构化地址信息
        :param city: 指定查询的城市
        :param batch: 是否批量查询
        :param sig: 签名
        :return: 地理编码信息列表
        """
        path = "/geocode/geo"
        params = {
            "address": address,
            "batch": "true" if batch else "false"
        }
        if city:
            params["city"] = city
        if sig:
            params["sig"] = sig
            
        data = await self._request("GET", path, params)
        
        results = []
        if data.get("geocodes"):
            for item in data["geocodes"]:
                results.append(GeoCode(**item))
                
        return results

    async def regeo(self: "AmapClient", location: str, poitype: Optional[str] = None, 
                   radius: int = 1000, extensions: str = "base", 
                   batch: bool = False, roadlevel: int = 0) -> Optional[ReGeoCode]:
        """
        逆地理编码: 将经纬度转换为详细结构化地
        
        :param location: 经纬度坐标，格式：经度,纬度
        :param poitype: 返回附近POI类型
        :param radius: 搜索半径
        :param extensions: 返回结果控制 (base/all)
        :param batch: 是否批量
        :param roadlevel: 道路等级
        :return: 逆地理编码结果
        """
        path = "/geocode/regeo"
        params = {
            "location": location,
            "radius": radius,
            "extensions": extensions,
            "batch": "true" if batch else "false",
            "roadlevel": roadlevel
        }
        if poitype:
            params["poitype"] = poitype
            
        data = await self._request("GET", path, params)
        
        if data.get("regeocode"):
            return ReGeoCode(**data["regeocode"])
        return None
