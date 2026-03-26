"""
Role: API 요청/응답 데이터 스키마 정의
Key Features: 일정 CRUD 스키마, 날씨 스키마, 브리핑 스키마
Dependencies: pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional


class ScheduleCreate(BaseModel):
    """일정 등록/수정 요청 — 입력 길이 및 형식 제한"""
    title: str = Field(..., min_length=1, max_length=200)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    category: str = Field("indoor", pattern=r"^(indoor|outdoor)$")
    memo: Optional[str] = Field(None, max_length=1000)


class ScheduleResponse(BaseModel):
    """일정 응답"""
    id: int
    title: str
    date: str
    time: Optional[str]
    category: str
    memo: Optional[str]
    created_at: str


class WeatherResponse(BaseModel):
    """날씨 응답"""
    date: str
    temperature: Optional[float]
    condition: Optional[str]
    humidity: Optional[int]
    wind_speed: Optional[float]
    icon: Optional[str]
    is_past: bool = False


class ScheduleWithWarnings(BaseModel):
    """경고가 포함된 일정"""
    id: int
    title: str
    time: Optional[str]
    category: str
    warnings: list[str]


class BriefingResponse(BaseModel):
    """특정일 브리핑 응답"""
    date: str
    weather: Optional[WeatherResponse]
    schedules: list[ScheduleWithWarnings]
    recommendations: list[str]
