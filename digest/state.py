import json
import os

from digest.models import Event


def load_sent(path: str = "state/sent.json") -> set[str]:
    try:
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_sent(urls: set[str], path: str = "state/sent.json") -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False, indent=2)
        f.write("\n")


def exclude_sent(events: list[Event], sent: set[str]) -> list[Event]:
    return [e for e in events if e.url not in sent]
