"""Chinese summaries and story selection with Claude (optional)."""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import anthropic

from . import config

log = logging.getLogger(__name__)

MODEL = os.environ.get("NEWSBOT_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("NEWSBOT_EFFORT", "medium")

SYSTEM = (
    "你是一名服务中国投资者的美股资深分析师。你会收到某一美股交易日的英文新闻列表，"
    "需要用简体中文为私人投资简报整理内容。要求：只依据给出的新闻，不编造事实或数字；"
    "公司名可保留英文或常用中文名，股票代码用大写英文；语言精炼、信息密度高。"
)

CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {"type": "array", "items": {"type": "string"}},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title_zh": {"type": "string"},
                    "summary_zh": {"type": "string"},
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "impact": {"type": "string", "enum": ["利好", "利空", "中性"]},
                    "importance": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
                },
                "required": ["id", "title_zh", "summary_zh", "tickers", "impact", "importance"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["overview", "items"],
    "additionalProperties": False,
}

DIGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "key_points"],
    "additionalProperties": False,
}


def enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def _ask(client: anthropic.Anthropic, prompt: str, schema: dict) -> dict | None:
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason != "end_turn":
        log.warning("Claude stopped with %s", message.stop_reason)
        return None
    text = next((b.text for b in message.content if b.type == "text"), "")
    return json.loads(text)


def _category(client, day: str, category: dict, items: list[dict]) -> dict | None:
    listing = [
        {
            "id": i,
            "title": it["title"],
            "source": it["source"],
            "published_utc": it["published"].strftime("%Y-%m-%d %H:%M"),
            "snippet": it["summary"][:300],
        }
        for i, it in enumerate(items)
    ]
    prompt = (
        f"交易日：{day}（美东时间）\n板块：{category['name']}\n\n"
        "以下是该板块在本交易日窗口内（前一交易日收盘后至当日结束）抓取到的新闻：\n"
        f"{json.dumps(listing, ensure_ascii=False)}\n\n"
        "任务：\n"
        "1. overview：用 3-5 条中文要点概括该板块本交易日最重要的动态及对美股的含义。\n"
        "2. items：挑选对美股投资者最有价值的 6-12 条新闻（同一事件只保留信息最完整的一条，"
        "剔除与本板块无关、纯广告或过时的内容），按重要性从高到低排列。每条给出：id（原列表编号）、"
        "title_zh（中文标题）、summary_zh（1-2 句中文要点，说明发生了什么和为什么重要）、"
        "tickers（相关美股代码，可为空）、impact（对相关股票：利好/利空/中性）、importance（1-5）。\n"
        "如果新闻很少，可以少于 6 条；没有相关新闻时 items 为空、overview 说明当日无重要动态。"
    )
    try:
        return _ask(client, prompt, CATEGORY_SCHEMA)
    except (anthropic.APIError, json.JSONDecodeError) as exc:
        log.warning("Claude summary failed for %s: %s", category["key"], exc)
        return None


def _digest(client, day: str, sections: list[dict], market: list[dict]) -> dict | None:
    brief = {
        "market": [{k: q[k] for k in ("name", "close", "change_pct")} for q in market],
        "sections": [
            {"name": s["name"], "overview": s["overview"], "top": [it["title_zh"] for it in s["items"][:4]]}
            for s in sections
        ],
    }
    prompt = (
        f"交易日：{day}。以下是当日美股市场数据和各板块新闻要点：\n"
        f"{json.dumps(brief, ensure_ascii=False)}\n\n"
        "请输出：headline（一句话概括当日美股主线，30 字以内）；"
        "key_points（4-6 条全市场最值得关注的要点，可跨板块，必要时引用指数涨跌）。"
    )
    try:
        return _ask(client, prompt, DIGEST_SCHEMA)
    except (anthropic.APIError, json.JSONDecodeError) as exc:
        log.warning("Claude digest failed: %s", exc)
        return None


def summarize(day: str, buckets: dict[str, list[dict]], market: list[dict]) -> tuple[list[dict], dict | None]:
    """Return (sections, digest). Sections fall back to plain headlines per category."""
    client = anthropic.Anthropic(max_retries=3) if enabled() else None
    candidates = {c["key"]: buckets.get(c["key"], [])[: config.MAX_CANDIDATES] for c in config.CATEGORIES}

    results: list[dict | None] = [None] * len(config.CATEGORIES)
    if client:
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(
                lambda c: _category(client, day, c, candidates[c["key"]]) if candidates[c["key"]] else None,
                config.CATEGORIES,
            ))

    sections = []
    for category, result in zip(config.CATEGORIES, results):
        items = candidates[category["key"]]
        section = {"key": category["key"], "name": category["name"], "icon": category["icon"], "ai": False,
                   "overview": [], "items": []}
        if result is not None:
            section["ai"] = True
            section["overview"] = result["overview"]
            for pick in result["items"]:
                if 0 <= pick["id"] < len(items):
                    section["items"].append({**_plain(items[pick["id"]]), **{k: pick[k] for k in pick if k != "id"}})
        else:
            section["items"] = [_plain(it) for it in items[: config.MAX_ITEMS_PLAIN]]
        sections.append(section)

    digest = None
    if client and any(s["ai"] for s in sections):
        digest = _digest(client, day, [s for s in sections if s["ai"]], market)
    return sections, digest


def _plain(item: dict) -> dict:
    return {
        "title": item["title"],
        "url": item["url"],
        "source": item["source"],
        "published": item["published"].isoformat(),
        "summary": item["summary"],
    }
