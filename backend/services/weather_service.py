"""
Role: 기상청 3개 API 호출 + 통합 날씨 데이터 제공
Key Features: ASOS(과거), 단기예보(오늘~3일), 중기예보(4~10일), 지역별 조회, DB 캐시
Dependencies: httpx, database, data.stations
Notes: 기상청 API는 인코딩된 서비스키를 URL에 직접 포함해야 함
"""
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_connection
from data.stations import get_station

load_dotenv()

API_KEY = os.getenv("KMA_API_KEY")
ASOS_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
VILAGE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
MID_TA_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
MID_LAND_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"


def _cloud_to_condition(avg_tca, sum_rn):
    """전운량과 강수량으로 날씨 상태 결정"""
    if sum_rn and float(sum_rn) > 0:
        return "비"
    if avg_tca is None:
        return "맑음"
    try:
        tca = float(avg_tca)
    except (ValueError, TypeError):
        return "흐림"
    if tca <= 2:
        return "맑음"
    elif tca <= 5:
        return "구름많음"
    else:
        return "흐림"


def _condition_to_icon(condition):
    """한국어 condition을 아이콘 코드로 변환"""
    mapping = {
        "맑음": "sunny",
        "구름많음": "partly_cloudy",
        "흐림": "cloudy",
        "비": "rain",
        "눈": "snow",
        "비/눈": "sleet",
    }
    return mapping.get(condition, "cloudy")


def _sky_pty_to_condition(sky: str, pty: str):
    """단기예보 SKY(하늘상태) + PTY(강수형태) → 한국어 condition"""
    pty_map = {"1": "비", "2": "비/눈", "3": "눈", "5": "비", "6": "비/눈", "7": "눈"}
    if pty in pty_map:
        return pty_map[pty]
    sky_map = {"1": "맑음", "3": "구름많음", "4": "흐림"}
    return sky_map.get(sky, "흐림")


def _mid_sky_to_condition(sky_text: str):
    """중기예보 하늘상태 문자열 → 한국어 condition"""
    if not sky_text:
        return "흐림"
    if "맑음" in sky_text:
        return "맑음"
    if "구름많음" in sky_text:
        return "구름많음"
    if "흐림" in sky_text:
        return "흐림"
    if "비" in sky_text and "눈" in sky_text:
        return "비/눈"
    if "비" in sky_text or "소나기" in sky_text:
        return "비"
    if "눈" in sky_text:
        return "눈"
    return "흐림"


def _get_base_datetime():
    """단기예보 발표 시각 계산 — 가장 최근 발표 시각 반환"""
    now = datetime.now()
    base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
    adjusted = now - timedelta(minutes=10)
    current_hhmm = adjusted.strftime("%H%M")
    base_date = adjusted.strftime("%Y%m%d")
    base_time = "2300"

    for bt in base_times:
        if current_hhmm >= bt:
            base_time = bt
        else:
            break

    if current_hhmm < "0210":
        base_date = (adjusted - timedelta(days=1)).strftime("%Y%m%d")
        base_time = "2300"

    return base_date, base_time


