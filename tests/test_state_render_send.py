import json
from datetime import date, datetime

from digest.models import KST, Event
from digest.render import render_html
from digest.send import send_email
from digest.state import exclude_sent, load_sent, save_sent


def ev(title, day, topics, url=None, online=False, location="서울 강남구"):
    return Event(title, url or f"https://x/{title}", datetime(2026, 12, day, 10, tzinfo=KST), None,
                 location, online, "s", topics=topics, summary=f"{title} 요약")


def test_exclude_sent_removes_known_urls():
    a, b = ev("a", 1, []), ev("b", 2, [])
    assert exclude_sent([a, b], {a.url}) == [b]


def test_load_sent_missing_file_is_empty(tmp_path):
    assert load_sent(str(tmp_path / "nope.json")) == set()


def test_save_then_load_roundtrip(tmp_path):
    p = str(tmp_path / "state" / "sent.json")
    save_sent({"https://b", "https://a"}, p)
    assert load_sent(p) == {"https://a", "https://b"}
    assert json.loads(open(p).read()) == ["https://a", "https://b"]


def test_render_groups_by_topic_sorted_by_start():
    html = render_html([ev("late-ai", 20, ["ai"]), ev("early-ai", 5, ["ai"]), ev("ops", 3, ["devops"])],
                       [], date(2026, 11, 16), topic_order=["ai", "devops"])
    assert html.index("early-ai") < html.index("late-ai")
    assert html.index("late-ai") < html.index("ops")
    assert "https://x/ops" in html and "ops 요약" in html


def test_render_empty_says_no_new_events():
    assert "이번 주 신규 행사 없음" in render_html([], [], date(2026, 11, 16))


def test_render_lists_failed_sources():
    html = render_html([], ["onoffmix"], date(2026, 11, 16))
    assert "onoffmix" in html


def test_render_escapes_html_in_titles():
    html = render_html([ev("<script>x</script>", 3, ["ai"])], [], date(2026, 11, 16))
    assert "<script>x" not in html


def test_send_email_builds_message(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port):
            sent["addr"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def login(self, u, p):
            sent["login"] = (u, p)

        def send_message(self, msg):
            sent["msg"] = msg

    monkeypatch.setattr("digest.send.smtplib.SMTP_SSL", FakeSMTP)
    for k, v in {"SMTP_HOST": "h", "SMTP_PORT": "465", "SMTP_USER": "u@x", "SMTP_PASSWORD": "pw", "MAIL_TO": "me@x"}.items():
        monkeypatch.setenv(k, v)
    send_email("<p>hi</p>", "제목")
    assert sent["addr"] == ("h", 465) and sent["login"] == ("u@x", "pw")
    msg = sent["msg"]
    assert msg["To"] == "me@x" and msg["Subject"] == "제목"
    assert "<p>hi</p>" in msg.get_body(("html",)).get_content()
