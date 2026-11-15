from datetime import datetime, timedelta

from digest.models import Event

KOREA_HINTS = [
    "한국", "대한민국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기",
    "강원", "충북", "충남", "충청", "전북", "전남", "전라", "경북", "경남", "경상", "제주",
    "판교", "성남", "수원", "korea", "seoul", "busan", "incheon", "daegu", "daejeon", "jeju",
    "pangyo", "seongnam",
]


def is_korea(location: str) -> bool:
    loc = location.lower()
    return any(h in loc for h in KOREA_HINTS)


def filter_events(events: list[Event], now: datetime, days: int = 60) -> list[Event]:
    limit = now + timedelta(days=days)
    return [
        e
        for e in events
        if (e.end or e.start) >= now and e.start <= limit and (e.online or is_korea(e.location))
    ]
