"""Helpers for the daily stock-guidance analysis (written by a scheduled Claude session).

    python -m newsbot.analysis context 2026-10-27   # coverage list, quotes and headline leads
    python -m newsbot.analysis check analysis/2026-10-27.json
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from . import config

ROOT = Path(__file__).resolve().parent.parent
VIEWS = {"利好", "利空", "中性", "分歧"}
EVENT_FIELDS = ["title", "facts", "impact_path", "magnitude", "priced_in", "guidance", "watch"]


def load_report(day: str) -> dict | None:
    """The news report for `day`, from a local build or the site-data branch."""
    local = ROOT / "site" / "data" / f"{day}.json"
    if local.exists():
        return json.loads(local.read_text())
    subprocess.run(["git", "fetch", "-q", "origin", "site-data"], cwd=ROOT, check=False)
    out = subprocess.run(["git", "show", f"origin/site-data:data/{day}.json"], cwd=ROOT,
                         capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 else None


def context(day: str) -> str:
    report = load_report(day)
    quotes = (report or {}).get("coverage_quotes", {})
    lines = [f"# 报告日 {day}"]
    if report:
        lines.append(f"新闻窗口（美东）：{report['window']['start']} → {report['window']['end']}")
        lines.append("\n## 指数与板块")
        for q in report["market"] + report["sectors"]:
            lines.append(f"- {q['name']} ({q['symbol']}): {q['close']} ({q['change_pct']:+.2f}%)")
    else:
        lines.append("（未找到当日新闻数据，需全部依靠检索）")
    for cat in config.CATEGORIES:
        lines.append(f"\n## {cat['name']} [{cat['key']}]")
        lines.append("覆盖个股（代码 | 名称 | 关键变量 | 当日涨跌）：")
        for ticker, name, drivers in config.COVERAGE[cat["key"]]:
            q = quotes.get(ticker)
            move = f"{q['change_pct']:+.2f}% 收 {q['close']}" if q and q.get("change_pct") is not None else "无行情"
            lines.append(f"- {ticker} | {name} | {drivers} | {move}")
        section = next((s for s in (report or {}).get("sections", []) if s["key"] == cat["key"]), None)
        if section:
            lines.append("新闻线索：")
            for it in section["items"]:
                lines.append(f"- [{it['published'][:16]}] {it['source']}: {it['title']} <{it['url']}>")
    return "\n".join(lines)


def check(doc: dict) -> list[str]:
    errors = []

    def need(cond, msg):
        if not cond:
            errors.append(msg)

    def text(obj, key, where):
        need(isinstance(obj.get(key), str) and obj[key].strip(), f"{where}.{key} 必须是非空字符串")

    need(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(doc.get("date", "")))), "date 必须是 YYYY-MM-DD")
    for key in ("window", "headline", "summary"):
        text(doc, key, "root")
    for key in ("risks", "opportunities"):
        need(isinstance(doc.get(key), list) and all(isinstance(x, str) for x in doc.get(key, [])),
             f"{key} 必须是字符串数组")
    for i, c in enumerate(doc.get("calendar", [])):
        for key in ("date", "event"):
            text(c, key, f"calendar[{i}]")
    need(isinstance(doc.get("self_check"), list) and doc["self_check"], "self_check 不能为空")
    for i, c in enumerate(doc.get("self_check", [])):
        text(c, "item", f"self_check[{i}]")
        need(isinstance(c.get("ok"), bool), f"self_check[{i}].ok 必须是 true/false")

    sectors = {s.get("key"): s for s in doc.get("sectors", [])}
    for cat in config.CATEGORIES:
        key = cat["key"]
        s = sectors.get(key)
        if s is None:
            errors.append(f"缺少板块 {key}")
            continue
        text(s, "overview", key)
        covered = set()
        for j, ev in enumerate(s.get("events", [])):
            where = f"{key}.events[{j}]"
            for f in EVENT_FIELDS:
                text(ev, f, where)
            need(ev.get("view") in VIEWS, f"{where}.view 必须是 {'/'.join(sorted(VIEWS))}")
            need(ev.get("importance") in (1, 2, 3, 4, 5), f"{where}.importance 必须是 1-5")
            need(isinstance(ev.get("tickers"), list), f"{where}.tickers 必须是数组")
            covered.update(ev.get("tickers", []))
            sources = ev.get("sources") or []
            need(sources and all(str(x.get("url", "")).startswith("http") and x.get("title") for x in sources),
                 f"{where}.sources 至少一条，且每条有 title 和 http(s) url")
        for j, inst in enumerate(s.get("institutions", [])):
            for f in ("firm", "action", "detail"):
                text(inst, f, f"{key}.institutions[{j}]")
            need(str(inst.get("url", "")).startswith("http"), f"{key}.institutions[{j}].url 必须是链接")
        need(s.get("institutions") or (isinstance(s.get("institutions_note"), str) and s["institutions_note"]),
             f"{key}: institutions 为空时须写 institutions_note（如“未发现可靠公开更新”）")
        covered.update(s.get("quiet", []))
        missing = [t for t, _, _ in config.COVERAGE[key] if t not in covered]
        need(not missing, f"{key}: 覆盖个股未出现在任何事件或 quiet 中：{', '.join(missing)}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("context").add_argument("date", type=date.fromisoformat)
    sub.add_parser("check").add_argument("file", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "context":
        print(context(args.date.isoformat()))
        return 0
    try:
        doc = json.loads(args.file.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"无法读取 JSON：{exc}")
        return 1
    errors = check(doc)
    for e in errors:
        print("✗", e)
    if not errors:
        print("✓ 格式检查通过")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
