"""
Role: 날씨 조건에 맞는 활동 추천을 DB에서 조회
Key Features: temp_range 변환, conditions JSON 매칭, 계절 필터링, 날짜별 셔플
Dependencies: database
"""
import json
import random
from datetime import datetime
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


def get_recommendations(weather: dict, limit: int = 2, date: str = None) -> list[str]:
    """날씨 데이터로 활동 추천 목록 반환 — 계절 필터링 포함"""
    if not weather:
        return []

    condition = weather.get("condition", "")
    temp = weather.get("temperature")
    if temp is None:
        return []

    # 조회 날짜의 월 추출 (계절 필터링용)
    if date:
        try:
            current_month = int(date.split("-")[1])
        except (IndexError, ValueError):
            current_month = datetime.now().month
    else:
        current_month = datetime.now().month

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

        # 계절 필터링 — months가 지정된 경우 현재 월이 포함되어야 함
        months = conds.get("months")
        if months and current_month not in months:
            continue

        matched.append(row["name"])

    # 날짜를 시드로 사용하여 날짜별로 다른 순서로 셔플
    if date:
        random.seed(date)
    random.shuffle(matched)

    return matched[:limit]
