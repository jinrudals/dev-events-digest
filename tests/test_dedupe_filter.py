from datetime import datetime, timedelta

from digest.models import KST, Event
from digest.pipeline.dedupe import dedupe
from digest.pipeline.filter import filter_events

NOW = datetime(2026, 11, 16, 10, 0, tzinfo=KST)


def ev(title="T", url="https://x/1", start=None, end=None, location="서울 강남구", online=False):
    return Event(title, url, start or NOW + timedelta(days=3), end, location, online, "s")


def test_dedupe_same_title_date_different_url():
    a = ev("KubeCon  Korea!", "https://a")
    b = ev("kubecon korea", "https://b")
    assert dedupe([a, b]) == [a]


def test_dedupe_same_url():
    a = ev("One", "https://same")
    b = ev("Two", "https://same", start=NOW + timedelta(days=9))
    assert dedupe([a, b]) == [a]


def test_dedupe_keeps_same_title_on_different_dates():
    a = ev("Meetup", "https://a")
    b = ev("Meetup", "https://b", start=NOW + timedelta(days=10))
    assert dedupe([a, b]) == [a, b]


def test_filter_excludes_past():
    assert filter_events([ev(start=NOW - timedelta(days=2))], NOW) == []


def test_filter_includes_ongoing_by_end_date():
    e = ev(start=NOW - timedelta(days=1), end=NOW + timedelta(days=1))
    assert filter_events([e], NOW) == [e]


def test_filter_boundary_day_60_included_61_excluded():
    in_ = ev(url="https://in", start=NOW + timedelta(days=60))
    out = ev(url="https://out", start=NOW + timedelta(days=61))
    assert filter_events([in_, out], NOW) == [in_]


def test_filter_excludes_overseas_offline():
    assert filter_events([ev(location="Porto, Portugal")], NOW) == []


def test_filter_keeps_online_anywhere():
    e = ev(location="Online", online=True)
    assert filter_events([e], NOW) == [e]


def test_filter_keeps_korean_cities_in_english():
    e = ev(location="COEX, Seoul")
    assert filter_events([e], NOW) == [e]
