from typing import List, Optional
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient
from ..types import District

class DistrictMixin:
    """
    行政区域查询 API
    """
    
    async def district(self: "AmapClient", keywords: Optional[str] = None, 
                      subdistrict: int = 1, page: int = 1, 
                      offset: int = 20, extensions: str = "base") -> List[District]:
        """
        行政区域查询
        
        :param keywords: 查询关键字
        :param subdistrict: 子级行政区 (0:不返回/1:返回下一级/2:返回下两级/3:返回下三级)
        :param page: 页码
        :param offset: 每页记录数
        :param extensions: 返回结果控制
        :return: 行政区列表
        """
        path = "/config/district"
        params = {
            "subdistrict": subdistrict,
            "page": page,
            "offset": offset,
            "extensions": extensions
        }
        if keywords:
            params["keywords"] = keywords
            
        data = await self._request("GET", path, params)
        
        results = []
        if data.get("districts"):
            for item in data["districts"]:
                results.append(District(**item))
                
        return results
