from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


@dataclass
class Event:
    title: str
    url: str
    start: datetime
    end: datetime | None
    location: str
    online: bool
    source: str
    description: str = ""
    topics: list[str] = field(default_factory=list)
    summary: str = ""


def parse_kst(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=KST)
