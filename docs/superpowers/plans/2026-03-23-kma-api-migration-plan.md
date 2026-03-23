# 기상청 API 교체 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenWeatherMap API를 기상청 3개 API(ASOS, 단기예보, 중기예보)로 교체하고, 지역 선택 기능을 추가한다.

**Architecture:** `weather_service.py`를 전체 재작성하여 기상청 3개 API를 호출하고 통합 형식으로 변환한다. 지역 데이터는 `stations.py` 딕셔너리로 관리하며, 프론트엔드 헤더에 드롭다운을 추가하여 지역 변경 시 캘린더를 다시 렌더링한다.

**Tech Stack:** Python 3.11+, FastAPI, httpx, SQLite, vanilla HTML/CSS/JS

**Spec:** `docs/superpowers/specs/2026-03-23-kma-api-migration-design.md`

---

## 파일 구조

```
03_날씨/
├── .env                                # KMA_API_KEY로 변경
├── backend/
│   ├── data/
│   │   ├── stations.py                 # [신규] 도시별 관측소/격자/지역코드
│   │   ├── seed.py                     # [수정] conditions 한국어로 변경
│   │   └── keywords.py                 # 변경 없음
│   ├── database.py                     # [수정] weather_cache에 station 컬럼 추가
│   ├── services/
│   │   ├── weather_service.py          # [전체 재작성] 기상청 3개 API 호출 + 통합
│   │   ├── warning_service.py          # [수정] condition 한국어 매핑
│   │   └── recommend_service.py        # 변경 없음 (condition은 DB에서 비교)
│   ├── routers/
│   │   ├── weather.py                  # [수정] station 파라미터 추가
│   │   └── briefing.py                 # [수정] station 파라미터 추가
│   └── main.py                         # 변경 없음
├── frontend/
│   ├── index.html                      # [수정] 지역 드롭다운 추가
│   ├── css/style.css                   # [수정] 드롭다운 스타일
│   └── js/
│       ├── api.js                      # [수정] station 파라미터 전달
│       ├── calendar.js                 # [수정] 아이콘 매핑 + 지역 변경 이벤트
│       └── briefing.js                 # [수정] 아이콘 매핑 변경
```

---

## Task 1: 환경 변수 및 DB 스키마 변경

**Files:**
- Modify: `.env`
- Modify: `backend/database.py`

- [ ] **Step 1: .env 파일 변경**

기존 OpenWeatherMap 키를 기상청 키로 교체한다.

```
KMA_API_KEY=44aea3cdb03e364415439c0c96cb4c89a9510fc5c9fa811eeb157dc798919f72
```

기존 `OPENWEATHER_API_KEY` 행은 삭제한다.

- [ ] **Step 2: database.py 수정 — weather_cache 테이블에 station 컬럼 추가**

`database.py`의 `init_db()` 함수에서 `weather_cache` 테이블 생성문을 변경한다.

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_cache (
        date TEXT NOT NULL,
        station TEXT NOT NULL DEFAULT '서울',
        temperature REAL,
        condition TEXT,
        humidity REAL,
        wind_speed REAL,
        icon TEXT,
        fetched_at TEXT DEFAULT (datetime('now', 'localtime')),
        PRIMARY KEY (date, station)
    )
