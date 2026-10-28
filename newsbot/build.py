"""Build the encrypted daily news site.

    python -m newsbot.build --site-dir site            # latest trading day
    python -m newsbot.build --site-dir site --date 2026-10-27 --force
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from . import config, crypto, fetch, market, summarize
from .trading_calendar import ET, is_trading_day, latest_trading_day, news_window

log = logging.getLogger("newsbot")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class Site:
    """Encrypted site directory: index.html, meta.json, data/manifest.json, data/<date>.json."""

    def __init__(self, root: Path, password: str):
        self.root = root
        self.data = root / "data"
        meta_path = root / "meta.json"
        key = None
        if meta_path.exists():
            self.meta = json.loads(meta_path.read_text())
            key = crypto.key_for_meta(password, self.meta)
            if key is None:
                log.warning("PAGE_PASSWORD changed: old archive can't be decrypted and is discarded")
                shutil.rmtree(self.data, ignore_errors=True)
        if key is None:
            self.meta, key = crypto.new_meta(password)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(json.dumps(self.meta, indent=1))
        self.key = key
        self.data.mkdir(parents=True, exist_ok=True)

    def _read(self, name: str):
        path = self.data / name
        return crypto.decrypt(self.key, json.loads(path.read_text())) if path.exists() else None

    def _write(self, name: str, obj) -> None:
        (self.data / name).write_text(json.dumps(crypto.encrypt(self.key, obj)))

    def has_day(self, day: date) -> bool:
        return (self.data / f"{day.isoformat()}.json").exists()

    def save_day(self, report: dict) -> None:
        self._write(f"{report['date']}.json", report)
        manifest = [m for m in (self._read("manifest.json") or []) if m["date"] != report["date"]]
        manifest.append({
            "date": report["date"],
            "headline": report.get("headline"),
            "count": sum(len(s["items"]) for s in report["sections"]),
        })
        manifest.sort(key=lambda m: m["date"], reverse=True)
        self._write("manifest.json", manifest)

    def write_static(self) -> None:
        for name in ("index.html", "robots.txt"):
            shutil.copy(WEB_DIR / name, self.root / name)
        (self.root / ".nojekyll").touch()


def build_report(day: date) -> dict:
    start, end = news_window(day)
    log.info("trading day %s, window %s -> %s", day, start.isoformat(), end.isoformat())
    buckets = fetch.collect(start, end)
    quotes = market.snapshot(config.MARKET_SYMBOLS, day)
    sectors = market.snapshot(config.SECTOR_SYMBOLS, day)
    sections, digest = summarize.summarize(day.isoformat(), buckets, quotes + sectors)
    return {
        "date": day.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "model": summarize.MODEL if any(s["ai"] for s in sections) else None,
        "headline": digest["headline"] if digest else None,
        "key_points": digest["key_points"] if digest else [],
        "market": quotes,
        "sectors": sectors,
        "sections": sections,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site-dir", default="site", type=Path)
    parser.add_argument("--date", type=date.fromisoformat, help="trading day (default: latest)")
    parser.add_argument("--force", action="store_true", help="rebuild even if the day exists")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    password = os.environ.get("PAGE_PASSWORD", "")
    if len(password) < 8:
        log.error("set PAGE_PASSWORD (at least 8 characters)")
        return 2

    day = args.date or latest_trading_day(datetime.now(ET))
    if not is_trading_day(day):
        log.error("%s is not an NYSE trading day", day)
        return 2

    site = Site(args.site_dir, password)
    site.write_static()
    if site.has_day(day) and not args.force:
        log.info("%s already built; use --force to rebuild", day)
        return 0
    if not summarize.enabled():
        log.warning("ANTHROPIC_API_KEY not set: publishing English headlines without Chinese summaries")
    report = build_report(day)
    if not any(s["items"] for s in report["sections"]):
        log.error("no news fetched for %s; keeping the site unchanged", day)
        return 1
    site.save_day(report)
    log.info("built %s: %d stories", day, sum(len(s["items"]) for s in report["sections"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
