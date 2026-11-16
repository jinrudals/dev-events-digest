import logging
from typing import Protocol

import httpx

from digest.models import Event

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "dev-events-digest/0.1 (personal weekly digest)"}


class Collector(Protocol):
    name: str

    def fetch(self) -> list[Event]: ...


def http_get(url: str, params: dict | None = None, retries: int = 2) -> str:
    last: Exception | None = None
    for _ in range(retries + 1):
        try:
            r = httpx.get(url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            r.raise_for_status()
            return r.text
        except httpx.HTTPError as e:
            last = e
    raise last  # type: ignore[misc]


def collect_all(collectors: list[Collector] | None = None) -> tuple[list[Event], list[str]]:
    if collectors is None:
        from digest.collectors import ALL_COLLECTORS

        collectors = ALL_COLLECTORS
    events: list[Event] = []
    failed: list[str] = []
    for c in collectors:
        try:
            events.extend(c.fetch())
        except Exception:
            log.exception("collector %s failed", c.name)
            failed.append(c.name)
    return events, failed
