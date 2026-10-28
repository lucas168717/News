from newsbot import analysis, config


def _quiet_doc():
    return {
        "date": "2026-10-27", "window": "w", "headline": "h", "summary": "s",
        "risks": [], "opportunities": [], "calendar": [],
        "self_check": [{"item": "x", "ok": True, "note": ""}],
        "sectors": [{"key": c["key"], "events": [], "institutions": [],
                     "quiet": [t for t, _, _ in config.COVERAGE[c["key"]]]} for c in config.CATEGORIES],
    }


def test_quiet_day_is_valid():
    assert analysis.check(_quiet_doc()) == []


def test_every_covered_stock_must_be_checked():
    doc = _quiet_doc()
    doc["sectors"][2]["quiet"].remove("LMT")
    assert analysis.check(doc) == ["defense: 覆盖个股未出现在任何事件或 quiet 中：LMT"]


def test_event_needs_sources_and_overview():
    doc = _quiet_doc()
    doc["sectors"][0]["events"] = [{
        "title": "t", "tickers": ["SPY"], "importance": 3, "view": "中性", "facts": "f",
        "impact_path": "i", "magnitude": "m", "priced_in": "p", "guidance": "g", "watch": "w", "sources": [],
    }]
    errors = analysis.check(doc)
    assert any("macro.overview" in e for e in errors)
    assert any("sources" in e for e in errors)
