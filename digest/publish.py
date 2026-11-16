import json
import os
from datetime import datetime
from email.utils import format_datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

from digest.models import KST

KEEP = 20


def load_history(path: str = "state/history.json") -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_history(history: list[dict], path: str = "state/history.json") -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")


def add_week(history: list[dict], date: str, title: str, html: str, count: int, keep: int = KEEP) -> list[dict]:
    rest = [h for h in history if h["date"] != date]
    rest.append({"date": date, "title": title, "html": html, "count": count})
    return sorted(rest, key=lambda h: h["date"], reverse=True)[:keep]


def build_feed(history: list[dict], site_url: str) -> str:
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = "개발자 행사 주간 소식"
    ET.SubElement(ch, "link").text = site_url + "/"
    ET.SubElement(ch, "description").text = "매주 월요일 10:00 KST, 웨비나/한국 오프라인 컨퍼런스 모음"
    ET.SubElement(ch, "language").text = "ko"
    for h in history:
        link = f"{site_url}/archive/{h['date']}.html"
        item = ET.SubElement(ch, "item")
        ET.SubElement(item, "title").text = h["title"]
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", isPermaLink="true").text = link
        published = datetime.fromisoformat(h["date"]).replace(hour=10, tzinfo=KST)
        ET.SubElement(item, "pubDate").text = format_datetime(published)
        ET.SubElement(item, "description").text = h["html"]
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")


def _with_nav(html: str, history: list[dict], site_url: str) -> str:
    feed_link = f'<link rel="alternate" type="application/rss+xml" title="개발자 행사 주간 소식" href="{escape(site_url)}/feed.xml">'
    items = "".join(
        f'<li><a href="archive/{h["date"]}.html">{escape(h["title"])}</a></li>' for h in history
    )
    nav = f'<hr><h3>지난 소식</h3><ul>{items}</ul><p><a href="feed.xml">RSS 구독</a></p>'
    return html.replace("</head>", feed_link + "</head>", 1).replace("</body>", nav + "</body>", 1)


_EMPTY = (
    '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>개발자 행사 주간 소식</title></head>'
    "<body><p>아직 발행된 다이제스트가 없습니다.</p></body></html>"
)


def write_site(history: list[dict], site_dir: str, site_url: str) -> None:
    root = Path(site_dir)
    (root / "archive").mkdir(parents=True, exist_ok=True)
    (root / ".nojekyll").write_text("", encoding="utf-8")
    for h in history:
        (root / "archive" / f"{h['date']}.html").write_text(h["html"], encoding="utf-8")
    latest = history[0]["html"] if history else _EMPTY
    (root / "index.html").write_text(_with_nav(latest, history, site_url), encoding="utf-8")
    (root / "feed.xml").write_text(build_feed(history, site_url), encoding="utf-8")
