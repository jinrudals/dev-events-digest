from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from digest.models import Event

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html", "j2"]),
)


def render_html(
    events: list[Event],
    failed_sources: list[str],
    today: date,
    topic_order: list[str] | None = None,
) -> str:
    groups: dict[str, list[Event]] = {}
    for e in sorted(events, key=lambda e: e.start):
        groups.setdefault(e.topics[0] if e.topics else "other", []).append(e)
    order = topic_order or sorted(groups)
    rank = {name: i for i, name in enumerate(order)}
    names = sorted(groups, key=lambda n: (n == "other", rank.get(n, len(rank)), n))
    sections = [(n, groups[n]) for n in names]
    return _env.get_template("digest.html.j2").render(
        sections=sections, failed_sources=failed_sources, today=today
    )
