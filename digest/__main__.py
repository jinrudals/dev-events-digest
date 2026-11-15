import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from digest.collectors.base import collect_all
from digest.models import KST
from digest.pipeline.classify import classify, default_llm, load_topics
from digest.pipeline.dedupe import dedupe
from digest.pipeline.filter import filter_events
from digest.render import render_html
from digest.send import send_email
from digest.state import exclude_sent, load_sent, save_sent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="digest")
    ap.add_argument("--dry-run", action="store_true", help="write HTML to --out instead of sending")
    ap.add_argument("--out", default="out/digest.html")
    ap.add_argument("--state", default="state/sent.json")
    ap.add_argument("--topics", default="topics.yaml")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    now = datetime.now(KST)
    raw, failed = collect_all()
    if not raw and failed:
        print(f"all sources failed: {failed}", file=sys.stderr)
        return 1

    sent = load_sent(args.state)
    events = exclude_sent(filter_events(dedupe(raw), now), sent)
    topics = load_topics(args.topics)
    events = classify(events, topics, llm=default_llm)
    html = render_html(events, failed, now.date(), topic_order=[t.name for t in topics])

    if args.dry_run:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out} ({len(events)} events)")
        return 0

    send_email(html, f"[개발자 행사] {now.strftime('%Y-%m-%d')} 주간 소식 ({len(events)}건)")
    save_sent(sent | {e.url for e in events}, args.state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
