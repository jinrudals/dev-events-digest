import json
import xml.etree.ElementTree as ET

from digest.publish import add_week, build_feed, load_history, save_history, write_site

URL = "https://jinrudals.github.io/dev-events-digest"


def week(d):
    return dict(date=d, title=f"주간 {d}", html=f"<html><head></head><body><p>{d} <b>행사</b></p></body></html>", count=1)


def test_add_week_sorts_desc_and_trims_to_20():
    h = []
    for i in range(1, 26):
        h = add_week(h, **week(f"2026-01-{i:02d}"))
    assert len(h) == 20
    assert h[0]["date"] == "2026-01-25" and h[-1]["date"] == "2026-01-06"


def test_add_week_same_date_replaces():
    h = add_week([], **week("2026-11-16"))
    h = add_week(h, date="2026-11-16", title="new", html="x", count=2)
    assert len(h) == 1 and h[0]["title"] == "new"


def test_history_roundtrip_and_missing_file(tmp_path):
    p = str(tmp_path / "h.json")
    assert load_history(p) == []
    save_history([week("2026-11-16")], p)
    assert load_history(p)[0]["date"] == "2026-11-16"


def test_feed_is_valid_rss_with_escaped_html_and_links():
    xml = build_feed([week("2026-11-16"), week("2026-11-09")], URL)
    root = ET.fromstring(xml)
    items = root.findall("./channel/item")
    assert len(items) == 2
    assert items[0].findtext("link") == f"{URL}/archive/2026-11-16.html"
    assert "<b>행사</b>" in items[0].findtext("description")
    assert items[0].findtext("pubDate").endswith("+0900")


def test_write_site_creates_index_archive_and_feed(tmp_path):
    write_site([week("2026-11-16"), week("2026-11-09")], str(tmp_path), URL)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2026-11-16 <b>행사</b>" in index
    assert 'href="archive/2026-11-09.html"' in index
    assert 'type="application/rss+xml"' in index
    assert (tmp_path / "archive" / "2026-11-09.html").exists()
    assert (tmp_path / "feed.xml").exists()
    assert (tmp_path / ".nojekyll").exists()


def test_write_site_with_empty_history_still_writes_feed(tmp_path):
    write_site([], str(tmp_path), URL)
    assert ET.fromstring((tmp_path / "feed.xml").read_text(encoding="utf-8")).find("channel") is not None
    assert "아직 발행된 다이제스트가 없습니다" in (tmp_path / "index.html").read_text(encoding="utf-8")
