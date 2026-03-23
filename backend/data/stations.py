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
