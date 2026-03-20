"""
Role: 날씨 조건에 맞는 활동 추천을 DB에서 조회
Key Features: temp_range 변환, conditions JSON 매칭
Dependencies: database
"""
import json
from database import get_connection


def get_temp_range(temp: float) -> str:
    """기온을 temp_range 문자열로 변환"""
    if temp <= -10:
        return "freezing"
    elif temp <= 5:
        return "cold"
    elif temp <= 15:
        return "cool"
    elif temp <= 25:
        return "comfortable"
    elif temp <= 33:
        return "warm"
    else:
        return "hot"


def get_recommendations(weather: dict, limit: int = 5) -> list[str]:
    """날씨 데이터로 활동 추천 목록 반환"""
    if not weather:
        return []

    condition = weather.get("condition", "")
    temp = weather.get("temperature")
    if temp is None:
        return []

    temp_range = get_temp_range(temp)

    conn = get_connection()
    rows = conn.execute(
        "SELECT name, conditions FROM activities WHERE is_active = 1"
    ).fetchall()
    conn.close()

    matched = []
    for row in rows:
        try:
            conds = json.loads(row["conditions"])
        except (json.JSONDecodeError, TypeError):
            continue

        weather_list = conds.get("weather")
        if weather_list and condition not in weather_list:
            continue

        cond_temp = conds.get("temp_range")
        if cond_temp and cond_temp != temp_range:
            continue

        matched.append(row["name"])

    return matched[:limit]
