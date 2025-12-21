import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import models, schemas

# Initialize DB
DATABASE_URL = "sqlite+aiosqlite:///./app.db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def debug_list_trips():
    async with AsyncSessionLocal() as db:
        print("--- Querying Trips ---")
        try:
            # 1. Check existing
            result = await db.execute(
                select(models.Trip)
                .options(selectinload(models.Trip.trip_days).selectinload(models.TripDay.items))
                .order_by(models.Trip.id.desc())
            )
            trips = result.scalars().all()
            print(f"Found {len(trips)} trips in DB.")
            
            # 2. If empty, insert ONE test trip to verify schema
            if len(trips) == 0:
                print("Inserting 1 test trip...")
                new_trip = models.Trip(
                    title="Test Trip",
                    city="Beijing",
                    days=1,
                    user_id=1
                )
                db.add(new_trip)
                await db.flush()
                
                new_day = models.TripDay(
                    trip_id=new_trip.id,
                    day_index=1,
                    date=None
                )
                db.add(new_day)
                await db.flush()
                
                new_item = models.TripItem(
                    trip_day_id=new_day.id,
                    name="Tiananmen",
                    location="116.397128,39.916527",
                    order=0
                )
                db.add(new_item)
                await db.commit()
                
                # Query again with loading
                result = await db.execute(
                    select(models.Trip)
                    .where(models.Trip.id == new_trip.id)
                    .options(selectinload(models.Trip.trip_days).selectinload(models.TripDay.items))
                )
                trips = [result.scalars().first()]
                print(f"Created Trip {trips[0].id}")

            # 3. Validate
            for i, trip in enumerate(trips):
                print(f"\nValidating Trip {trip.id}: {trip.title}")
                try:
                    # Attempt manual validation
                    pydantic_trip = schemas.Trip.model_validate(trip)
                    print("  [OK] Valid")
                except Exception as e:
                    print(f"  [FAIL] Invalid: {e}")
                            
        except Exception as query_e:
            import traceback
            traceback.print_exc()
            print(f"Query Failed: {query_e}")

if __name__ == "__main__":
    asyncio.run(debug_list_trips())
