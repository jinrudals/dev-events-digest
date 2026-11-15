import html
import re
from datetime import datetime

from bs4 import BeautifulSoup

from digest.collectors.base import http_get
from digest.models import KST, Event

BASE = "https://onoffmix.com"
QUERIES = ["devops", "kubernetes", "인공지능 ai", "개발자", "클라우드", "플랫폼 엔지니어링"]

_FULL = re.compile(r"(\d{4})\.(\d{2})\.(\d{2}) \([^)]*\) (\d{1,2}):(\d{2})")
_TIME = re.compile(r"(\d{1,2}):(\d{2})")


def _full(m: re.Match) -> datetime:
    return datetime(*(int(g) for g in m.groups()), tzinfo=KST)


def _span(text: str) -> tuple[datetime, datetime | None] | None:
    left, _, right = text.partition("~")
    m = _FULL.search(left)
    if not m:
        return None
    start = _full(m)
    end = None
    rm = _FULL.search(right)
    if rm:
        end = _full(rm)
    else:
        tm = _TIME.search(right)
        if tm:
            end = start.replace(hour=int(tm.group(1)), minute=int(tm.group(2)))
    return start, end


def parse(raw: str) -> list[Event]:
    soup = BeautifulSoup(raw, "html.parser")
    events: list[Event] = []
    for art in soup.select("article.event_area"):
        a = art.find("a", href=re.compile(r"^/event/\d+"))
        title_el = art.select_one(".title")
        date_el = art.select_one(".list_date_place .date")
        place_el = art.select_one(".list_date_place .place")
        if not (a and title_el and date_el):
            continue
        span = _span(date_el.get_text(strip=True))
        if not span:
            continue
        place = place_el.get_text(strip=True) if place_el else ""
        cat = art.select_one(".category_type")
        tags = " ".join(t.get_text(strip=True) for t in art.select(".list_event_tags .tag"))
        events.append(
            Event(
                title=html.unescape(title_el.get_text(strip=True)),
                url=BASE + re.match(r"/event/\d+", a["href"]).group(0),
                start=span[0],
                end=span[1],
                location=place,
                online=place == "온라인",
                source="onoffmix",
                description=f"{cat.get_text(strip=True) if cat else ''} {tags}".strip(),
            )
        )
    return events


class OnoffmixCollector:
    name = "onoffmix"

    def fetch(self) -> list[Event]:
        seen: dict[str, Event] = {}
        for q in QUERIES:
            for e in parse(http_get(f"{BASE}/event/main", params={"s": q})):
                seen.setdefault(e.url, e)
        return list(seen.values())
