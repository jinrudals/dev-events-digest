import json

from digest.collectors.base import http_get
from digest.models import Event, parse_kst

URL = "https://community.cncf.io/api/event/"
PARAMS = {
    "status": "Live",
    "order_by": "start_date",
    "page_size": "200",
    "fields": "title,start_date,end_date,url,event_type_title,city,venue_name,description_short",
}


def parse(raw: str) -> list[Event]:
    events: list[Event] = []
    for r in json.loads(raw).get("results", []):
        etype = (r.get("event_type_title") or "").lower()
        online = "online" in etype or "virtual" in etype
        loc = ", ".join(p for p in (r.get("venue_name"), r.get("city")) if p)
        events.append(
            Event(
                title=r["title"],
                url=r["url"],
                start=parse_kst(r["start_date"].replace("Z", "+00:00")),
                end=parse_kst(r["end_date"].replace("Z", "+00:00")) if r.get("end_date") else None,
                location="Online" if online else loc,
                online=online,
                source="cncf",
                description=r.get("description_short") or "",
            )
        )
    return events


class CncfCollector:
    name = "cncf"

    def fetch(self) -> list[Event]:
        return parse(http_get(URL, params=PARAMS))
