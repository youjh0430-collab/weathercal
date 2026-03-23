# 기상청 API 교체 설계

## 목표

OpenWeatherMap API를 한국 기상청(공공데이터포털) API 3개로 교체하여, 과거 관측 데이터 + 단기예보 + 중기예보를 통합 제공한다. 지역 선택 기능을 추가하여 주요 도시별 날씨를 조회할 수 있도록 한다.

## 배경

- 기존 OpenWeatherMap 무료 플랜은 미래 5일 예보만 제공하여 과거 날씨 표시 불가
- 기상청 API는 과거 관측 데이터를 무료로 제공
- 한국 사용자 대상 서비스이므로 기상청 데이터가 더 정확하고 자연스러움

## API 구성

### 1. 종관기상관측(ASOS) 일자료 조회

- **용도**: 과거~어제 날씨 (실측값)
- **엔드포인트**: `http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList`
- **주요 파라미터**: `stnIds` (관측소 번호), `startDt`, `endDt`, `dataCd=ASOS`, `dateCd=DAY`
- **응답 데이터**: 평균기온(avgTa), 최고기온(maxTa), 최저기온(minTa), 평균습도(avgRhm), 평균풍속(avgWs), 일강수량(sumRn), 전운량(avgTca)

### 2. 단기예보 조회

- **용도**: 오늘~3일 후 예보
- **엔드포인트**: `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst`
- **주요 파라미터**: `base_date`, `base_time`, `nx`, `ny` (격자좌표)
- **응답 데이터**: TMP(기온), SKY(하늘상태), PTY(강수형태), REH(습도), WSD(풍속)
- **하늘상태 코드**: 1=맑음, 3=구름많음, 4=흐림
- **강수형태 코드**: 0=없음, 1=비, 2=비/눈, 3=눈, 5=빗방울, 6=빗방울눈날림, 7=눈날림

### 3. 중기예보 조회

- **용도**: 4일~10일 후 예보
- **중기기온**: `http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa`
- **중기육상예보**: `http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst`
- **주요 파라미터**: `regId` (예보구역코드), `tmFc` (발표시각)
- **응답 데이터**: 최저/최고기온, 하늘상태(문자열), 강수확률
- **참고**: 습도, 풍속은 제공하지 않음 → null 처리

## 인증

- API 키: 3개 서비스 동일 키 사용
- `.env` 파일에 `KMA_API_KEY` 하나로 관리
- 기존 `OPENWEATHER_API_KEY`는 제거

## 통합 날씨 데이터 형식

프론트엔드와 경고/추천 서비스에 전달하는 통합 형식. 기존 구조를 최대한 유지하되 condition을 한국어로 변경.

```python
{
    "date": "2026-03-23",
    "temperature": 14.1,
    "condition": "흐림",        # 맑음, 구름많음, 흐림, 비, 눈, 비/눈
    "humidity": 30,             # 중기예보는 None
    "wind_speed": 2.1,          # 중기예보는 None
    "icon": "cloudy",           # 자체 아이콘 코드
    "is_past": False
}
```

## 아이콘 매핑

OpenWeatherMap 아이콘 코드(01d 등)를 자체 코드로 단순화.

| condition | icon 코드 | 이모지 |
|-----------|----------|--------|
| 맑음 | sunny | ☀️ |
| 구름많음 | partly_cloudy | ⛅ |
| 흐림 | cloudy | ☁️ |
| 비 | rain | 🌧 |
| 눈 | snow | 🌨 |
| 비/눈 | sleet | 🌧 |

## 지역 선택

### 드롭다운 도시 목록

헤더의 "서울" 텍스트를 드롭다운(`<select>`)으로 교체.

| 도시 | ASOS 관측소(stnIds) | 단기예보 격자(nx,ny) | 중기기온(regId) | 중기육상(regId) |
|------|--------------------|--------------------|----------------|----------------|
| 서울 | 108 | 60,127 | 11B10101 | 11B00000 |
| 부산 | 159 | 98,76 | 11H20201 | 11H20000 |
| 대구 | 143 | 89,90 | 11H10701 | 11H10000 |
| 인천 | 112 | 55,124 | 11B20201 | 11B00000 |
| 광주 | 156 | 58,74 | 11F20501 | 11F20000 |
| 대전 | 133 | 67,100 | 11C20401 | 11C20000 |
| 울산 | 152 | 102,84 | 11H20101 | 11H20000 |
| 세종 | 129 | 66,103 | 11C20404 | 11C20000 |
| 제주 | 184 | 52,38 | 11G00201 | 11G00000 |
| 수원 | 119 | 60,121 | 11B20601 | 11B00000 |
| 춘천 | 101 | 73,134 | 11D10301 | 11D10000 |
| 청주 | 131 | 69,106 | 11C10301 | 11C10000 |
| 전주 | 146 | 63,89 | 11F10201 | 11F10000 |
| 포항 | 138 | 102,94 | 11H10201 | 11H10000 |
| 창원 | 155 | 89,77 | 11H20301 | 11H20000 |
| 강릉 | 105 | 92,131 | 11D20501 | 11D20000 |

