"""
Role: 날씨 조회 API 엔드포인트
Key Features: 월별 날씨 목록, 특정일 날씨 상세, 도시 목록
Dependencies: services.weather_service, data.stations
"""
from fastapi import APIRouter, HTTPException
from services.weather_service import get_weather_for_month, get_weather_for_date
from data.stations import get_station_names

router = APIRouter(prefix="/api/weather", tags=["날씨"])


@router.get("/stations/list")
def get_stations():
    """사용 가능한 도시 목록 반환"""
    return get_station_names()


@router.get("")
def get_monthly_weather(month: str, station: str = "서울"):
    """월별 날씨 조회"""
    return get_weather_for_month(month, station)


@router.get("/{date}")
def get_daily_weather(date: str, station: str = "서울"):
    """특정일 날씨 상세"""
    weather = get_weather_for_date(date, station)
    if not weather:
        raise HTTPException(status_code=404, detail="해당 날짜의 날씨 정보가 없습니다")
    return weather
