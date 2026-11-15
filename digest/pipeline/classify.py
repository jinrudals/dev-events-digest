import json
import logging
import os
import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx
import yaml

from digest.models import Event

log = logging.getLogger(__name__)

BATCH = 20
MODELS_URL = "https://models.github.ai/inference/chat/completions"
MODEL = "openai/gpt-4o-mini"


@dataclass
class Topic:
    name: str
    description: str
    keywords: list[str]


def load_topics(path: str = "topics.yaml") -> list[Topic]:
    with open(path, encoding="utf-8") as f:
        return [Topic(t["name"], t.get("description", ""), t.get("keywords", [])) for t in yaml.safe_load(f)["topics"]]


def _matches(keyword: str, text: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])", text) is not None


def keyword_classify(event: Event, topics: list[Topic]) -> list[str]:
    text = f"{event.title} {event.description}".lower()
    found = [t.name for t in topics if any(_matches(k, text) for k in t.keywords)]
    return found or ["other"]


def _first_sentence(text: str) -> str:
    m = re.match(r"\s*(.+?[.!?。])(?:\s|$)", text, re.S)
    return (m.group(1) if m else text).strip()[:200]


def default_llm(prompt: str) -> str:
    r = httpx.post(
        MODELS_URL,
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _prompt(batch: list[Event], topics: list[Topic]) -> str:
    topic_lines = "\n".join(f"- {t.name}: {t.description}" for t in topics)
    items = [{"url": e.url, "title": e.title, "description": e.description[:300]} for e in batch]
    return (
        "개발자 행사 목록을 주제별로 분류하고 한국어 한 줄 요약(60자 이내)을 작성하세요.\n"
        f"사용 가능한 주제(이 이름만 사용, 복수 가능, 해당 없으면 빈 배열):\n{topic_lines}\n\n"
        '출력은 JSON 배열만: [{"url": "...", "topics": ["..."], "summary": "..."}]\n\n'
        f"행사:\n{json.dumps(items, ensure_ascii=False)}"
    )


def _parse(raw: str) -> dict[str, dict]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    return {d["url"]: d for d in json.loads(text) if isinstance(d, dict) and "url" in d}


def classify(events: list[Event], topics: list[Topic], llm: Callable[[str], str] = default_llm) -> list[Event]:
    valid = {t.name for t in topics}
    for i in range(0, len(events), BATCH):
        batch = events[i : i + BATCH]
        try:
            results = _parse(llm(_prompt(batch, topics)))
        except Exception:
            log.exception("LLM classification failed; using keyword fallback")
            results = {}
        for e in batch:
            r = results.get(e.url, {})
            llm_topics = [t for t in r.get("topics", []) if t in valid] if isinstance(r.get("topics"), list) else []
            e.topics = llm_topics or keyword_classify(e, topics)
            summary = r.get("summary")
            e.summary = summary.strip() if isinstance(summary, str) and summary.strip() else _first_sentence(e.description)
    return events