### 지역 데이터 관리

`backend/data/stations.py`에 딕셔너리로 관리.

```python
STATIONS = {
    "서울": {"stn_id": "108", "nx": 60, "ny": 127, "mid_ta_id": "11B10101", "mid_land_id": "11B00000"},
    "부산": {"stn_id": "159", "nx": 98, "ny": 76, "mid_ta_id": "11H20201", "mid_land_id": "11H20000"},
    ...
}
```

## 캐시 전략

### weather_cache 테이블 변경

기존 테이블에 `station` 컬럼을 추가하여 지역별 캐시를 분리.

```sql
CREATE TABLE weather_cache (
    date TEXT,
    station TEXT,            -- 추가: 도시명
    temperature REAL,
    condition TEXT,
    humidity REAL,
    wind_speed REAL,
    icon TEXT,
    fetched_at TEXT,
    PRIMARY KEY (date, station)  -- 복합키로 변경
);
```

### 갱신 정책

- **과거 데이터**: 한 번 조회 후 갱신 불필요 (실측값은 변하지 않음)
- **단기예보**: 3시간 TTL (기존과 동일)
- **중기예보**: 12시간 TTL (하루 2회 발표)

## 경고/추천 서비스 변경

### warning_service.py

```python
# 기존
if condition in ("Rain", "Drizzle", "Thunderstorm"):
# 변경
if condition in ("비", "비/눈"):

# 기존
if condition == "Snow":
# 변경
if condition == "눈":
```

### recommend_service.py / seed.py

activities 테이블의 conditions JSON에서 weather 배열을 한국어로 변경.

```python
# 기존: {"weather": ["Clear", "Clouds"], "temp_range": "comfortable"}
# 변경: {"weather": ["맑음", "구름많음"], "temp_range": "comfortable"}
```

## API 엔드포인트 변경

### 날씨 조회

```
# 기존
GET /api/weather?month=2026-03

# 변경 — station 파라미터 추가
GET /api/weather?month=2026-03&station=서울
```

### 브리핑

```
# 기존
GET /api/briefing/2026-03-23

# 변경
GET /api/briefing/2026-03-23?station=서울
```

## 프론트엔드 변경

### index.html

```html
<!-- 기존 -->
<span class="location">서울</span>

<!-- 변경 -->
<select id="station-select" class="location-select">
    <option value="서울" selected>서울</option>
    <option value="부산">부산</option>
    ...
</select>
```

### calendar.js 아이콘 매핑

```javascript
// 기존: OpenWeatherMap 코드
const WEATHER_ICONS = { '01d': '☀️', ... };

// 변경: 자체 코드
const WEATHER_ICONS = {
    'sunny': '☀️',
    'partly_cloudy': '⛅',
    'cloudy': '☁️',
    'rain': '🌧',
    'snow': '🌨',
    'sleet': '🌧',
};
```

### api.js

모든 API 호출에 선택된 station 값을 파라미터로 전달.

## 변경 파일 목록

| 파일 | 변경 유형 |
|------|----------|
| `.env` | 수정 — OPENWEATHER_API_KEY → KMA_API_KEY |
| `backend/data/stations.py` | 신규 — 도시별 관측소/격자/지역코드 |
| `backend/services/weather_service.py` | 전체 재작성 — 기상청 3개 API 호출 + 통합 |
| `backend/services/warning_service.py` | 수정 — condition 한국어 매핑 |
| `backend/services/recommend_service.py` | 수정 — condition 매칭 한국어 |
| `backend/data/seed.py` | 수정 — activities conditions 한국어 |
| `backend/routers/weather.py` | 수정 — station 파라미터 추가 |
| `backend/routers/briefing.py` | 수정 — station 파라미터 추가 |
| `backend/database.py` | 수정 — weather_cache 테이블에 station 컬럼 |
| `frontend/index.html` | 수정 — 헤더에 지역 드롭다운 |
| `frontend/js/calendar.js` | 수정 — 아이콘 매핑 + 지역 변경 이벤트 |
| `frontend/js/api.js` | 수정 — station 파라미터 전달 |
| `frontend/js/briefing.js` | 수정 — 아이콘 매핑 변경 |
| `frontend/css/style.css` | 수정 — 드롭다운 스타일 |
