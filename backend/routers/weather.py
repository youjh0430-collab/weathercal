"""
Role: 날씨 조회 API 엔드포인트
Key Features: 월별 날씨 목록, 특정일 날씨 상세
Dependencies: services.weather_service
"""
from fastapi import APIRouter, HTTPException
from services.weather_service import get_weather_for_month, get_weather_for_date

router = APIRouter(prefix="/api/weather", tags=["날씨"])


@router.get("")
def get_monthly_weather(month: str):
    """월별 날씨 조회 — month: '2026-03' 형식"""
    return get_weather_for_month(month)


@router.get("/{date}")
def get_daily_weather(date: str):
    """특정일 날씨 상세"""
    weather = get_weather_for_date(date)
    if not weather:
        raise HTTPException(status_code=404, detail="해당 날짜의 날씨 정보가 없습니다")
    return weather
