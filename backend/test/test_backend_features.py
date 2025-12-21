import os
import sys
import asyncio
import logging
from datetime import date

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import init_db, get_db
from app.db import models, schemas
from app.api.routes import save_trip, generate_trip
from sqlalchemy import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backend():
    logger.info("1. Initialize DB...")
    await init_db()
    
    logger.info("2. Checking DB session...")
    async for db in get_db():
        logger.info("   DB Session created successfully.")
        
        # Test Saving a Trip
        logger.info("3. Testing Save Trip...")
        trip_data = schemas.TripCreateWithDays(
            title="Test Trip",
            city="Shanghai",
            days=2,
            trip_days=[
                schemas.TripDayCreate(
                    day_index=1,
                    items=[
                        schemas.TripItemCreate(name="Oriental Pearl", location="121.5,31.2", order=0),
                        schemas.TripItemCreate(name="The Bund", location="121.4,31.2", order=1)
                    ]
                ),
                schemas.TripDayCreate(
                    day_index=2,
                    items=[
                        schemas.TripItemCreate(name="Disney", location="121.6,31.1", order=0)
                    ]
                )
            ]
        )
        
        saved_trip = await save_trip(trip_data, db)
        logger.info(f"   Saved Trip ID: {saved_trip.id}")
        
        # Verify persistence
        result = await db.execute(select(models.Trip).where(models.Trip.id == saved_trip.id))
        trip_in_db = result.scalars().first()
        logger.info(f"   Trip in DB: {trip_in_db.title}, Days: {trip_in_db.days}")
        
        # Verify cascade load (if relationship loaded)
        # Note: default relationship loading is lazy, so we might not see items unless eager loaded or accessed in session
        # But this confirms the main record is there.

    logger.info("Backend features verification completed.")

if __name__ == "__main__":
    asyncio.run(test_backend())
