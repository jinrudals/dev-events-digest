import re
from datetime import datetime

from digest.collectors.base import http_get
from digest.models import KST, Event

URL = "https://raw.githubusercontent.com/brave-people/Dev-Event/master/README.md"

_SECTION = re.compile(r"^## `(\d{2})년 (\d{1,2})월`")
_ENTRY = re.compile(r"^- __\[(.+?)\]\((.+?)\)__")
_FIELD = re.compile(r"^\s+- (분류|주최|일시|접수): (.*)$")
_DATE = re.compile(r"(\d{1,2})\. (\d{1,2})\([^)]*\)(?: (\d{1,2}):(\d{2}))?")
_LOC = re.compile(r"오프라인\((.*?)\)")


def _to_dt(m: re.Match, year: int, section_month: int) -> datetime:
    month, day = int(m.group(1)), int(m.group(2))
    y = year + 1 if month < section_month - 6 else year
    hour, minute = (int(m.group(3)), int(m.group(4))) if m.group(3) else (0, 0)
    return datetime(y, month, day, hour, minute, tzinfo=KST)


def _build(title: str, url: str, fields: dict[str, str], year: int, month: int) -> Event | None:
    when = fields.get("일시") or fields.get("접수")
    if not when:
        return None
    dates = [_to_dt(m, year, month) for m in _DATE.finditer(when)]
    if not dates:
        return None
    tags = fields.get("분류", "")
    loc = _LOC.search(tags)
    online = "온라인" in tags
    desc = f"분류: {tags} / 주최: {fields.get('주최', '')}"
    has_event_dates = "일시" in fields
    return Event(
        title=title,
        url=url,
        start=dates[-1] if not has_event_dates else dates[0],
        end=dates[-1] if has_event_dates and len(dates) > 1 else None,
        location="온라인" if online else (loc.group(1) if loc else ""),
        online=online,
        source="dev-event",
        description=desc,
    )


def parse(raw: str) -> list[Event]:
    events: list[Event] = []
    year = month = 0
    current: tuple[str, str] | None = None
    fields: dict[str, str] = {}

    def flush():
        if current and year:
            ev = _build(current[0], current[1], fields, year, month)
            if ev:
                events.append(ev)

    for line in raw.splitlines():
        if line.startswith("## "):
            flush()
            current, fields = None, {}
            m = _SECTION.match(line)
            year, month = (2000 + int(m.group(1)), int(m.group(2))) if m else (0, 0)
            continue
        m = _ENTRY.match(line)
        if m:
            flush()
            current, fields = (m.group(1), m.group(2)), {}
            continue
        m = _FIELD.match(line)
        if m and current:
            fields[m.group(1)] = m.group(2)
    flush()
    return events


class DevEventCollector:
    name = "dev-event"

    def fetch(self) -> list[Event]:
        return parse(http_get(URL))
