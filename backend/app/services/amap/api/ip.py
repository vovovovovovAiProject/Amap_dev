from typing import Optional
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient
from ..types import IPInfo

class IPMixin:
    """
    IP定位 API
    """
    
    async def ip(self: "AmapClient", ip: Optional[str] = None) -> Optional[IPInfo]:
        """
        IP定位
        
        :param ip: IP地址，不传默认为请求发起的IP
        :return: IP定位信息
        """
        path = "/ip"
        params = {}
        if ip:
            params["ip"] = ip
            
        data = await self._request("GET", path, params)
        
        if data.get("status") == "1":
            return IPInfo(
                province=data.get("province", ""),
                city=data.get("city", ""),
                adcode=data.get("adcode", ""),
                rectangle=data.get("rectangle", "")
            )
        return None