def fetch_asos(station_name: str, start_date: str, end_date: str):
    """ASOS 일자료 조회 — 과거~어제 실측 날씨"""
    if not API_KEY:
        print("[경고] KMA_API_KEY가 설정되지 않았습니다")
        return []

    station = get_station(station_name)
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "60",
        "pageNo": "1",
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "startDt": start_date.replace("-", ""),
        "endDt": end_date.replace("-", ""),
        "stnIds": station["stn_id"],
    }

    try:
        response = httpx.get(ASOS_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[에러] ASOS API 호출 실패: {e}")
        return []

    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    result = []
    for item in items:
        date_str = item.get("tm", "")
        avg_ta = item.get("avgTa")
        min_ta = item.get("minTa")
        max_ta = item.get("maxTa")
        avg_rhm = item.get("avgRhm")
        avg_ws = item.get("avgWs")
        sum_rn = item.get("sumRn")
        avg_tca = item.get("avgTca")

        condition = _cloud_to_condition(avg_tca, sum_rn)

        result.append({
            "date": date_str,
            "temperature": float(avg_ta) if avg_ta else None,
            "temp_min": float(min_ta) if min_ta else None,
            "temp_max": float(max_ta) if max_ta else None,
            "condition": condition,
            "humidity": round(float(avg_rhm)) if avg_rhm else None,
            "wind_speed": round(float(avg_ws), 1) if avg_ws else None,
            "icon": _condition_to_icon(condition),
            "is_past": True,
        })

    return result


def fetch_vilage_forecast(station_name: str):
    """단기예보 조회 — 오늘~3일 후"""
    if not API_KEY:
        return []

    station = get_station(station_name)
    base_date, base_time = _get_base_datetime()

    params = {
        "serviceKey": API_KEY,
        "numOfRows": "1000",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": station["nx"],
        "ny": station["ny"],
    }

    try:
        response = httpx.get(VILAGE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[에러] 단기예보 API 호출 실패: {e}")
        return []

    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    # 날짜+시간별로 그룹핑
    daily = {}
    for item in items:
        fc_date = item["fcstDate"]
        fc_time = item["fcstTime"]
        category = item["category"]
        value = item["fcstValue"]

        if fc_date not in daily:
            daily[fc_date] = {}
        if fc_time not in daily[fc_date]:
            daily[fc_date][fc_time] = {}
        daily[fc_date][fc_time][category] = value

    # 각 날짜에서 정오(1200)에 가장 가까운 시간의 대표값 추출
    today = datetime.now().date()
    result = []
    for date_str, times in sorted(daily.items()):
        best_time = min(times.keys(), key=lambda t: abs(int(t) - 1200))
        vals = times[best_time]

        sky = vals.get("SKY", "1")
        pty = vals.get("PTY", "0")
        condition = _sky_pty_to_condition(sky, pty)

        temp = vals.get("TMP") or vals.get("T1H")
        humidity = vals.get("REH")
        wind = vals.get("WSD")

        # TMN(최저)은 0600, TMX(최고)는 1500에 발표 — 날짜 내 전체 시간에서 탐색
        temp_min = None
        temp_max = None
        for t, t_vals in times.items():
            if "TMN" in t_vals and t_vals["TMN"]:
                temp_min = float(t_vals["TMN"])
            if "TMX" in t_vals and t_vals["TMX"]:
                temp_max = float(t_vals["TMX"])

        # TMN/TMX가 없으면 각 시간대 TMP 값에서 최소/최고 계산으로 보완
        if temp_min is None or temp_max is None:
            all_temps = []
            for t, t_vals in times.items():
                t_val = t_vals.get("TMP") or t_vals.get("T1H")
                if t_val:
                    try:
                        all_temps.append(float(t_val))
                    except (ValueError, TypeError):
                        pass
            if all_temps:
                if temp_min is None:
                    temp_min = min(all_temps)
                if temp_max is None:
                    temp_max = max(all_temps)

        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        row_date = datetime.strptime(date_str, "%Y%m%d").date()

        result.append({
            "date": formatted_date,
            "temperature": float(temp) if temp else None,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "condition": condition,
            "humidity": round(float(humidity)) if humidity else None,
            "wind_speed": round(float(wind), 1) if wind else None,
            "icon": _condition_to_icon(condition),
            "is_past": row_date < today,
        })

    return result


def fetch_mid_forecast(station_name: str):
    """중기예보 조회 — 4일~10일 후 기온 + 하늘상태"""
    if not API_KEY:
        return []

    station = get_station(station_name)
    now = datetime.now()

    if now.hour < 6:
        tm_fc = (now - timedelta(days=1)).strftime("%Y%m%d") + "1800"
    elif now.hour < 18:
        tm_fc = now.strftime("%Y%m%d") + "0600"
    else:
        tm_fc = now.strftime("%Y%m%d") + "1800"

    ta_params = {
        "serviceKey": API_KEY,
        "numOfRows": "10",
        "pageNo": "1",
        "dataType": "JSON",
        "regId": station["mid_ta_id"],
        "tmFc": tm_fc,
    }

    land_params = {
        "serviceKey": API_KEY,
        "numOfRows": "10",
        "pageNo": "1",
        "dataType": "JSON",
        "regId": station["mid_land_id"],
        "tmFc": tm_fc,
    }

    try:
        ta_res = httpx.get(MID_TA_URL, params=ta_params, timeout=15)
        ta_res.raise_for_status()
        ta_data = ta_res.json()

        land_res = httpx.get(MID_LAND_URL, params=land_params, timeout=15)
        land_res.raise_for_status()
        land_data = land_res.json()
    except Exception as e:
        print(f"[에러] 중기예보 API 호출 실패: {e}")
        return []

    ta_items = ta_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    land_items = land_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    ta_item = ta_items[0] if ta_items else {}
    land_item = land_items[0] if land_items else {}

    today = datetime.now().date()
    result = []
    for day_offset in range(4, 11):
        target_date = today + timedelta(days=day_offset)
        date_str = target_date.isoformat()

        min_temp = ta_item.get(f"taMin{day_offset}")
        max_temp = ta_item.get(f"taMax{day_offset}")

        if min_temp is not None and max_temp is not None:
            avg_temp = round((float(min_temp) + float(max_temp)) / 2, 1)
        else:
            avg_temp = None

        if day_offset <= 7:
            sky_text = land_item.get(f"wf{day_offset}Am", "") or land_item.get(f"wf{day_offset}Pm", "")
        else:
            sky_text = land_item.get(f"wf{day_offset}", "")

        condition = _mid_sky_to_condition(sky_text)

        t_min = float(min_temp) if min_temp is not None else None
        t_max = float(max_temp) if max_temp is not None else None

        result.append({
            "date": date_str,
            "temperature": avg_temp,
            "temp_min": t_min,
            "temp_max": t_max,
            "condition": condition,
            "humidity": None,
            "wind_speed": None,
            "icon": _condition_to_icon(condition),
            "is_past": False,
        })

    return result


def get_weather_for_month(month: str, station_name: str = "서울"):
    """월별 날씨 조회 — 캐시 확인 후 필요 시 API 호출"""
    conn = get_connection()
    today = datetime.now().date()

    # 캐시 갱신 필요 여부 확인
    cached_today = conn.execute(
        "SELECT fetched_at FROM weather_cache WHERE date = ? AND station = ?",
        (today.isoformat(), station_name)
    ).fetchone()

    need_refresh = True
    if cached_today and cached_today["fetched_at"]:
        fetched = datetime.fromisoformat(cached_today["fetched_at"])
        if (datetime.now() - fetched).total_seconds() < 10800:
            need_refresh = False

    if need_refresh:
        _refresh_weather_cache(station_name)

    rows = conn.execute(
        "SELECT * FROM weather_cache WHERE date LIKE ? AND station = ? ORDER BY date",
        (f"{month}%", station_name)
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        result.append({
            "date": row["date"],
            "temperature": row["temperature"],
            "temp_min": row["temp_min"],
            "temp_max": row["temp_max"],
            "condition": row["condition"],
            "humidity": row["humidity"],
            "wind_speed": row["wind_speed"],
            "icon": row["icon"],
            "is_past": row_date < today,
        })

    return result


def get_weather_for_date(date: str, station_name: str = "서울"):
    """특정일 날씨 상세 조회"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM weather_cache WHERE date = ? AND station = ?",
        (date, station_name)
    ).fetchone()
    conn.close()

    if not row:
        return None

    today = datetime.now().date()
    row_date = datetime.strptime(date, "%Y-%m-%d").date()
    return {
        "date": row["date"],
        "temperature": row["temperature"],
        "temp_min": row["temp_min"],
        "temp_max": row["temp_max"],
        "condition": row["condition"],
        "humidity": row["humidity"],
        "wind_speed": row["wind_speed"],
        "icon": row["icon"],
        "is_past": row_date < today,
    }


def _refresh_weather_cache(station_name: str):
    """3개 API 호출 후 캐시에 저장"""
    conn = get_connection()
    today = datetime.now().date()

    # 1. ASOS — 이번 달 1일 ~ 어제
    month_start = today.replace(day=1)
    yesterday = today - timedelta(days=1)
    if yesterday >= month_start:
        asos_data = fetch_asos(station_name, month_start.isoformat(), yesterday.isoformat())
        for item in asos_data:
            # 과거 데이터는 이미 캐시되어 있으면 갱신하지 않음
            existing = conn.execute(
                "SELECT 1 FROM weather_cache WHERE date = ? AND station = ?",
                (item["date"], station_name)
            ).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO weather_cache (date, station, temperature, temp_min, temp_max, condition, humidity, wind_speed, icon, fetched_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
                    (item["date"], station_name, item["temperature"], item["temp_min"], item["temp_max"],
                     item["condition"], item["humidity"], item["wind_speed"], item["icon"])
                )

    # 2. 단기예보 — 오늘~3일 후
    vilage_data = fetch_vilage_forecast(station_name)
    for item in vilage_data:
        conn.execute(
            """INSERT OR REPLACE INTO weather_cache (date, station, temperature, temp_min, temp_max, condition, humidity, wind_speed, icon, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
            (item["date"], station_name, item["temperature"], item["temp_min"], item["temp_max"],
             item["condition"], item["humidity"], item["wind_speed"], item["icon"])
        )

    # 3. 중기예보 — 4일~10일 후
    mid_data = fetch_mid_forecast(station_name)
    for item in mid_data:
        conn.execute(
            """INSERT OR REPLACE INTO weather_cache (date, station, temperature, temp_min, temp_max, condition, humidity, wind_speed, icon, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
            (item["date"], station_name, item["temperature"], item["temp_min"], item["temp_max"],
             item["condition"], item["humidity"], item["wind_speed"], item["icon"])
        )

    conn.commit()
    conn.close()
