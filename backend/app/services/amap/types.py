from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field, field_validator

def handle_empty_list(v):
    if isinstance(v, list) and len(v) == 0:
        return ""
    return v

def handle_empty_list_none(v):
    if isinstance(v, list) and len(v) == 0:
        return None
    return v

def handle_empty_list_dict(v):
    if isinstance(v, list) and len(v) == 0:
        return {}
    return v

class AmapResponse(BaseModel):
    """
    高德API通用响应模型
    """
    status: str = Field(..., description="返回结果状态值，1：成功，0：失败")
    info: str = Field(..., description="返回状态说明，status为0时，info返回错误原因")
    infocode: str = Field(..., description="返回状态码")
    count: Optional[str] = Field(None, description="返回结果总数目")
    
    class Config:
        extra = "allow"

class GeoCode(BaseModel):
    formatted_address: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    township: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    adcode: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None

    @field_validator('*', mode='before')
    def check_empty_list(cls, v):
        return handle_empty_list(v)

class ReGeoCode(BaseModel):
    formatted_address: str
    addressComponent: Dict[str, Any]

class Poi(BaseModel):
    id: str
    name: str
    type: str
    typecode: str
    biz_type: Union[str, List]
    address: Union[str, List]
    location: str
    tel: Union[str, List]
    distance: Optional[str] = None
    biz_ext: Optional[Dict[str, Any]] = None
    pcode: Optional[str] = None
    pname: Optional[str] = None
    cityname: Optional[str] = None
    citycode: Optional[str] = None
    adname: Optional[str] = None
    adcode: Optional[str] = None
    photos: Optional[List[Dict[str, Any]]] = None

    @field_validator('distance', 'pcode', 'pname', 'cityname', 'citycode', 'adname', 'adcode', mode='before')
    def check_empty_list_str(cls, v):
        return handle_empty_list(v)

    @field_validator('biz_ext', mode='before')
    def check_empty_list_dict(cls, v):
        return handle_empty_list_dict(v)

class District(BaseModel):
    citycode: Union[str, List]
    adcode: str
    name: str
    polyline: Optional[str] = None
    center: str
    level: str
    districts: List['District'] = []

    @field_validator('polyline', mode='before')
    def check_empty_list(cls, v):
        return handle_empty_list(v)

class WeatherInfo(BaseModel):
    province: str
    city: str
    adcode: str
    weather: str
    temperature: str
    winddirection: str
    windpower: str
    humidity: str
    reporttime: str

class IPInfo(BaseModel):
    province: str
    city: str
    adcode: str
    rectangle: str

    @field_validator('*', mode='before')
    def check_empty_list(cls, v):
        return handle_empty_list(v)

