"""
Role: OpenWeatherMap API 호출 + 3시간 단위 → 일별 대표값 변환 + DB 캐시
Key Features: 5일 예보 조회, 정오 기준 대표값 추출, 3시간 TTL 캐시
Dependencies: httpx, database
Notes: 무료 플랜 기준 — 분당 60회 호출 제한
"""
import httpx
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = 37.5665
LON = 126.9780
BASE_URL = "https://api.openweathermap.org/data/2.5"


def fetch_forecast():
    """OpenWeatherMap 5일 예보 API 호출 → 일별 대표값 리스트 반환"""
    if not API_KEY:
        print("[경고] OPENWEATHER_API_KEY가 설정되지 않았습니다")
        return []

    url = f"{BASE_URL}/forecast"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": API_KEY,
        "units": "metric",
        "lang": "kr"
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[에러] 날씨 API 호출 실패: {e}")
        return []

    daily = {}
    for item in data.get("list", []):
        dt_text = item["dt_txt"]
        date_str = dt_text.split(" ")[0]
        hour = int(dt_text.split(" ")[1].split(":")[0])

        if date_str not in daily:
            daily[date_str] = {"items": [], "noon_diff": 99, "noon_item": None}

        daily[date_str]["items"].append(item)

        diff = abs(hour - 12)
        if diff < daily[date_str]["noon_diff"]:
            daily[date_str]["noon_diff"] = diff
            daily[date_str]["noon_item"] = item

    result = []
    for date_str, info in daily.items():
        item = info["noon_item"]
        if not item:
            continue
        result.append({
            "date": date_str,
            "temperature": round(item["main"]["temp"], 1),
            "condition": item["weather"][0]["main"],
            "humidity": item["main"]["humidity"],
            "wind_speed": round(item["wind"]["speed"], 1),
            "icon": item["weather"][0]["icon"]
        })

    return result


def get_weather_for_month(month: str):
    """월별 날씨 조회 — 캐시 확인 후 필요 시 API 호출"""
    conn = get_connection()
    today = datetime.now().date()

    cached_today = conn.execute(
        "SELECT fetched_at FROM weather_cache WHERE date = ?",
        (today.isoformat(),)
    ).fetchone()

    need_refresh = True
    if cached_today and cached_today["fetched_at"]:
        fetched = datetime.fromisoformat(cached_today["fetched_at"])
        if (datetime.now() - fetched).total_seconds() < 10800:
            need_refresh = False

    if need_refresh:
        forecasts = fetch_forecast()
        for f in forecasts:
            conn.execute(
                """INSERT OR REPLACE INTO weather_cache (date, temperature, condition, humidity, wind_speed, icon, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
                (f["date"], f["temperature"], f["condition"], f["humidity"], f["wind_speed"], f["icon"])
            )
        conn.commit()

    rows = conn.execute(
        "SELECT * FROM weather_cache WHERE date LIKE ? ORDER BY date",
        (f"{month}%",)
    ).fetchall()
    conn.close()

    result = []
    max_future = today + timedelta(days=5)
    for row in rows:
        row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        result.append({
            "date": row["date"],
            "temperature": row["temperature"],
            "condition": row["condition"],
            "humidity": row["humidity"],
            "wind_speed": row["wind_speed"],
            "icon": row["icon"],
            "is_past": row_date < today
        })

    return result


def get_weather_for_date(date: str):
    """특정일 날씨 상세 조회"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM weather_cache WHERE date = ?", (date,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    today = datetime.now().date()
    row_date = datetime.strptime(date, "%Y-%m-%d").date()
    return {
        "date": row["date"],
        "temperature": row["temperature"],
        "condition": row["condition"],
        "humidity": row["humidity"],
        "wind_speed": row["wind_speed"],
        "icon": row["icon"],
        "is_past": row_date < today
    }
