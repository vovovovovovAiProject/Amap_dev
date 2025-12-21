from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    
    trips = relationship("Trip", back_populates="owner")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    city = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days = Column(Integer, default=1)
    budget = Column(Float, nullable=True)
    status = Column(String, default="planned")
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="trips")
    trip_days = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan")

class TripDay(Base):
    __tablename__ = "trip_days"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    day_index = Column(Integer)  # 第几天，从1开始
    date = Column(Date, nullable=True)
    summary = Column(String, nullable=True) # 每日行程摘要
    routes = Column(JSON, nullable=True)  # 存储路线数据

    trip = relationship("Trip", back_populates="trip_days")
    items = relationship("TripItem", back_populates="trip_day", cascade="all, delete-orphan")

class TripItem(Base):
    __tablename__ = "trip_items"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id"))
    poi_id = Column(String, nullable=True)
    name = Column(String)
    address = Column(String, nullable=True)
    location = Column(String)  # 经纬度
    type = Column(String, nullable=True)
    order = Column(Integer)  # 排序
    visit_duration = Column(Integer, default=60)  # 游览时长(分钟)
    cost = Column(Float, default=0.0)
    photos = Column(JSON, nullable=True) # 存储图片URL列表
    
    trip_day = relationship("TripDay", back_populates="items")
