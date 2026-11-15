import re

from digest.models import Event


def _norm(title: str) -> str:
    return re.sub(r"[\W_]+", "", title.lower())


def dedupe(events: list[Event]) -> list[Event]:
    seen_urls: set[str] = set()
    seen_keys: set[tuple[str, object]] = set()
    out: list[Event] = []
    for e in events:
        key = (_norm(e.title), e.start.date())
        if e.url in seen_urls or key in seen_keys:
            continue
        seen_urls.add(e.url)
        seen_keys.add(key)
        out.append(e)
    return out
