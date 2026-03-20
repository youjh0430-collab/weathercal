"""
Role: 특정일 브리핑 API — 날씨 + 일정(경고 포함) + 활동 추천을 통합 반환
Key Features: 날씨 경고, 활동 추천, 일정 통합
Dependencies: services (weather, warning, recommend), database
"""
from fastapi import APIRouter
from database import get_connection
from services.weather_service import get_weather_for_date
from services.warning_service import get_warnings
from services.recommend_service import get_recommendations

router = APIRouter(prefix="/api/briefing", tags=["브리핑"])


@router.get("/{date}")
def get_briefing(date: str):
    """특정일 브리핑 — 날씨 + 일정 + 경고 + 추천"""
    weather = get_weather_for_date(date)

    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM schedules WHERE date = ? ORDER BY time", (date,)
    ).fetchall()
    conn.close()

    schedules = []
    for row in rows:
        warnings = get_warnings(row["category"], weather) if weather else []
        schedules.append({
            "id": row["id"],
            "title": row["title"],
            "time": row["time"],
            "category": row["category"],
            "memo": row["memo"],
            "warnings": warnings
        })

    recommendations = get_recommendations(weather) if weather else []

    return {
        "date": date,
        "weather": weather,
        "schedules": schedules,
        "recommendations": recommendations
    }