""")
```

기존 `id INTEGER PRIMARY KEY AUTOINCREMENT`와 `date TEXT NOT NULL UNIQUE`를 복합 PRIMARY KEY로 변경한다.

- [ ] **Step 3: 기존 DB 파일 삭제**

스키마가 변경되었으므로 기존 `weathercal.db`를 삭제하여 새로 생성되도록 한다.

```bash
rm backend/weathercal.db
```

- [ ] **Step 4: 동작 확인**

```bash
cd backend && python -c "from database import init_db; init_db(); print('DB 초기화 성공')"
```

- [ ] **Step 5: 커밋**

```bash
git add .env backend/database.py
git commit -m "DB 스키마 변경 — weather_cache에 station 컬럼 추가, API 키를 기상청으로 교체"
```

---

## Task 2: 지역 데이터 파일 생성

**Files:**
- Create: `backend/data/stations.py`

- [ ] **Step 1: stations.py 작성**

```python
"""
Role: 도시별 기상청 API 파라미터 매핑
Key Features: ASOS 관측소 번호, 단기예보 격자좌표, 중기예보 지역코드
Dependencies: 없음
"""

STATIONS = {
    "서울": {"stn_id": "108", "nx": 60, "ny": 127, "mid_ta_id": "11B10101", "mid_land_id": "11B00000"},
    "부산": {"stn_id": "159", "nx": 98, "ny": 76, "mid_ta_id": "11H20201", "mid_land_id": "11H20000"},
    "대구": {"stn_id": "143", "nx": 89, "ny": 90, "mid_ta_id": "11H10701", "mid_land_id": "11H10000"},
    "인천": {"stn_id": "112", "nx": 55, "ny": 124, "mid_ta_id": "11B20201", "mid_land_id": "11B00000"},
    "광주": {"stn_id": "156", "nx": 58, "ny": 74, "mid_ta_id": "11F20501", "mid_land_id": "11F20000"},
    "대전": {"stn_id": "133", "nx": 67, "ny": 100, "mid_ta_id": "11C20401", "mid_land_id": "11C20000"},
    "울산": {"stn_id": "152", "nx": 102, "ny": 84, "mid_ta_id": "11H20101", "mid_land_id": "11H20000"},
    "세종": {"stn_id": "129", "nx": 66, "ny": 103, "mid_ta_id": "11C20404", "mid_land_id": "11C20000"},
    "제주": {"stn_id": "184", "nx": 52, "ny": 38, "mid_ta_id": "11G00201", "mid_land_id": "11G00000"},
    "수원": {"stn_id": "119", "nx": 60, "ny": 121, "mid_ta_id": "11B20601", "mid_land_id": "11B00000"},
    "춘천": {"stn_id": "101", "nx": 73, "ny": 134, "mid_ta_id": "11D10301", "mid_land_id": "11D10000"},
    "청주": {"stn_id": "131", "nx": 69, "ny": 106, "mid_ta_id": "11C10301", "mid_land_id": "11C10000"},
    "전주": {"stn_id": "146", "nx": 63, "ny": 89, "mid_ta_id": "11F10201", "mid_land_id": "11F10000"},
    "포항": {"stn_id": "138", "nx": 102, "ny": 94, "mid_ta_id": "11H10201", "mid_land_id": "11H10000"},
    "창원": {"stn_id": "155", "nx": 89, "ny": 77, "mid_ta_id": "11H20301", "mid_land_id": "11H20000"},
    "강릉": {"stn_id": "105", "nx": 92, "ny": 131, "mid_ta_id": "11D20501", "mid_land_id": "11D20000"},
}


def get_station(name: str) -> dict:
    """도시명으로 관측소 정보 반환 — 없으면 서울 기본값"""
    return STATIONS.get(name, STATIONS["서울"])


def get_station_names() -> list[str]:
    """드롭다운용 도시명 목록 반환"""
    return list(STATIONS.keys())
```

- [ ] **Step 2: import 확인**

```bash
cd backend && python -c "from data.stations import get_station, get_station_names; print(get_station('부산')); print(get_station_names())"
```

- [ ] **Step 3: 커밋**

```bash
git add backend/data/stations.py
git commit -m "지역 데이터 추가 — 16개 도시별 기상청 관측소/격자/지역코드 매핑"
```

---

## Task 3: weather_service.py 전체 재작성

**Files:**
- Modify: `backend/services/weather_service.py`

이 Task가 가장 핵심이고 코드량이 많다. 3개 API 호출 + 통합 로직을 작성한다.

- [ ] **Step 1: 기본 구조 + ASOS(과거 날씨) 함수 작성**

`weather_service.py`를 전체 교체한다. 먼저 import, 공통 상수, ASOS 호출 함수까지 작성한다.

```python
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

# ASOS 전운량 → condition 변환 (전운량 0~10 스케일)
def _cloud_to_condition(avg_tca, sum_rn):
    """전운량과 강수량으로 날씨 상태 결정"""
    if sum_rn and float(sum_rn) > 0:
        return "비"
    if avg_tca is None:
        return "맑음"
    tca = float(avg_tca)
    if tca <= 2:
        return "맑음"
    elif tca <= 5:
        return "구름많음"
    else:
        return "흐림"


# condition → icon 매핑
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
        avg_rhm = item.get("avgRhm")
        avg_ws = item.get("avgWs")
        sum_rn = item.get("sumRn")
        avg_tca = item.get("avgTca")

        condition = _cloud_to_condition(avg_tca, sum_rn)

        result.append({
            "date": date_str,
            "temperature": float(avg_ta) if avg_ta else None,
            "condition": condition,
            "humidity": round(float(avg_rhm)) if avg_rhm else None,
            "wind_speed": round(float(avg_ws), 1) if avg_ws else None,
            "icon": _condition_to_icon(condition),
            "is_past": True,
        })

    return result
```

- [ ] **Step 2: ASOS 함수 동작 확인**

```bash
cd backend && python -c "
from dotenv import load_dotenv; load_dotenv()
from services.weather_service import fetch_asos
data = fetch_asos('서울', '2026-03-01', '2026-03-22')
print(f'{len(data)}건')
for d in data[:3]: print(d)
"
```

- [ ] **Step 3: 단기예보 함수 추가**

`weather_service.py`에 단기예보 호출 함수를 추가한다.

```python
def _get_base_datetime():
    """단기예보 발표 시각 계산 — 가장 최근 발표 시각 반환"""
    now = datetime.now()
    # 단기예보 발표 시각: 0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300
    base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]

    # 현재 시각에서 10분 빼기 (API 생성 지연 고려)
    adjusted = now - timedelta(minutes=10)
    current_hhmm = adjusted.strftime("%H%M")

    base_date = adjusted.strftime("%Y%m%d")
    base_time = "2300"  # 기본값 (전날 23시)

    for bt in base_times:
        if current_hhmm >= bt:
            base_time = bt
        else:
            break

    # 0200 이전이면 전날 2300 사용
    if current_hhmm < "0210":
        base_date = (adjusted - timedelta(days=1)).strftime("%Y%m%d")
        base_time = "2300"

    return base_date, base_time


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

    # 각 날짜에서 정오(1200) 또는 가장 가까운 시간의 대표값 추출
    today = datetime.now().date()
    result = []
    for date_str, times in sorted(daily.items()):
        # 정오에 가장 가까운 시간 찾기
        best_time = min(times.keys(), key=lambda t: abs(int(t) - 1200))
        vals = times[best_time]

        # 하늘상태(SKY) + 강수형태(PTY) → condition
        sky = vals.get("SKY", "1")
        pty = vals.get("PTY", "0")
        condition = _sky_pty_to_condition(sky, pty)

        temp = vals.get("TMP") or vals.get("T1H")
        humidity = vals.get("REH")
        wind = vals.get("WSD")

        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        row_date = datetime.strptime(date_str, "%Y%m%d").date()

        result.append({
            "date": formatted_date,
            "temperature": float(temp) if temp else None,
            "condition": condition,
            "humidity": round(float(humidity)) if humidity else None,
            "wind_speed": round(float(wind), 1) if wind else None,
            "icon": _condition_to_icon(condition),
            "is_past": row_date < today,
        })

    return result


def _sky_pty_to_condition(sky: str, pty: str):
    """단기예보 SKY(하늘상태) + PTY(강수형태) → 한국어 condition"""
    # 강수형태 우선
    pty_map = {"1": "비", "2": "비/눈", "3": "눈", "5": "비", "6": "비/눈", "7": "눈"}
    if pty in pty_map:
        return pty_map[pty]

    # 하늘상태
    sky_map = {"1": "맑음", "3": "구름많음", "4": "흐림"}
    return sky_map.get(sky, "흐림")
```

- [ ] **Step 4: 단기예보 동작 확인**

```bash
cd backend && python -c "
from dotenv import load_dotenv; load_dotenv()
from services.weather_service import fetch_vilage_forecast
data = fetch_vilage_forecast('서울')
print(f'{len(data)}건')
for d in data: print(d)
"
```

- [ ] **Step 5: 중기예보 함수 추가**

```python
def fetch_mid_forecast(station_name: str):
    """중기예보 조회 — 4일~10일 후 기온 + 하늘상태"""
    if not API_KEY:
        return []

    station = get_station(station_name)
    now = datetime.now()

    # 발표 시각: 06시, 18시
    if now.hour < 6:
        tm_fc = (now - timedelta(days=1)).strftime("%Y%m%d") + "1800"
    elif now.hour < 18:
        tm_fc = now.strftime("%Y%m%d") + "0600"
    else:
        tm_fc = now.strftime("%Y%m%d") + "1800"

    # 중기기온 조회
    ta_params = {
        "serviceKey": API_KEY,
        "numOfRows": "10",
        "pageNo": "1",
        "dataType": "JSON",
        "regId": station["mid_ta_id"],
        "tmFc": tm_fc,
    }

    # 중기육상예보 조회
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
    # 중기예보는 3일~10일 후 데이터 제공 (3일차는 단기예보와 겹치므로 4일차부터 사용)
    for day_offset in range(4, 11):
        target_date = today + timedelta(days=day_offset)
        date_str = target_date.isoformat()

        # 기온: taMinN, taMaxN (N=3~10)
        min_temp = ta_item.get(f"taMin{day_offset}")
        max_temp = ta_item.get(f"taMax{day_offset}")

        if min_temp is not None and max_temp is not None:
            avg_temp = round((float(min_temp) + float(max_temp)) / 2, 1)
        else:
            avg_temp = None

        # 하늘상태: wf3Am, wf3Pm ~ wf10 (문자열)
        if day_offset <= 7:
            sky_text = land_item.get(f"wf{day_offset}Am", "") or land_item.get(f"wf{day_offset}Pm", "")
        else:
            sky_text = land_item.get(f"wf{day_offset}", "")

        condition = _mid_sky_to_condition(sky_text)

        result.append({
            "date": date_str,
            "temperature": avg_temp,
            "condition": condition,
            "humidity": None,
            "wind_speed": None,
            "icon": _condition_to_icon(condition),
            "is_past": False,
        })

    return result


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
```

- [ ] **Step 6: 중기예보 동작 확인**

```bash
cd backend && python -c "
from dotenv import load_dotenv; load_dotenv()
from services.weather_service import fetch_mid_forecast
data = fetch_mid_forecast('서울')
print(f'{len(data)}건')
for d in data: print(d)
"
```

- [ ] **Step 7: 통합 조회 함수 작성 (get_weather_for_month, get_weather_for_date)**

기존 함수 시그니처를 유지하면서 station 파라미터를 추가한다.

```python
def get_weather_for_month(month: str, station_name: str = "서울"):
    """월별 날씨 조회 — 캐시 확인 후 필요 시 API 호출"""
    conn = get_connection()
    today = datetime.now().date()

    # 캐시 갱신 필요 여부 확인 (오늘 날짜 기준)
    cached_today = conn.execute(
        "SELECT fetched_at FROM weather_cache WHERE date = ? AND station = ?",
        (today.isoformat(), station_name)
    ).fetchone()

    need_refresh = True
    if cached_today and cached_today["fetched_at"]:
        fetched = datetime.fromisoformat(cached_today["fetched_at"])
        if (datetime.now() - fetched).total_seconds() < 10800:  # 3시간 TTL
            need_refresh = False

    if need_refresh:
        _refresh_weather_cache(station_name)

    # 요청된 월의 데이터 반환
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
            # 과거 데이터는 이미 캐시되어 있으면 갱신하지 않음 (실측값은 변하지 않음)
            existing = conn.execute(
                "SELECT 1 FROM weather_cache WHERE date = ? AND station = ?",
                (item["date"], station_name)
            ).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO weather_cache (date, station, temperature, condition, humidity, wind_speed, icon, fetched_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
                    (item["date"], station_name, item["temperature"], item["condition"],
                     item["humidity"], item["wind_speed"], item["icon"])
                )

    # 2. 단기예보 — 오늘~3일 후
    vilage_data = fetch_vilage_forecast(station_name)
    for item in vilage_data:
        conn.execute(
            """INSERT OR REPLACE INTO weather_cache (date, station, temperature, condition, humidity, wind_speed, icon, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
            (item["date"], station_name, item["temperature"], item["condition"],
             item["humidity"], item["wind_speed"], item["icon"])
        )

    # 3. 중기예보 — 4일~10일 후
    mid_data = fetch_mid_forecast(station_name)
    for item in mid_data:
        conn.execute(
            """INSERT OR REPLACE INTO weather_cache (date, station, temperature, condition, humidity, wind_speed, icon, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
            (item["date"], station_name, item["temperature"], item["condition"],
             item["humidity"], item["wind_speed"], item["icon"])
        )

    conn.commit()
    conn.close()
```

- [ ] **Step 8: 통합 조회 동작 확인**

```bash
cd backend && python -c "
from dotenv import load_dotenv; load_dotenv()
from services.weather_service import get_weather_for_month
data = get_weather_for_month('2026-03', '서울')
print(f'{len(data)}건')
for d in data[:5]: print(d)
print('...')
for d in data[-3:]: print(d)
"
```

- [ ] **Step 9: 커밋**

```bash
git add backend/services/weather_service.py
git commit -m "기상청 API 연동 — ASOS(과거) + 단기예보 + 중기예보 통합 호출 + 지역별 캐시"
```

---

## Task 4: 경고/추천 서비스 한국어 전환

**Files:**
- Modify: `backend/services/warning_service.py`
- Modify: `backend/data/seed.py`

- [ ] **Step 1: warning_service.py 수정**

condition 비교를 영어에서 한국어로 변경한다.

```python
# 기존
if condition in ("Rain", "Drizzle", "Thunderstorm"):
# 변경
if condition in ("비", "비/눈"):

# 기존
if condition == "Snow":
# 변경
if condition in ("눈", "비/눈"):
```

- [ ] **Step 2: seed.py 수정**

SEED_DATA의 conditions에서 영어 날씨값을 한국어로 변경한다.

```python
# 매핑 규칙:
# "Clear" → "맑음"
# "Clouds" → "구름많음"
# "Rain", "Drizzle" → "비"
# "Thunderstorm" → "비"
# "Snow" → "눈"
# "Mist", "Fog", "Haze" → "흐림"
```

- [ ] **Step 3: 시드 데이터 재투입**

```bash
cd backend && python -m data.seed
```

- [ ] **Step 4: 커밋**

```bash
git add backend/services/warning_service.py backend/data/seed.py
git commit -m "경고/추천 한국어 전환 — condition 비교를 영어에서 한국어로 변경"
```

---

## Task 5: 라우터에 station 파라미터 추가

**Files:**
- Modify: `backend/routers/weather.py`
- Modify: `backend/routers/briefing.py`

- [ ] **Step 1: weather.py 수정**

```python
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
```

- [ ] **Step 2: briefing.py 수정**

```python
@router.get("/{date}")
def get_briefing(date: str, station: str = "서울"):
    """특정일 브리핑 — 날씨 + 일정 + 경고 + 추천"""
    weather = get_weather_for_date(date, station)
    # 이하 동일
```

- [ ] **Step 3: 도시 목록 API 추가 (weather.py)**

프론트엔드 드롭다운에 도시 목록을 제공하기 위한 엔드포인트를 추가한다.

```python
from data.stations import get_station_names

@router.get("/stations/list")
def get_stations():
    """사용 가능한 도시 목록 반환"""
    return get_station_names()
```

**주의:** 이 라우트는 `/{date}` 보다 위에 선언해야 경로 충돌이 없다.

- [ ] **Step 4: 서버 실행 후 API 테스트**

```bash
cd backend && python main.py &
sleep 3
curl -s "http://localhost:8000/api/weather/stations/list"
curl -s "http://localhost:8000/api/weather?month=2026-03&station=서울" | head -5
curl -s "http://localhost:8000/api/briefing/2026-03-23?station=서울" | head -10
```

- [ ] **Step 5: 커밋**

```bash
git add backend/routers/weather.py backend/routers/briefing.py
git commit -m "라우터에 지역 파라미터 추가 — station 쿼리 + 도시 목록 API"
```

---

## Task 6: 프론트엔드 — 지역 드롭다운 + API 연동

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/js/api.js`
- Modify: `frontend/css/style.css`

- [ ] **Step 1: index.html — 헤더에 드롭다운 추가**

```html
<!-- 기존 -->
<span class="location">서울</span>

<!-- 변경 -->
<select id="station-select" class="location-select">
    <option value="서울" selected>서울</option>
    <option value="부산">부산</option>
    <option value="대구">대구</option>
    <option value="인천">인천</option>
    <option value="광주">광주</option>
    <option value="대전">대전</option>
    <option value="울산">울산</option>
    <option value="세종">세종</option>
    <option value="제주">제주</option>
    <option value="수원">수원</option>
    <option value="춘천">춘천</option>
    <option value="청주">청주</option>
    <option value="전주">전주</option>
    <option value="포항">포항</option>
    <option value="창원">창원</option>
    <option value="강릉">강릉</option>
</select>
```

- [ ] **Step 2: api.js — station 파라미터 추가**

모든 날씨/브리핑 API 호출에 선택된 도시를 전달한다.

```javascript
function getStation() {
    return document.getElementById('station-select').value;
}

const api = {
    // schedules는 변경 없음 (일정은 지역 무관)

    async getWeather(month) {
        const station = getStation();
        const res = await fetch(`${API_BASE}/weather?month=${month}&station=${encodeURIComponent(station)}`);
        return res.json();
    },

    async getBriefing(date) {
        const station = getStation();
        const res = await fetch(`${API_BASE}/briefing/${date}?station=${encodeURIComponent(station)}`);
        return res.json();
    }
};
```

- [ ] **Step 3: style.css — 드롭다운 스타일 추가**

```css
.location-select {
    background: rgba(255,255,255,0.2);
    color: white;
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 0.9rem;
    cursor: pointer;
}

.location-select option {
    color: #333;
    background: white;
}
```

- [ ] **Step 4: 커밋**

```bash
git add frontend/index.html frontend/js/api.js frontend/css/style.css
git commit -m "프론트엔드 지역 선택 — 헤더 드롭다운 + API에 station 파라미터 전달"
```

---

## Task 7: 프론트엔드 — 아이콘 매핑 변경 + 지역 변경 이벤트

**Files:**
- Modify: `frontend/js/calendar.js`
- Modify: `frontend/js/briefing.js`

- [ ] **Step 1: calendar.js — 아이콘 매핑 교체 + 지역 변경 이벤트**

기존 OpenWeatherMap 아이콘 매핑을 자체 코드로 교체하고, 드롭다운 변경 시 캘린더를 다시 렌더링한다.

```javascript
// 기존 WEATHER_ICONS 전체를 아래로 교체
const WEATHER_ICONS = {
    'sunny': '☀️',
    'partly_cloudy': '⛅',
    'cloudy': '☁️',
    'rain': '🌧',
    'snow': '🌨',
    'sleet': '🌧',
};
```

DOMContentLoaded 이벤트에 드롭다운 변경 리스너를 추가한다.

```javascript
document.getElementById('station-select').addEventListener('change', () => {
    renderCalendar();
});
```

아이콘 렌더링 부분에서 기존 `WEATHER_ICONS[dayIcon]` 대신 `WEATHER_ICONS[weather.icon]`을 사용한다 (icon이 이제 자체 코드이므로 d/n 변환 불필요).

```javascript
// 기존: const dayIcon = weather.icon.replace('n', 'd');
//       iconSpan.textContent = WEATHER_ICONS[dayIcon] || WEATHER_ICONS[weather.icon] || '';
// 변경:
iconSpan.textContent = WEATHER_ICONS[weather.icon] || '';
```

- [ ] **Step 2: briefing.js — 아이콘 매핑 변경**

브리핑 카드에서도 동일하게 자체 아이콘 코드를 사용한다.

```javascript
// 기존
const icon = WEATHER_ICONS[w.icon] || '🌡';
// 변경 (WEATHER_ICONS가 calendar.js에서 전역으로 선언되어 있으므로 그대로 사용)
const icon = WEATHER_ICONS[w.icon] || '🌡';
```

condition이 한국어로 오므로 브리핑 카드에서 별도 번역 없이 바로 표시된다.

- [ ] **Step 3: 커밋**

```bash
git add frontend/js/calendar.js frontend/js/briefing.js
git commit -m "아이콘 매핑 변경 — OpenWeatherMap 코드를 자체 한국어 기반 코드로 교체 + 지역 변경 이벤트"
```

---

## Task 8: 통합 테스트

- [ ] **Step 1: 기존 DB 삭제 + 시드 데이터 재투입**

```bash
cd backend && rm -f weathercal.db && python -m data.seed
```

- [ ] **Step 2: 서버 실행**

```bash
cd backend && python main.py
```

- [ ] **Step 3: 전체 플로우 테스트**

1. 브라우저에서 `http://localhost:8000` 접속
2. 캘린더에 과거 날짜(3/1~3/22)와 미래 날짜(3/23~4/2)에 날씨 아이콘이 표시되는지 확인
3. 헤더 드롭다운에서 "부산"으로 변경 → 캘린더가 부산 날씨로 갱신되는지 확인
4. 날짜 클릭 → 브리핑 패널에 한국어 condition 표시 확인
5. 일정 등록 → 야외 일정에 비 경고가 한국어로 표시되는지 확인
6. 활동 추천이 한국어 condition 기준으로 정상 매칭되는지 확인

- [ ] **Step 4: 버그 수정 (발견 시)**

- [ ] **Step 5: 최종 커밋**

```bash
git add -A
git commit -m "기상청 API 교체 완료 — 전체 통합 테스트 통과"
```
