"""Fetch RSS feeds and route items into categories."""

import calendar
import html
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import requests

from . import config

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"[a-z0-9$&.]+")
STOPWORDS = {"the", "and", "for", "with", "from", "after", "into", "over", "amid", "its", "says", "said",
             "will", "has", "have", "are", "was", "new", "how", "why", "what", "this", "that", "stock", "stocks"}
SPACE_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def fetch_feed(url: str, days: int) -> list[dict]:
    url = url.replace("{days}", str(days))
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("feed failed: %s (%s)", urlparse(url).netloc, exc)
        return []
    parsed = feedparser.parse(resp.content)
    host = urlparse(url).netloc
    feed_title = config.FEED_SOURCES.get(host) or _clean(parsed.feed.get("title", "")) or host
    items = []
    for entry in parsed.entries:
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        title = _clean(entry.get("title", ""))
        link = entry.get("link", "")
        if not stamp or not title or not link.startswith(("http://", "https://")):
            continue
        source = _clean(entry.get("source", {}).get("title", "")) if "source" in entry else ""
        # Google News titles end with " - Publisher".
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3].rstrip()
        summary = _clean(entry.get("summary", ""))
        if summary.startswith(title[:40]):  # Google News repeats the title as summary
            summary = ""
        items.append({
            "title": title,
            "url": link,
            "source": source or feed_title,
            "published": datetime.fromtimestamp(calendar.timegm(stamp), timezone.utc),
            "summary": summary[:400],
        })
    return items


def _matches(text: str, keywords: list[str]) -> int:
    text = f" {text.lower()} "
    return sum(1 for kw in keywords if kw in text)


def _source_weight(source: str) -> int:
    source = source.lower()
    return next((w for w, names in config.SOURCE_WEIGHTS.items() if any(n in source for n in names)), 0)


def _words(title: str) -> set[str]:
    return {w for w in WORD_RE.findall(title.lower()) if len(w) > 2 and w not in STOPWORDS}


def rank(items: list[dict], keywords: list[str]) -> list[dict]:
    """Order by publisher quality and relevance, dropping near-duplicate headlines."""
    def score(it):
        text = it["title"] + " " + it["summary"]
        foreign = _matches(it["title"], config.FOREIGN_TERMS) and not _matches(text, config.US_TERMS)
        return 3 * _source_weight(it["source"]) + min(3, _matches(text, keywords)) - (10 if foreign else 0)

    ordered = sorted(items, key=lambda it: (score(it), it["published"]), reverse=True)
    kept, kept_words = [], []
    for it in ordered:
        words = _words(it["title"])
        if any(words and len(words & other) / len(words | other) >= 0.5 for other in kept_words):
            continue
        kept.append(it)
        kept_words.append(words)
    return kept


def collect(window_start: datetime, window_end: datetime) -> dict[str, list[dict]]:
    """Return {category_key: [items]} restricted to the window, best first."""
    days = max(1, min(7, (datetime.now(timezone.utc) - window_start).days + 1))
    jobs = [(c["key"], url) for c in config.CATEGORIES for url in c["feeds"]]
    jobs += [(None, url) for url in config.GENERAL_FEEDS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: fetch_feed(job[1], days), jobs))

    buckets: dict[str, dict[str, dict]] = {c["key"]: {} for c in config.CATEGORIES}
    dedicated: set[tuple[str, str]] = set()  # (category, title) found via that category's own feed
    seen_any = 0
    for (cat_key, _), items in zip(jobs, results):
        for item in items:
            if not (window_start <= item["published"] < window_end):
                continue
            seen_any += 1
            if cat_key:
                targets = [cat_key]
            else:
                text = item["title"] + " " + item["summary"]
                scores = {c["key"]: _matches(text, c["keywords"]) for c in config.CATEGORIES}
                best = max(scores.values())
                targets = [k for k, s in scores.items() if s and s == best]
            norm = _norm_title(item["title"])
            for key in targets:
                buckets[key].setdefault(norm, item)
                if cat_key:
                    dedicated.add((key, norm))
    log.info("fetched %d feeds, %d items in window", len(jobs), seen_any)

    # An item seen in several categories stays only in the one it fits best,
    # preferring categories whose own feeds carried it.
    owner: dict[str, tuple[int, str]] = {}
    for c in config.CATEGORIES:
        for norm, item in buckets[c["key"]].items():
            score = _matches(item["title"] + " " + item["summary"], c["keywords"])
            score += 5 if (c["key"], norm) in dedicated else 0
            if norm not in owner or score > owner[norm][0]:
                owner[norm] = (score, c["key"])
    out = {}
    for c in config.CATEGORIES:
        items = buckets[c["key"]]
        out[c["key"]] = rank([it for norm, it in items.items() if owner[norm][1] == c["key"]], c["keywords"])
    return out
