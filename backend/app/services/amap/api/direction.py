from typing import Optional, Dict, Any
from typing import Optional, Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from ..client import AmapClient

class DirectionMixin:
    """
    路径规划 API
    """
    
    async def direction_walking(self: "AmapClient", origin: str, destination: str) -> Dict[str, Any]:
        """
        步行路径规划
        """
        path = "/direction/walking"
        params = {
            "origin": origin,
            "destination": destination
        }
        return await self._request("GET", path, params)

    async def direction_transit(self: "AmapClient", origin: str, destination: str, city: str,
                              cityd: Optional[str] = None, strategy: int = 0,
                              nightflag: int = 0, date: Optional[str] = None,
                              time: Optional[str] = None) -> Dict[str, Any]:
        """
        公交路径规划
        """
        path = "/direction/transit/integrated"
        params = {
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": strategy,
            "nightflag": nightflag
        }
        if cityd:
            params["cityd"] = cityd
        if date:
            params["date"] = date
        if time:
            params["time"] = time
            
        return await self._request("GET", path, params)

    async def direction_driving(self: "AmapClient", origin: str, destination: str,
                              strategy: int = 10, waypoints: Optional[str] = None,
                              avoidpolygons: Optional[str] = None,
                              plate: Optional[str] = None) -> Dict[str, Any]:
        """
        驾车路径规划
        """
        path = "/direction/driving"
        params = {
            "origin": origin,
            "destination": destination,
            "strategy": strategy
        }
        if waypoints:
            params["waypoints"] = waypoints
        if avoidpolygons:
            params["avoidpolygons"] = avoidpolygons
        if plate:
            params["province"] = plate[0]
            params["number"] = plate[1:]
            
        return await self._request("GET", path, params)

    async def direction_bicycling(self: "AmapClient", origin: str, destination: str) -> Dict[str, Any]:
        """
        骑行路径规划
        """
        path = "/direction/bicycling"
        params = {
            "origin": origin,
            "destination": destination
        }
        return await self._request("GET", path, params)
