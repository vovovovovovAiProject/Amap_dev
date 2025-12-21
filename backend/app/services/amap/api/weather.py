from typing import List, Optional
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient
from ..types import WeatherInfo

class WeatherMixin:
    """
    天气查询 API
    """
    
    async def weather(self: "AmapClient", city: str, extensions: str = "base") -> List[WeatherInfo]:
        """
        天气查询
        
        :param city: 城市编码
        :param extensions: 气象类型 (base:实况天气/all:预报天气)
        :return: 天气信息列表
        """
        path = "/weather/weatherInfo"
        params = {
            "city": city,
            "extensions": extensions
        }
        
        data = await self._request("GET", path, params)
        
        results = []
        if data.get("lives") and extensions == "base":
            for item in data["lives"]:
                results.append(WeatherInfo(**item))
        # 注意: 预报天气结构不同，这里暂时主要支持实况，预报可后续扩展或直接返回原始数据
                
        return results
