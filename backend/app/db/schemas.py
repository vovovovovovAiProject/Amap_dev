from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# Trip Item Schemas
class TripItemBase(BaseModel):
    poi_id: Optional[str] = None
    name: str
    location: str
    address: Optional[str] = None
    type: Optional[str] = None
    order: int
    visit_duration: int = 60
    cost: float = 0.0
    photos: Optional[List[dict]] = []

class TripItemCreate(TripItemBase):
    pass

class TripItem(TripItemBase):
    id: int
    trip_day_id: int
    class Config:
        from_attributes = True

# Trip Day Schemas
class TripDayBase(BaseModel):
    day_index: int
    date: Optional[date] = None
    summary: Optional[str] = None # 每日行程描述

class TripDayCreate(TripDayBase):
    items: List[TripItemCreate] = []
    routes: List[dict] = [] # 包含从后端计算的路线信息，用于前端展示

class TripDay(TripDayBase):
    id: int
    trip_id: int
    items: List[TripItem] = []
    class Config:
        from_attributes = True

# Trip Schemas
class TripBase(BaseModel):
    title: str
    city: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: int = 1
    budget: Optional[float] = None
    status: str = "planned"

class TripCreate(TripBase):
    pass

class Trip(TripBase):
    id: int
    user_id: Optional[int] = None
    trip_days: List[TripDay] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# API Interaction Schemas
class TripRequest(BaseModel):
    user_input: str
    start_location: Optional[str] = None

class TripInsights(BaseModel):
    packing_list: List[str] = []
    local_delicacies: List[str] = []
    pro_tips: List[str] = []

class TripCreateWithDays(TripBase):
    trip_days: List[TripDayCreate] = []

class TripResponseData(BaseModel):
    trip: TripCreate
    days: List[TripDayCreate]
    weather: Optional[dict] = None
    insights: Optional[TripInsights] = None

class TripResponse(BaseModel):
    success: bool
    message: str
    data: Optional[TripResponseData] = None


# Chat Schemas
class ChatMessage(BaseModel):
    role: str  # user 或 assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    current_trip: Optional[dict] = None
    conversation_history: Optional[List[ChatMessage]] = []
    collected_info: Optional[dict] = {}


class ChatResponse(BaseModel):
    success: bool
    reply: str
    trip_data: Optional[TripResponseData] = None
    action: Optional[str] = None  # ask_questions, generate_trip, modify_trip, info
    collected_info: Optional[dict] = None
