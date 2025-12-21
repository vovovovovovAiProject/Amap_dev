import httpx
import logging
from typing import Dict, Any, Optional

from .api.geocoding import GeocodingMixin
from .api.search import SearchMixin
from .api.direction import DirectionMixin
from .api.weather import WeatherMixin
from .api.district import DistrictMixin
from .api.ip import IPMixin

logger = logging.getLogger(__name__)

class AmapClient(GeocodingMixin, SearchMixin, DirectionMixin, 
                 WeatherMixin, DistrictMixin, IPMixin):
    """
    高德地图 Web 服务 API 客户端
    集成所有功能模块
    """
    BASE_URL = "https://restapi.amap.com/v3"
    
    def __init__(self, api_key: str, http_client: Optional[httpx.AsyncClient] = None):
        """
        初始化高德地图客户端
        
        :param api_key: 高德地图 Web 服务 API Key
        :param http_client: 可选的 httpx.AsyncClient 实例，用于复用连接
        """
        self.api_key = api_key
        self._client = http_client or httpx.AsyncClient()
        self._external_client = http_client is not None

    async def _request(self, method: str, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送 API 请求
        
        :param method: HTTP 方法 (GET, POST)
        :param path: API 路径 (例如 /geocode/geo)
        :param params: 请求参数
        :return: API 响应数据
        :raises Exception: 当 API 返回错误状态时抛出异常
        """
        if params is None:
            params = {}
            
        # 添加 API Key
        params["key"] = self.api_key
        # 默认返回 JSON
        params["output"] = "json"
        
        url = f"{self.BASE_URL}{path}"
        
        try:
            # 设置 30 秒超时
            response = await self._client.request(method, url, params=params, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            # 部分接口 status 返回 "1" 代表成功，部分可能是其他方式，这里主要处理通用的 status 字段
            # 注意: IP定位等接口可能返回 status="1"
            if "status" in data and data["status"] == "0":
                error_info = data.get("info", "Unknown Error")
                infocode = data.get("infocode", "")
                logger.error(f"Amap API Error: {error_info} (Code: {infocode}) - URL: {url}")
                raise Exception(f"Amap API Error: {error_info}")
                
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error during Amap API request: {str(e)}")
            raise

    async def close(self):
        """
        关闭 HTTP 客户端
        如果客户端是传入的，则不会关闭
        """
        if not self._external_client:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
