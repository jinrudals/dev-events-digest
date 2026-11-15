from datetime import datetime, timedelta, timezone
from pathlib import Path

from digest.collectors import cncf, devevent, onoffmix
from digest.collectors.base import collect_all
from digest.models import KST, Event

FIX = Path(__file__).parent / "fixtures"


def test_devevent_parses_fixture():
    events = devevent.parse((FIX / "devevent.md").read_text(encoding="utf-8"))
    first = events[0]
    assert first.title == "Furiosa Developer Meetup"
    assert first.url == "https://luma.com/1kshcws3"
    assert first.start == datetime(2026, 11, 12, 16, 0, tzinfo=KST)
    assert first.end == datetime(2026, 11, 12, 19, 0, tzinfo=KST)
    assert first.online is False
    assert "서울 강남구" in first.location
    assert "AI" in first.description
    assert first.source == "dev-event"


def test_devevent_registration_only_entry_uses_deadline_and_online_flag():
    events = devevent.parse((FIX / "devevent.md").read_text(encoding="utf-8"))
    second = events[1]
    assert second.online is True
    assert second.start == datetime(2026, 11, 12, 10, 0, tzinfo=KST)


def test_onoffmix_parses_fixture():
    events = onoffmix.parse((FIX / "onoffmix.html").read_text(encoding="utf-8"))
    assert len(events) == 6
    first = events[0]
    assert first.title.startswith("[KIIN 포럼]")
    assert first.url == "https://onoffmix.com/event/352698"
    assert first.start == datetime(2026, 11, 18, 0, 0, tzinfo=KST)
    assert first.end == datetime(2026, 11, 18, 23, 59, tzinfo=KST)
    assert first.location == "서울특별시 강남구"
    assert first.online is False
    multi = events[2]
    assert multi.end == datetime(2026, 11, 18, 21, 40, tzinfo=KST)
    assert "&lt;" not in multi.title


def test_cncf_parses_fixture():
    events = cncf.parse((FIX / "cncf.json").read_text(encoding="utf-8"))
    assert len(events) == 5
    first = events[0]
    assert first.title.startswith("KCD Porto 2026")
    assert first.start == datetime(2026, 11, 19, 9, 0, tzinfo=timezone.utc)
    assert "Porto" in first.location
    assert first.online is False
    assert first.source == "cncf"


class _Ok:
    name = "ok"

    def fetch(self):
        t = datetime(2026, 12, 1, tzinfo=KST)
        return [Event("a", "https://a", t, None, "Seoul", False, "ok")]


class _Boom:
    name = "boom"

    def fetch(self):
        raise RuntimeError("down")


def test_collect_all_isolates_failure():
    events, failed = collect_all([_Boom(), _Ok()])
    assert [e.title for e in events] == ["a"]
    assert failed == ["boom"]
