import json
from datetime import datetime, timedelta

from digest import __main__ as cli
from digest.models import KST, Event


def _event():
    return Event("AI Conf", "https://x/1", datetime.now(KST) + timedelta(days=5), None,
                 "서울 강남구", False, "s", description="AI 컨퍼런스. 둘째.")


def _patch(monkeypatch, events, failed=()):
    monkeypatch.setattr(cli, "collect_all", lambda: (list(events), list(failed)))
    monkeypatch.setattr(cli, "default_llm", lambda p: (_ for _ in ()).throw(RuntimeError("no llm")))


def _args(tmp_path, *extra):
    return ["--state", str(tmp_path / "sent.json"), "--history", str(tmp_path / "history.json"),
            "--site", str(tmp_path / "site"), *extra]


def test_dry_run_writes_html_and_does_not_publish_or_record(monkeypatch, tmp_path):
    _patch(monkeypatch, [_event()])
    out = tmp_path / "digest.html"
    assert cli.main(_args(tmp_path, "--dry-run", "--out", str(out))) == 0
    assert "AI Conf" in out.read_text(encoding="utf-8")
    assert not (tmp_path / "sent.json").exists() and not (tmp_path / "site").exists()


def test_run_publishes_site_and_records_sent(monkeypatch, tmp_path):
    _patch(monkeypatch, [_event()])
    assert cli.main(_args(tmp_path)) == 0
    assert "AI Conf" in (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "sent.json").read_text()) == ["https://x/1"]
    assert len(json.loads((tmp_path / "history.json").read_text())) == 1


def test_records_sent_only_after_successful_publish(monkeypatch, tmp_path):
    _patch(monkeypatch, [_event()])

    def boom(*a, **k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(cli, "write_site", boom)
    try:
        cli.main(_args(tmp_path))
    except RuntimeError:
        pass
    assert not (tmp_path / "sent.json").exists()


def test_second_run_publishes_empty_week_and_keeps_history(monkeypatch, tmp_path):
    _patch(monkeypatch, [_event()])
    cli.main(_args(tmp_path))
    cli.main(_args(tmp_path))
    assert "이번 주 신규 행사 없음" in (tmp_path / "site" / "index.html").read_text(encoding="utf-8")


def test_all_sources_failed_exits_nonzero_without_publishing(monkeypatch, tmp_path):
    _patch(monkeypatch, [], failed=["a", "b"])
    assert cli.main(_args(tmp_path)) == 1
    assert not (tmp_path / "site").exists()
