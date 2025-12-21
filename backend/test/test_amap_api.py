"""
高德地图 Web API 测试
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AMAP_KEY = os.getenv("AMAP_API_KEY", "")
BASE_URL = "https://restapi.amap.com/v3"


async def test_geocode():
    """测试地理编码 - 地址转坐标"""
    print("\n" + "=" * 50)
    print("TEST 1: Geocoding")
    print("=" * 50)
    
    url = f"{BASE_URL}/geocode/geo"
    params = {
        "key": AMAP_KEY,
        "address": "北京市天安门"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1" and data.get("geocodes"):
            geo = data["geocodes"][0]
            print(f"PASS!")
            print(f"   地址: {geo.get('formatted_address')}")
            print(f"   坐标: {geo.get('location')}")
            return True
        else:
            print(f"FAIL: {data.get('info', '未知错误')}")
            return False


async def test_poi_search():
    """测试POI搜索"""
    print("\n" + "=" * 50)
    print("TEST 2: POI Search")
    print("=" * 50)
    
    url = f"{BASE_URL}/place/text"
    params = {
        "key": AMAP_KEY,
        "keywords": "故宫",
        "city": "北京",
        "offset": 3,
        "extensions": "all"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1" and data.get("pois"):
            print(f"PASS! Found {len(data['pois'])} results")
            for i, poi in enumerate(data["pois"][:3], 1):
                print(f"   {i}. {poi.get('name')} - {poi.get('address', '暂无地址')}")
            return True
        else:
            print(f"FAIL: {data.get('info', '未知错误')}")
            return False


async def test_route_planning():
    """测试路线规划"""
    print("\n" + "=" * 50)
    print("TEST 3: Route Planning")
    print("=" * 50)
    
    url = f"{BASE_URL}/direction/transit/integrated"
    params = {
        "key": AMAP_KEY,
        "origin": "116.397428,39.90923",  # 天安门
        "destination": "116.403414,39.924091",  # 故宫
        "city": "北京",
        "strategy": 0
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1" and data.get("route"):
            route = data["route"]
            transits = route.get("transits", [])
            if transits:
                best = transits[0]
                print(f"PASS!")
                print(f"   Distance: {route.get('distance')}m")
                print(f"   Duration: {int(best.get('duration', 0)) // 60} min")
                print(f"   Cost: Yuan {best.get('cost', 0)}")
                return True
        
        print(f"FAIL: {data.get('info', '未知错误')}")
        return False


async def test_weather():
    """测试天气查询"""
    print("\n" + "=" * 50)
    print("TEST 4: Weather")
    print("=" * 50)
    
    url = f"{BASE_URL}/weather/weatherInfo"
    params = {
        "key": AMAP_KEY,
        "city": "北京",
        "extensions": "base"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            print(f"PASS!")
            print(f"   City: {live.get('city')}")
            print(f"   Weather: {live.get('weather')}")
            print(f"   Temp: {live.get('temperature')}C")
            print(f"   Humidity: {live.get('humidity')}%")
            return True
        else:
            print(f"FAIL: {data.get('info', '未知错误')}")
            return False


async def main():
    print("\n" + "==" + "=" * 46 + "==")
    print("       高德地图 Web API 测试")
    print("==" + "=" * 46 + "==")
    
    if not AMAP_KEY:
        print("\nERROR: AMAP_API_KEY not found")
        print("   请在 backend/.env 文件中设置 AMAP_API_KEY")
        return
    
    print(f"\nAPI Key: {AMAP_KEY[:8]}...{AMAP_KEY[-4:]}")
    
    results = []
    results.append(await test_geocode())
    results.append(await test_poi_search())
    results.append(await test_route_planning())
    results.append(await test_weather())
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\nSUCCESS! {passed}/{total}")
    else:
        print(f"\nWARNING: Passed {passed}/{total}")
    
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
