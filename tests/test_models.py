from datetime import timedelta, timezone

from digest.models import KST, parse_kst


def test_parse_kst_naive_gets_kst():
    assert parse_kst("2026-12-01T14:00").tzinfo == KST


def test_parse_kst_keeps_explicit_offset():
    dt = parse_kst("2026-12-01T14:00:00+00:00")
    assert dt.utcoffset() == timedelta(0)
    assert dt.tzinfo == timezone.utc
