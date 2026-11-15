import json
from datetime import datetime, timedelta

from digest import __main__ as cli
from digest.models import KST, Event


def _event():
    return Event("AI Conf", "https://x/1", datetime.now(KST) + timedelta(days=5), None,
                 "서울 강남구", False, "s", description="AI 컨퍼런스. 둘째.")


def _patch(monkeypatch, events, failed=(), sent=None):
    monkeypatch.setattr(cli, "collect_all", lambda: (list(events), list(failed)))
    monkeypatch.setattr(cli, "default_llm", lambda p: (_ for _ in ()).throw(RuntimeError("no llm")))
    sent = sent if sent is not None else []
    monkeypatch.setattr(cli, "send_email", lambda html, subject: sent.append((html, subject)))
    return sent


def test_dry_run_writes_html_and_does_not_send_or_record(monkeypatch, tmp_path):
    sent = _patch(monkeypatch, [_event()])
    out, state = tmp_path / "digest.html", tmp_path / "sent.json"
    assert cli.main(["--dry-run", "--out", str(out), "--state", str(state)]) == 0
    assert "AI Conf" in out.read_text(encoding="utf-8")
    assert sent == [] and not state.exists()


def test_run_records_sent_only_after_successful_send(monkeypatch, tmp_path):
    state = tmp_path / "sent.json"
    _patch(monkeypatch, [_event()])

    def boom(html, subject):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(cli, "send_email", boom)
    try:
        cli.main(["--state", str(state)])
    except RuntimeError:
        pass
    assert not state.exists()

    sent = _patch(monkeypatch, [_event()])
    assert cli.main(["--state", str(state)]) == 0
    assert len(sent) == 1
    assert json.loads(state.read_text()) == ["https://x/1"]
    # second run: already sent -> empty digest still mailed
    sent.clear()
    assert cli.main(["--state", str(state)]) == 0
    assert "이번 주 신규 행사 없음" in sent[0][0]


def test_all_sources_failed_exits_nonzero_without_sending(monkeypatch, tmp_path):
    sent = _patch(monkeypatch, [], failed=["a", "b"])
    assert cli.main(["--state", str(tmp_path / "s.json")]) == 1
    assert sent == []
