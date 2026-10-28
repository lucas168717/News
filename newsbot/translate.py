"""Free English -> Chinese machine translation (Google Translate web endpoint, best effort).

Used only when Claude summaries are unavailable.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from .fetch import USER_AGENT

log = logging.getLogger(__name__)
URL = "https://translate.googleapis.com/translate_a/single"


def translate(text: str) -> str | None:
    if not text:
        return None
    try:
        resp = requests.get(
            URL,
            params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": text},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        return "".join(part[0] for part in resp.json()[0] if part and part[0]).strip() or None
    except (requests.RequestException, ValueError, TypeError, IndexError) as exc:
        log.debug("translate failed: %s", exc)
        return None


def translate_sections(sections: list[dict]) -> bool:
    """Add title_zh / summary_zh to items of non-Claude sections. Returns True if any succeeded."""
    jobs = [(it, field) for s in sections if not s["ai"] for it in s["items"]
            for field in ("title", "summary") if it.get(field)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda job: translate(job[0][job[1]]), jobs))
    for (item, field), zh in zip(jobs, results):
        if zh:
            item[field + "_zh"] = zh
    done = sum(1 for zh in results if zh)
    log.info("machine-translated %d/%d texts", done, len(jobs))
    return done > 0
