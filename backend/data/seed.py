"""
Role: 활동 추천 초기 데이터를 DB에 투입
Key Features: 날씨×기온 조합별 한국인 패치 활동 추천 데이터
Dependencies: database
Notes: 최초 1회 실행 또는 데이터 리셋 시 실행
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_connection, init_db

SEED_DATA = [
    # months: 해당 활동이 어울리는 월 (None이면 연중)
    # 봄(3~5), 여름(6~8), 가을(9~11), 겨울(12~2)
    ("한강 피크닉", "outdoor", {"weather": ["맑음"], "temp_range": "comfortable", "months": [3,4,5,6,9,10]}, "야외, 소셜, 봄"),
    ("자전거 타기", "outdoor", {"weather": ["맑음"], "temp_range": "comfortable"}, "운동, 야외"),
    ("빨래하기 좋은 날", "indoor", {"weather": ["맑음"], "temp_range": "comfortable"}, "일상, 집안일"),
    ("둘레길 산책", "outdoor", {"weather": ["맑음"], "temp_range": "comfortable"}, "산책, 자연"),
    ("치맥", "outdoor", {"weather": ["맑음"], "temp_range": "comfortable", "months": [5,6,7,8,9]}, "음식, 소셜"),
    ("빙수 먹으러 가기", "indoor", {"weather": ["맑음"], "temp_range": "warm", "months": [6,7,8]}, "음식, 여름"),
    ("냉면 맛집", "indoor", {"weather": ["맑음"], "temp_range": "warm", "months": [6,7,8]}, "음식, 여름"),
    ("계곡 물놀이", "outdoor", {"weather": ["맑음"], "temp_range": "warm", "months": [7,8]}, "야외, 여름"),
    ("워터파크", "outdoor", {"weather": ["맑음"], "temp_range": "warm", "months": [6,7,8]}, "야외, 여름"),
    ("쇼핑몰 대피", "indoor", {"weather": ["맑음"], "temp_range": "hot", "months": [6,7,8]}, "쇼핑, 여름"),
    ("영화관", "indoor", {"weather": ["맑음"], "temp_range": "hot"}, "여가, 실내"),
    ("팥빙수 투어", "indoor", {"weather": ["맑음"], "temp_range": "hot", "months": [6,7,8]}, "음식, 여름"),
    ("단풍길 산책", "outdoor", {"weather": ["맑음"], "temp_range": "cool", "months": [9,10,11]}, "산책, 가을"),
    ("전통시장 구경", "outdoor", {"weather": ["맑음"], "temp_range": "cool"}, "쇼핑, 문화"),
    ("호떡 사먹기", "outdoor", {"weather": ["맑음"], "temp_range": "cool", "months": [10,11,12,1,2]}, "음식, 가을"),
    ("찜질방", "indoor", {"weather": ["맑음"], "temp_range": "cold", "months": [11,12,1,2,3]}, "여가, 겨울"),
    ("설렁탕 맛집", "indoor", {"weather": ["맑음"], "temp_range": "cold", "months": [10,11,12,1,2,3]}, "음식, 겨울"),
    ("군고구마 사먹기", "outdoor", {"weather": ["맑음"], "temp_range": "cold", "months": [11,12,1,2]}, "음식, 겨울"),
    ("집콕", "indoor", {"weather": ["맑음"], "temp_range": "freezing"}, "집콕, 겨울"),
    ("군밤 까먹기", "indoor", {"weather": ["맑음"], "temp_range": "freezing", "months": [11,12,1,2]}, "음식, 집콕"),
    ("이불 속 넷플릭스", "indoor", {"weather": ["맑음"], "temp_range": "freezing"}, "집콕, 여가"),
    ("야외 카페", "outdoor", {"weather": ["구름많음"], "temp_range": "comfortable", "months": [4,5,6,9,10]}, "카페, 야외"),
    ("사진 찍기", "outdoor", {"weather": ["구름많음"], "temp_range": "comfortable"}, "취미, 야외"),
    ("카페 투어", "indoor", {"weather": ["구름많음"], "temp_range": "cool"}, "카페, 탐방"),
    ("서점 탐방", "indoor", {"weather": ["구름많음"], "temp_range": "cool"}, "여가, 독서"),
    ("드라이브", "outdoor", {"weather": ["구름많음"], "temp_range": "comfortable"}, "드라이브, 야외"),
    ("미술관 관람", "indoor", {"weather": ["구름많음"], "temp_range": "comfortable"}, "전시, 문화"),
    ("통창 카페 비 구경", "indoor", {"weather": ["비"], "temp_range": "comfortable"}, "카페, 감성, 비"),
    ("파전+막걸리", "indoor", {"weather": ["비"], "temp_range": "cool"}, "음식, 비, 전통"),
    ("독서", "indoor", {"weather": ["비"], "temp_range": None}, "여가, 집콕"),
    ("집콕 라면 끓이기", "indoor", {"weather": ["비"], "temp_range": None}, "집콕, 음식, 비"),
    ("넷플릭스 정주행", "indoor", {"weather": ["비"], "temp_range": None}, "집콕, 여가"),
    ("이불 속 담요+간식", "indoor", {"weather": ["비"], "temp_range": None}, "집콕, 편안"),
    ("배달음식 시켜먹기", "indoor", {"weather": ["비"], "temp_range": None}, "음식, 집콕"),
    ("눈 구경 산책", "outdoor", {"weather": ["눈"], "temp_range": "cold", "months": [12,1,2]}, "산책, 겨울, 눈"),
    ("붕어빵 투어", "outdoor", {"weather": ["눈"], "temp_range": "cold", "months": [11,12,1,2]}, "음식, 겨울"),
    ("겨울 카페", "indoor", {"weather": ["눈"], "temp_range": "cold", "months": [11,12,1,2]}, "카페, 겨울"),
    ("수정과 만들기", "indoor", {"weather": ["눈"], "temp_range": "freezing", "months": [12,1,2]}, "요리, 전통, 겨울"),
    ("김치찌개 끓이기", "indoor", {"weather": ["눈"], "temp_range": "freezing"}, "요리, 집콕"),
    ("감성 드라이브", "outdoor", {"weather": ["흐림"], "temp_range": None}, "드라이브, 감성"),
    ("따뜻한 카페", "indoor", {"weather": ["흐림"], "temp_range": None}, "카페, 감성"),
    ("두쫀쿠 만들기", "indoor", {"weather": ["비", "눈", "흐림"], "temp_range": None}, "요리, 트렌드, 집콕"),
    ("달고나 커피 만들기", "indoor", {"weather": ["비", "눈"], "temp_range": None}, "요리, 트렌드, 카페"),
    ("약과 만들기", "indoor", {"weather": ["비", "눈", "흐림"], "temp_range": None}, "요리, 전통, 트렌드"),
    ("영화 감상", "indoor", {"weather": ["비", "눈"], "temp_range": None}, "집콕, 여가"),
    # 봄 전용
    ("벚꽃 구경", "outdoor", {"weather": ["맑음", "구름많음"], "temp_range": "cool", "months": [3,4]}, "산책, 봄, 꽃"),
    ("봄나들이", "outdoor", {"weather": ["맑음"], "temp_range": "cool", "months": [3,4,5]}, "산책, 봄"),
]


def run_seed():
    """시드 데이터 투입"""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM activities")
    for name, category, conditions, tags in SEED_DATA:
        conn.execute(
            "INSERT INTO activities (name, category, conditions, tags) VALUES (?, ?, ?, ?)",
            (name, category, json.dumps(conditions, ensure_ascii=False), tags)
        )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) as cnt FROM activities").fetchone()["cnt"]
    conn.close()
    print(f"시드 데이터 {count}건 투입 완료")


if __name__ == "__main__":
    run_seed()
