"""
API路由定义
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from app.services.llm_service import LLMService
from app.services.amap_service import AmapService
from app.services.tavily_service import TavilyService
from app.db.database import get_db
from app.db import models, schemas
import datetime
import json

router = APIRouter()

# 初始化服务
llm_service = LLMService()
amap_service = AmapService()
tavily_service = TavilyService()


@router.post("/trip/generate", response_model=schemas.TripResponse)
async def generate_trip(request: schemas.TripRequest):
    """
    生成行程规划 (支持多日) - 优化版
    """
    try:
        # 1. 使用LLM解析用户意图
        parsed_intent = await llm_service.parse_user_intent(request.user_input)
        print(f"Parsed intent: {parsed_intent}")

        city = parsed_intent.get("city", "北京")
        days = parsed_intent.get("duration", 1) or 1
        preferences = parsed_intent.get("preferences", [])

        # 2. 搜索景点（每天3-4个）
        attractions = await amap_service.search_attractions(
            city=city,
            keywords=preferences if preferences else None,
            page_size=days * 4
        )
        print(f"Found {len(attractions)} attractions")

        if not attractions:
            return schemas.TripResponse(
                success=False,
                message=f"未能在{city}找到相关景点，请尝试更换城市或更具体的描述",
                data=None
            )

        # 3. 优化景点顺序
        optimized_attractions = amap_service._optimize_route_order(attractions)

        # 4. 构建每日行程
        trip_days = []
        attractions_per_day = max(3, len(optimized_attractions) // days)

        for day_idx in range(1, days + 1):
            start_idx = (day_idx - 1) * attractions_per_day
            end_idx = start_idx + attractions_per_day if day_idx < days else len(optimized_attractions)
            day_attractions = optimized_attractions[start_idx:end_idx]

            if not day_attractions:
                continue

            # 构建当天的时间表
            day_pois = []
            current_time = 9 * 60  # 从9:00开始，用分钟表示
            total_cost = 0

            # 上午景点（9:00 - 12:00）
            morning_attractions = day_attractions[:2] if len(day_attractions) >= 2 else day_attractions[:1]
            for poi in morning_attractions:
                poi_copy = poi.copy()
                poi_copy["start_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
                duration = poi_copy.get("visit_duration", 90)
                current_time += duration
                poi_copy["end_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
                total_cost += poi_copy.get("estimated_cost", 0)
                day_pois.append(poi_copy)
                current_time += 20  # 20分钟交通时间

            # 午餐（根据当前时间动态调整）
            lunch_time = max(current_time, 12 * 60)  # 至少12:00
            lunch_location = morning_attractions[-1].get("location") if morning_attractions else None
            if lunch_location:
                nearby_restaurants = await amap_service.search_restaurants_nearby(
                    location=lunch_location,
                    city=city,
                    keywords=preferences if any(k in str(preferences) for k in ["美食", "吃", "餐"]) else None
                )
                if nearby_restaurants:
                    lunch = nearby_restaurants[0].copy()
                    lunch_duration = lunch.get("visit_duration", 60)
                    lunch["start_time"] = f"{lunch_time // 60:02d}:{lunch_time % 60:02d}"
                    lunch_time += lunch_duration
                    lunch["end_time"] = f"{lunch_time // 60:02d}:{lunch_time % 60:02d}"
                    lunch["time_slot"] = "午餐"
                    total_cost += lunch.get("estimated_cost", 60)
                    day_pois.append(lunch)
                    current_time = lunch_time + 15

            # 下午景点（午餐后 - 18:00）
            afternoon_attractions = day_attractions[2:5] if len(day_attractions) > 2 else []
            for poi in afternoon_attractions:
                poi_copy = poi.copy()
                poi_copy["start_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
                duration = poi_copy.get("visit_duration", 90)
                current_time += duration
                poi_copy["end_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
                total_cost += poi_copy.get("estimated_cost", 0)
                day_pois.append(poi_copy)
                current_time += 20

            # 晚餐（根据当前时间动态调整）
            dinner_time = max(current_time, 18 * 60)  # 至少18:00
            dinner_location = afternoon_attractions[-1].get("location") if afternoon_attractions else (morning_attractions[-1].get("location") if morning_attractions else None)
            if dinner_location:
                nearby_restaurants = await amap_service.search_restaurants_nearby(
                    location=dinner_location,
                    city=city,
                    keywords=preferences if any(k in str(preferences) for k in ["美食", "吃", "餐"]) else None
                )
                # 选择不同于午餐的餐厅
                lunch_name = None
                for p in day_pois:
                    if p.get("time_slot") == "午餐":
                        lunch_name = p.get("name")
                        break
                for restaurant in nearby_restaurants:
                    if restaurant.get("name") != lunch_name:
                        dinner = restaurant.copy()
                        dinner_duration = dinner.get("visit_duration", 75)
                        dinner["start_time"] = f"{dinner_time // 60:02d}:{dinner_time % 60:02d}"
                        dinner_time += dinner_duration
                        dinner["end_time"] = f"{dinner_time // 60:02d}:{dinner_time % 60:02d}"
                        dinner["time_slot"] = "晚餐"
                        total_cost += dinner.get("estimated_cost", 80)
                        day_pois.append(dinner)
                        current_time = dinner_time
                        break

            # 如果是多日游且不是最后一天，添加酒店
            if days > 1 and day_idx < days:
                hotels = await amap_service.search_hotels(city=city, page_size=1)
                if hotels:
                    hotel = hotels[0].copy()
                    hotel_time = max(current_time + 30, 20 * 60)  # 至少20:00
                    hotel["start_time"] = f"{hotel_time // 60:02d}:{hotel_time % 60:02d}"
                    hotel["end_time"] = ""
                    hotel["visit_duration"] = 0
                    hotel["time_slot"] = "住宿"
                    total_cost += hotel.get("estimated_cost", 300)
                    day_pois.append(hotel)

            # 规划路线
            routes = await amap_service.plan_routes(day_pois, city=city)

            # 构建行程项
            trip_items = []
            for i, poi in enumerate(day_pois):
                trip_items.append(schemas.TripItemCreate(
                    name=poi.get("name"),
                    location=poi.get("location"),
                    address=poi.get("address"),
                    type=poi.get("type"),
                    order=i,
                    visit_duration=poi.get("visit_duration", 60),
                    cost=poi.get("estimated_cost", 0),
                    photos=poi.get("photos", [])
                ))

            # 生成当天摘要
            attraction_names = [p.get("name") for p in day_attractions[:3]]
            summary = f"第{day_idx}天：游览{', '.join(attraction_names)}，预计花费约{total_cost}元/人"

            trip_days.append(schemas.TripDayCreate(
                day_index=day_idx,
                summary=summary,
                items=trip_items,
                routes=routes
            ))

        # 5. 获取天气信息
        weather = await amap_service.get_weather(city)

        # 检查是否成功生成了行程
        if not trip_days or all(len(day.items) == 0 for day in trip_days):
            return schemas.TripResponse(
                success=False,
                message=f"未能为{city}生成有效行程，请尝试更具体的描述",
                data=None
            )

        # 5. 生成行程摘要 (针对整个行程)
        summary = "" # TODO: 生成综合摘要
        
        # 6. 生成旅行智囊建议 (新功能) - 增加鲁棒性
        insights = None
        try:
            print(f"Generating insights for {city}...")
            all_day_pois = []
            for day in trip_days:
                all_day_pois.extend(day.items)
            
            # 使用 model_dump (Pydantic V2) 或 dict (V1)
            poi_dicts = []
            for item in all_day_pois:
                if hasattr(item, 'model_dump'):
                    poi_dicts.append(item.model_dump())
                else:
                    poi_dicts.append(item.dict())
                    
            insights = await llm_service.generate_travel_insights(
                city=city,
                days=days,
                weather=weather,
                pois=poi_dicts
            )
            print("Insights generated successfully.")
        except Exception as e:
            print(f"Failed to generate travel insights: {e}")
            # 生成失败时不影响主流程
            insights = {
                "packing_list": ["雨伞", "充电宝", "舒适的运动鞋"],
                "local_delicacies": ["当地特色小吃"],
                "pro_tips": ["建议提前预订热门景点门票"]
            }
        
        # 构造返回结果
        trip_plan = schemas.TripCreate(
            title=f"{city} {days}日游",
            city=city,
            days=days,
            status="generated"
        )

        # 构造 insights 对象
        insights_obj = None
        if insights:
            insights_obj = schemas.TripInsights(
                packing_list=insights.get("packing_list", []),
                local_delicacies=insights.get("local_delicacies", []),
                pro_tips=insights.get("pro_tips", [])
            )

        return schemas.TripResponse(
            success=True,
            message="行程规划生成成功",
            data=schemas.TripResponseData(
                trip=trip_plan,
                days=trip_days,
                weather=weather,
                insights=insights_obj
            )
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        # 返回统一格式的错误响应，而不是抛出 HTTPException
        return schemas.TripResponse(
            success=False,
            message=f"生成行程时发生错误: {str(e)}",
            data=None
        )


@router.get("/trip/list", response_model=List[schemas.Trip])
async def list_trips(db: AsyncSession = Depends(get_db)):
    """获取行程列表"""
    try:
        result = await db.execute(
            select(models.Trip)
            .options(selectinload(models.Trip.trip_days).selectinload(models.TripDay.items))
            .order_by(models.Trip.id.desc())
        )
        trips = result.scalars().all()
        print(f"Found {len(trips)} trips")
        return trips
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trip/{trip_id}", response_model=schemas.TripResponse)
async def get_trip_detail(trip_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取行程详情 - 直接从数据库加载，不重新规划路线
    """
    print(f"Loading trip detail for ID: {trip_id}")
    try:
        # 查询 Trip
        result = await db.execute(select(models.Trip).where(models.Trip.id == trip_id))
        trip = result.scalars().first()

        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")

        print(f"Found trip: {trip.title}, city: {trip.city}")

        # 查询 Days 和 Items
        result_days = await db.execute(
            select(models.TripDay)
            .where(models.TripDay.trip_id == trip.id)
            .order_by(models.TripDay.day_index)
        )
        days_db = result_days.scalars().all()
        print(f"Found {len(days_db)} days")

        days_response = []
        for day in days_db:
            result_items = await db.execute(
                select(models.TripItem)
                .where(models.TripItem.trip_day_id == day.id)
                .order_by(models.TripItem.order)
            )
            items_db = result_items.scalars().all()
            print(f"Day {day.day_index}: {len(items_db)} items")

            # 转换 items 为 schema（不重新规划路线，前端会用直线连接）
            items_schema = []
            for item in items_db:
                items_schema.append(schemas.TripItemCreate(
                    poi_id=item.poi_id,
                    name=item.name,
                    location=item.location,
                    address=item.address,
                    type=item.type,
                    order=item.order,
                    visit_duration=item.visit_duration or 60,
                    cost=item.cost or 0.0,
                    photos=item.photos or []
                ))

            days_response.append(schemas.TripDayCreate(
                day_index=day.day_index,
                summary=day.summary,
                items=items_schema,
                routes=day.routes or []  # 从数据库读取路线数据
            ))

        # 获取天气（这个可以保留，因为天气是实时的）
        weather = {}
        try:
            weather = await amap_service.get_weather(trip.city)
        except Exception as weather_err:
            print(f"Weather fetch failed: {weather_err}")

        print("Returning saved trip data...")
        return schemas.TripResponse(
            success=True,
            message="获取成功",
            data=schemas.TripResponseData(
                trip=schemas.TripCreate(
                    title=trip.title,
                    city=trip.city,
                    start_date=trip.start_date,
                    end_date=trip.end_date,
                    days=trip.days,
                    budget=trip.budget,
                    status=trip.status
                ),
                days=days_response,
                weather=weather,
                insights=None
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trip/save", response_model=schemas.Trip)
async def save_trip(trip_data: schemas.TripCreateWithDays, db: AsyncSession = Depends(get_db)):
    """保存行程到数据库"""
    try:
        print(f"Saving trip: {trip_data.title}, city: {trip_data.city}, days: {trip_data.days}")
        print(f"Trip days count: {len(trip_data.trip_days)}")

        # 创建 Trip
        db_trip = models.Trip(
            title=trip_data.title,
            city=trip_data.city,
            days=trip_data.days,
            status="planned",
            user_id=1 # 暂时硬编码
        )
        db.add(db_trip)
        await db.flush() # 获取ID
        print(f"Created trip with ID: {db_trip.id}")

        # 创建 Days 和 Items
        for day_data in trip_data.trip_days:
            print(f"Processing day {day_data.day_index} with {len(day_data.items)} items")
            db_day = models.TripDay(
                trip_id=db_trip.id,
                day_index=day_data.day_index,
                date=day_data.date,
                summary=day_data.summary,
                routes=day_data.routes  # 保存路线数据
            )
            db.add(db_day)
            await db.flush()

            for item_data in day_data.items:
                db_item = models.TripItem(
                    trip_day_id=db_day.id,
                    name=item_data.name,
                    location=item_data.location,
                    address=item_data.address,
                    type=item_data.type,
                    order=item_data.order,
                    visit_duration=item_data.visit_duration,
                    photos=item_data.photos
                )
                db.add(db_item)

        await db.commit()

        # 重新查询并预加载关联数据，避免懒加载问题
        result = await db.execute(
            select(models.Trip)
            .options(selectinload(models.Trip.trip_days).selectinload(models.TripDay.items))
            .where(models.Trip.id == db_trip.id)
        )
        saved_trip = result.scalars().first()

        print(f"Trip saved successfully with ID: {saved_trip.id}")
        return saved_trip
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poi/search")
async def search_poi(keyword: str, city: str = "北京", page: int = 1):
    """搜索POI"""
    try:
        results = await amap_service.search_pois(
            city=city,
            keywords=[keyword],
            page=page
        )
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather")
async def get_weather(city: str = "北京"):
    """获取天气信息"""
    try:
        weather = await amap_service.get_weather(city)
        return {"success": True, "data": weather}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trip/{trip_id}")
async def delete_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    """删除行程"""
    print(f"Deleting trip with ID: {trip_id}")
    try:
        # 查询行程
        result = await db.execute(select(models.Trip).where(models.Trip.id == trip_id))
        trip = result.scalars().first()

        if not trip:
            print(f"Trip {trip_id} not found")
            raise HTTPException(status_code=404, detail="行程不存在")

        # 删除行程（级联删除会自动删除关联的 trip_days 和 trip_items）
        await db.delete(trip)
        await db.commit()

        print(f"Trip {trip_id} deleted successfully")
        return {"success": True, "message": "行程已删除"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest):
    """
    对话接口 - 支持多轮对话收集信息后生成行程
    """
    try:
        message = request.message
        current_trip = request.current_trip
        conversation_history = request.conversation_history or []
        collected_info = request.collected_info or {}

        print(f"Chat message: {message}")
        print(f"Collected info: {collected_info}")

        # 构建对话上下文
        context = [{"role": msg.role, "content": msg.content} for msg in conversation_history]

        # 使用LLM分析用户意图
        intent = await llm_service.analyze_chat_intent(message, current_trip, context)
        print(f"Intent: {intent}")

        action = intent.get("action", "ask_questions")
        reply = intent.get("reply", "")
        new_collected_info = intent.get("collected_info", {})

        # 合并收集到的信息
        for key, value in new_collected_info.items():
            if value and value not in [None, "", [], {}]:
                collected_info[key] = value

        # 根据意图执行不同操作
        if action == "generate_trip" or intent.get("ready_to_generate"):
            # 信息足够，生成行程
            city = collected_info.get("city", "北京")
            days = collected_info.get("duration", 1)
            if isinstance(days, str):
                try:
                    days = int(days)
                except:
                    days = 1

            # 构建关键词
            keywords = collected_info.get("preferences", [])
            if not keywords:
                keywords = ["旅游景点"]

            return await generate_trip_from_chat(message, {
                "city": city,
                "duration": days,
                "keywords": keywords,
                "constraints": [collected_info.get("special_needs", "")],
                "poi_type": None
            }, reply or f"好的！正在为你规划 **{city}{days}日游** 🗺️\n\n正在搜索景点、规划路线，请稍等...")

        elif action == "modify_trip" and current_trip:
            # 修改现有行程
            return schemas.ChatResponse(
                success=True,
                reply=reply or "好的，我理解你想要修改行程。目前这个功能还在完善中，你可以告诉我想去哪里，我重新帮你规划。",
                trip_data=None,
                action="modify_trip",
                collected_info=collected_info
            )

        elif action == "info":
            # 纯信息查询或闲聊
            return schemas.ChatResponse(
                success=True,
                reply=reply or "我可以帮你规划旅行行程，告诉我你想去哪里吧！",
                trip_data=None,
                action="info",
                collected_info=collected_info
            )

        elif action == "chat":
            # 自然对话（回答问题、给建议等）
            return schemas.ChatResponse(
                success=True,
                reply=reply or "有什么我可以帮你的吗？",
                trip_data=None,
                action="chat",
                collected_info=collected_info
            )

        elif action == "confirm_info":
            # 总结确认阶段
            return schemas.ChatResponse(
                success=True,
                reply=reply or "请确认以上信息是否正确~",
                trip_data=None,
                action="confirm_info",
                collected_info=collected_info
            )

        else:
            # 继续询问信息
            return schemas.ChatResponse(
                success=True,
                reply=reply or "请告诉我更多关于你旅行计划的信息吧~",
                trip_data=None,
                action="ask_questions",
                collected_info=collected_info
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return schemas.ChatResponse(
            success=False,
            reply=f"抱歉，处理您的请求时出现了问题：{str(e)}",
            trip_data=None,
            action="error",
            collected_info={}
        )


async def generate_trip_from_chat(message: str, intent: dict, intro_reply: str = "") -> schemas.ChatResponse:
    """从对话生成新行程 - 优化版"""
    city = intent.get("city", "北京")
    days = intent.get("duration", 1) or 1
    keywords = intent.get("keywords", [])

    # 搜索景点
    attractions = await amap_service.search_attractions(
        city=city,
        keywords=keywords if keywords else None,
        page_size=days * 4
    )

    if not attractions:
        return schemas.ChatResponse(
            success=True,
            reply=f"抱歉，我在{city}没有找到相关的景点。你可以换个城市或者更具体地描述你想去的地方。",
            trip_data=None,
            action="no_result"
        )

    # 优化景点顺序
    optimized_attractions = amap_service._optimize_route_order(attractions)

    # 构建每日行程
    trip_days = []
    attractions_per_day = max(3, len(optimized_attractions) // days)

    for day_idx in range(1, days + 1):
        start_idx = (day_idx - 1) * attractions_per_day
        end_idx = start_idx + attractions_per_day if day_idx < days else len(optimized_attractions)
        day_attractions = optimized_attractions[start_idx:end_idx]

        if not day_attractions:
            continue

        # 构建当天的时间表
        day_pois = []
        current_time = 9 * 60  # 从9:00开始
        total_cost = 0

        # 上午景点（9:00 - 12:00）
        morning_attractions = day_attractions[:2] if len(day_attractions) >= 2 else day_attractions[:1]
        for poi in morning_attractions:
            poi_copy = poi.copy()
            poi_copy["start_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
            duration = poi_copy.get("visit_duration", 90)
            current_time += duration
            poi_copy["end_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
            total_cost += poi_copy.get("estimated_cost", 0)
            day_pois.append(poi_copy)
            current_time += 20

        # 午餐
        lunch_time = max(current_time, 12 * 60)
        lunch_location = morning_attractions[-1].get("location") if morning_attractions else None
        if lunch_location:
            nearby_restaurants = await amap_service.search_restaurants_nearby(
                location=lunch_location,
                city=city,
                keywords=keywords if any(k in str(keywords) for k in ["美食", "吃", "餐"]) else None
            )
            if nearby_restaurants:
                lunch = nearby_restaurants[0].copy()
                lunch_duration = lunch.get("visit_duration", 60)
                lunch["start_time"] = f"{lunch_time // 60:02d}:{lunch_time % 60:02d}"
                lunch_time += lunch_duration
                lunch["end_time"] = f"{lunch_time // 60:02d}:{lunch_time % 60:02d}"
                lunch["time_slot"] = "午餐"
                total_cost += lunch.get("estimated_cost", 60)
                day_pois.append(lunch)
                current_time = lunch_time + 15

        # 下午景点
        afternoon_attractions = day_attractions[2:5] if len(day_attractions) > 2 else []
        for poi in afternoon_attractions:
            poi_copy = poi.copy()
            poi_copy["start_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
            duration = poi_copy.get("visit_duration", 90)
            current_time += duration
            poi_copy["end_time"] = f"{current_time // 60:02d}:{current_time % 60:02d}"
            total_cost += poi_copy.get("estimated_cost", 0)
            day_pois.append(poi_copy)
            current_time += 20

        # 晚餐
        dinner_time = max(current_time, 18 * 60)
        dinner_location = afternoon_attractions[-1].get("location") if afternoon_attractions else (morning_attractions[-1].get("location") if morning_attractions else None)
        if dinner_location:
            nearby_restaurants = await amap_service.search_restaurants_nearby(
                location=dinner_location,
                city=city,
                keywords=keywords if any(k in str(keywords) for k in ["美食", "吃", "餐"]) else None
            )
            lunch_name = None
            for p in day_pois:
                if p.get("time_slot") == "午餐":
                    lunch_name = p.get("name")
                    break
            for restaurant in nearby_restaurants:
                if restaurant.get("name") != lunch_name:
                    dinner = restaurant.copy()
                    dinner_duration = dinner.get("visit_duration", 75)
                    dinner["start_time"] = f"{dinner_time // 60:02d}:{dinner_time % 60:02d}"
                    dinner_time += dinner_duration
                    dinner["end_time"] = f"{dinner_time // 60:02d}:{dinner_time % 60:02d}"
                    dinner["time_slot"] = "晚餐"
                    total_cost += dinner.get("estimated_cost", 80)
                    day_pois.append(dinner)
                    current_time = dinner_time
                    break

        # 酒店
        if days > 1 and day_idx < days:
            hotels = await amap_service.search_hotels(city=city, page_size=1)
            if hotels:
                hotel = hotels[0].copy()
                hotel_time = max(current_time + 30, 20 * 60)
                hotel["start_time"] = f"{hotel_time // 60:02d}:{hotel_time % 60:02d}"
                hotel["end_time"] = ""
                hotel["visit_duration"] = 0
                hotel["time_slot"] = "住宿"
                total_cost += hotel.get("estimated_cost", 300)
                day_pois.append(hotel)

        routes = await amap_service.plan_routes(day_pois, city=city)

        trip_items = [schemas.TripItemCreate(
            name=poi.get("name"),
            location=poi.get("location"),
            address=poi.get("address"),
            type=poi.get("type"),
            order=i,
            visit_duration=poi.get("visit_duration", 60),
            cost=poi.get("estimated_cost", 0),
            photos=poi.get("photos", [])
        ) for i, poi in enumerate(day_pois)]

        attraction_names = [p.get("name") for p in day_attractions[:3]]
        summary = f"第{day_idx}天：游览{', '.join(attraction_names)}，预计花费约{total_cost}元/人"

        trip_days.append(schemas.TripDayCreate(
            day_index=day_idx,
            summary=summary,
            items=trip_items,
            routes=routes
        ))

    # 获取天气
    weather = await amap_service.get_weather(city)

    # 生成智囊建议
    insights = None
    try:
        all_pois = []
        for day in trip_days:
            all_pois.extend([item.model_dump() if hasattr(item, 'model_dump') else item.dict() for item in day.items])
        insights_data = await llm_service.generate_travel_insights(city, days, weather, all_pois)
        if insights_data:
            insights = schemas.TripInsights(
                packing_list=insights_data.get("packing_list", []),
                local_delicacies=insights_data.get("local_delicacies", []),
                pro_tips=insights_data.get("pro_tips", [])
            )
    except:
        pass

    trip_data = schemas.TripResponseData(
        trip=schemas.TripCreate(
            title=f"{city} {days}日游",
            city=city,
            days=days,
            status="generated"
        ),
        days=trip_days,
        weather=weather,
        insights=insights
    )

    # 生成回复文本
    poi_names = [item.name for day in trip_days for item in day.items[:3]]
    poi_count = sum(len(day.items) for day in trip_days)
    reply = f"🎉 **{city}{days}日游行程规划完成！**\n\n"
    reply += f"为你精选了 **{poi_count}个地点**，包括：{', '.join(poi_names[:4])}{'...' if len(poi_names) > 4 else ''}\n\n"
    reply += "👆 点击上方「地图」标签查看完整行程，每个景点都支持一键导航和打车哦~"

    return schemas.ChatResponse(
        success=True,
        reply=reply.strip(),
        trip_data=trip_data,
        action="generate_trip",
        collected_info={"city": city, "duration": days}
    )


async def modify_trip_from_chat(message: str, intent: dict, current_trip: dict) -> schemas.ChatResponse:
    """修改现有行程"""
    modification = intent.get("modification", {})
    mod_type = modification.get("type", "")

    # 简单实现：返回提示信息
    # 完整实现需要解析current_trip并进行修改
    reply = "好的，我理解你想要修改行程。目前这个功能还在完善中，你可以尝试重新描述你的需求，我会为你生成新的行程。"

    return schemas.ChatResponse(
        success=True,
        reply=reply,
        trip_data=None,
        action="modify_pending"
    )


@router.post("/chat/stream")
async def chat_stream(request: schemas.ChatRequest):
    """
    流式对话接口 - 支持SSE流式输出和联网搜索
    """
    message = request.message
    current_trip = request.current_trip
    conversation_history = request.conversation_history or []
    collected_info = request.collected_info or {}

    # 构建对话上下文
    context = [{"role": msg.role, "content": msg.content} for msg in conversation_history]
    has_trip = current_trip is not None and current_trip.get("days")

    # 构建对话历史字符串
    context_str = ""
    if context:
        context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context[-6:]])

    # 构建已收集信息的描述
    info_str = ""
    city = collected_info.get("city", "")
    if collected_info:
        info_parts = []
        if city:
            info_parts.append(f"城市: {city}")
        if collected_info.get("duration"):
            info_parts.append(f"天数: {collected_info['duration']}")
        if collected_info.get("travelers"):
            info_parts.append(f"同行人: {collected_info['travelers']}")
        if collected_info.get("preferences"):
            info_parts.append(f"偏好: {', '.join(collected_info['preferences']) if isinstance(collected_info['preferences'], list) else collected_info['preferences']}")
        if info_parts:
            info_str = "已收集的信息：" + "、".join(info_parts)

    # 判断是否需要联网搜索
    search_keywords = ["推荐", "有什么", "哪里", "怎么样", "好玩", "好吃", "攻略", "注意", "天气", "最新", "现在"]
    need_search = any(kw in message for kw in search_keywords) and city

    # 如果需要搜索，先获取搜索结果
    search_context = ""
    if need_search:
        try:
            # 根据问题类型选择搜索方式
            if any(kw in message for kw in ["好吃", "美食", "餐厅", "吃"]):
                search_result = await tavily_service.search_restaurant(city)
            elif any(kw in message for kw in ["景点", "好玩", "去哪"]):
                search_result = await tavily_service.search_attraction(city)
            elif any(kw in message for kw in ["注意", "攻略", "避坑"]):
                search_result = await tavily_service.search_travel_tips(city)
            else:
                search_result = await tavily_service.search_travel_info(city, message)

            if search_result and not search_result.get("error"):
                search_context = tavily_service.format_search_results(search_result)
                print(f"Search results for '{message}': {search_context[:200]}...")
        except Exception as e:
            print(f"Search error: {e}")

    system_prompt = f"""你是"智途无忧"的AI旅行助手小智，性格活泼开朗、见多识广。

【你的人设】
- 热爱旅行，去过很多地方，有丰富的旅行经验
- 说话风格：轻松幽默，像朋友聊天，偶尔用emoji
- 专业但不死板，会给出实用的建议和小tips

【当前对话状态】
用户{'已有行程' if has_trip else '还没有行程'}
{info_str if info_str else ''}

【对话历史】
{context_str if context_str else '（新对话）'}

{f'【参考资料 - 来自网络搜索】{chr(10)}{search_context}{chr(10)}请基于这些信息回答，但用自己的话说，不要生硬引用。' if search_context else ''}

【回复要求】
1. 简洁有趣，控制在2-4句话
2. 给出具体、实用的建议，不要泛泛而谈
3. 如果是推荐类问题，给出2-3个具体选项
4. 适当加入个人经验分享的口吻，如"我上次去的时候..."
5. 可以用emoji但不要太多

直接回复，不要返回JSON。"""

    async def generate():
        try:
            # 如果有搜索结果，先发送搜索结果
            if search_context:
                # 发送搜索结果供前端展示
                search_data = {
                    'search': True,
                    'search_results': search_result.get('results', [])[:5] if search_result else []
                }
                yield f"data: {json.dumps(search_data, ensure_ascii=False)}\n\n"

            async for chunk in llm_service.chat_stream(message, system_prompt):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/search")
async def search(query: str, city: str = None, search_type: str = "general"):
    """
    联网搜索接口

    Args:
        query: 搜索关键词
        city: 城市（可选）
        search_type: 搜索类型 (general, restaurant, attraction, tips)
    """
    try:
        search_query = f"{city} {query}" if city else query

        if search_type == "restaurant":
            result = await tavily_service.search_restaurant(city or "", query)
        elif search_type == "attraction":
            result = await tavily_service.search_attraction(city or "", query)
        elif search_type == "tips":
            result = await tavily_service.search_travel_tips(city or query)
        else:
            result = await tavily_service.search(search_query)

        return {
            "success": True,
            "data": result,
            "formatted": tavily_service.format_search_results(result)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


