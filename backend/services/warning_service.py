"""
Role: 야외 일정에 날씨 경고 메시지 생성
Key Features: 비/한파/강풍/폭염 조건별 경고
Dependencies: 없음 (순수 로직)
"""


def get_warnings(category: str, weather: dict) -> list[str]:
    """일정 카테고리와 날씨 데이터로 경고 메시지 목록 반환"""
    if category != "outdoor" or not weather:
        return []

    warnings = []
    condition = weather.get("condition", "")
    temp = weather.get("temperature")
    wind = weather.get("wind_speed")

    if condition in ("Rain", "Drizzle", "Thunderstorm"):
        warnings.append("🌧 비 예보가 있어요, 우산을 챙기세요")

    if condition == "Snow":
        warnings.append("🌨 눈 예보가 있어요, 미끄럼에 주의하세요")

    if temp is not None and temp < 0:
        warnings.append("🥶 영하 날씨예요, 방한 준비하세요")

    if temp is not None and temp >= 33:
        warnings.append("🥵 폭염 경보, 야외 활동을 자제하세요")

    if wind is not None and wind > 10:
        warnings.append("💨 강풍 주의, 야외 활동에 주의하세요")

    return warnings
