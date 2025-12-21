import os
import sys
import asyncio
import logging

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.amap_service import AmapService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_service():
    service = AmapService()
    
    if not service.api_key:
        logger.error("No API KEY found")
        return

    logger.info("--- Testing Geocode ---")
    geo = await service.geocode("北京市朝阳区阜通东大街6号")
    logger.info(f"Geocode result: {geo}")
    
    logger.info("\n--- Testing Search POIs ---")
    pois = await service.search_pois("北京", ["肯德基"], page_size=2)
    logger.info(f"Found {len(pois)} POIs")
    if pois:
        logger.info(f"First POI: {pois[0]}")

    logger.info("\n--- Testing Get Route ---")
    if len(pois) >= 2:
        origin = pois[0]["location"]
        dest = pois[1]["location"]
        route = await service.get_route(origin, dest, "transit")
        logger.info(f"Route result: {route.keys()}")
        
    logger.info("\n--- Testing Weather ---")
    weather = await service.get_weather("北京")
    logger.info(f"Weather result: {weather.keys()}")
    
    logger.info("\n--- Testing IP Location ---")
    ip_loc = await service.get_ip_location()
    logger.info(f"IP Location: {ip_loc}")

if __name__ == "__main__":
    asyncio.run(test_service())
