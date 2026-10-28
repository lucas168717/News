"""Closing prices for the market snapshot (Yahoo Finance chart API, best effort)."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

import requests

from .fetch import USER_AGENT
from .trading_calendar import ET

log = logging.getLogger(__name__)
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"


def quote(symbol: str, name: str, day: date) -> dict | None:
    try:
        resp = requests.get(CHART_URL.format(symbol=symbol), headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        stamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        log.warning("quote failed: %s (%s)", symbol, exc)
        return None
    bars = [(datetime.fromtimestamp(t, ET).date(), c) for t, c in zip(stamps, closes) if c is not None]
    bars = [b for b in bars if b[0] <= day]
    if len(bars) < 2:
        return None
    (bar_day, close), (_, prev) = bars[-1], bars[-2]
    return {
        "symbol": symbol,
        "name": name,
        "date": bar_day.isoformat(),
        "close": round(close, 4),
        "change": round(close - prev, 4),
        "change_pct": round((close - prev) / prev * 100, 2) if prev else None,
    }


def snapshot(symbols: list[tuple[str, str]], day: date) -> list[dict]:
    with ThreadPoolExecutor(max_workers=6) as pool:
        quotes = pool.map(lambda s: quote(s[0], s[1], day), symbols)
    return [q for q in quotes if q]
