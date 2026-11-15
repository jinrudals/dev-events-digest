import json
from datetime import datetime

from digest.models import KST, Event
from digest.pipeline.classify import Topic, classify, keyword_classify, load_topics

TOPICS = [
    Topic("ai", "AI", ["llm", "ai"]),
    Topic("devops", "DevOps", ["devops", "ci/cd"]),
]


def ev(title, url="https://x/1", desc=""):
    return Event(title, url, datetime(2026, 12, 1, tzinfo=KST), None, "서울", False, "s", description=desc)


def test_load_topics_reads_yaml():
    names = [t.name for t in load_topics("topics.yaml")]
    assert {"ai", "devops", "platform-engineering"} <= set(names)


def test_keyword_classify_no_match_is_other():
    assert keyword_classify(ev("Cooking class"), TOPICS) == ["other"]


def test_classify_uses_llm_topics_and_summary():
    e = ev("Some Conf")
    llm = lambda prompt: json.dumps([{"url": e.url, "topics": ["devops"], "summary": "요약입니다"}])
    out = classify([e], TOPICS, llm=llm)
    assert out[0].topics == ["devops"]
    assert out[0].summary == "요약입니다"


def test_classify_drops_unknown_topic_falls_back():
    e = ev("LLM day")
    llm = lambda prompt: json.dumps([{"url": e.url, "topics": ["quantum"], "summary": "s"}])
    out = classify([e], TOPICS, llm=llm)
    assert out[0].topics == ["ai"]


def test_classify_broken_json_falls_back_to_keywords():
    e = ev("DevOps Days", desc="첫 문장입니다. 둘째 문장.")
    out = classify([e], TOPICS, llm=lambda p: "not json {{")
    assert out[0].topics == ["devops"]
    assert out[0].summary == "첫 문장입니다."


def test_classify_llm_exception_falls_back():
    def boom(prompt):
        raise RuntimeError("rate limited")

    out = classify([ev("AI Summit")], TOPICS, llm=boom)
    assert out[0].topics == ["ai"]


def test_classify_accepts_code_fenced_json():
    e = ev("Some Conf")
    payload = json.dumps([{"url": e.url, "topics": ["ai"], "summary": "ok"}])
    out = classify([e], TOPICS, llm=lambda p: f"```json\n{payload}\n```")
    assert out[0].topics == ["ai"] and out[0].summary == "ok"
