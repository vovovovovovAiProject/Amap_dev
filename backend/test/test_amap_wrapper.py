import os
import asyncio
import logging
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.amap import AmapClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AMAP_KEY = os.getenv("AMAP_API_KEY", "")

async def test_wrapper():
    if not AMAP_KEY:
        logger.error("未找到 AMAP_API_KEY 环境变量")
        return

    logger.info("开始测试高德地图 API 封装...")
    
    async with AmapClient(AMAP_KEY) as client:
        # 1. 测试地理编码
        logger.info("\n--- 测试地理编码 ---")
        try:
            geocodes = await client.geo("北京市朝阳区阜通东大街6号")
            for geo in geocodes:
                logger.info(f"地址: {geo.formatted_address}, 坐标: {geo.location}")
                
            if geocodes:
                # 2. 测试逆地理编码
                logger.info("\n--- 测试逆地理编码 ---")
                location = geocodes[0].location
                regeo = await client.regeo(location)
                if regeo:
                    logger.info(f"坐标: {location} -> 地址: {regeo.formatted_address}")
        except Exception as e:
            logger.error(f"地理编码测试失败: {e}")

        # 3. 测试搜索
        logger.info("\n--- 测试关键字搜索 ---")
        try:
            search_result = await client.search_text("肯德基", city="北京", offset=3)
            logger.info(f"找到 {search_result['count']} 个结果")
            for poi in search_result['pois']:
                logger.info(f"名称: {poi.name}, 地址: {poi.address}")
        except Exception as e:
            logger.error(f"搜索测试失败: {e}")

        # 4. 测试路径规划
        logger.info("\n--- 测试步行路径规划 ---")
        try:
            # 这里的坐标仅作示例
            origin = "116.481028,39.989643"
            dest = "116.465302,40.004717"
            route = await client.direction_walking(origin, dest)
            if route.get("route", {}).get("paths"):
                distance = route["route"]["paths"][0]["distance"]
                duration = route["route"]["paths"][0]["duration"]
                logger.info(f"步行距离: {distance}米, 耗时: {duration}秒")
        except Exception as e:
            logger.error(f"路径规划测试失败: {e}")

        # 5. 测试天气
        logger.info("\n--- 测试天气查询 ---")
        try:
            weather_list = await client.weather("110101") # 北京东城区
            for w in weather_list:
                logger.info(f"城市: {w.city}, 天气: {w.weather}, 温度: {w.temperature}°C")
        except Exception as e:
            logger.error(f"天气测试失败: {e}")

        # 6. 测试行政区域
        logger.info("\n--- 测试行政区域查询 ---")
        try:
            districts = await client.district("北京市", subdistrict=1)
            for d in districts:
                logger.info(f"行政区: {d.name}, 级别: {d.level}, 下级数量: {len(d.districts)}")
                if d.districts:
                    logger.info(f"第一个下级: {d.districts[0].name}")
        except Exception as e:
            logger.error(f"行政区域测试失败: {e}")

        # 7. 测试IP定位
        logger.info("\n--- 测试IP定位 ---")
        try:
            ip_info = await client.ip()
            if ip_info:
                logger.info(f"当前IP位置: {ip_info.province} {ip_info.city} ({ip_info.rectangle})")
        except Exception as e:
            logger.error(f"IP定位测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_wrapper())
