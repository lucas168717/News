from datetime import datetime, timezone

from newsbot import config, fetch

GOOGLE_RSS = b"""<?xml version="1.0"?><rss><channel><title>Google News</title>
<item><title>Lockheed Martin wins $2 billion missile contract - Reuters</title>
<link>https://news.google.com/a</link><pubDate>Tue, 27 Oct 2026 15:00:00 GMT</pubDate>
<description>Lockheed Martin wins $2 billion missile contract</description>
<source url="https://reuters.com">Reuters</source></item>
<item><title>Old story - Reuters</title><link>https://news.google.com/b</link>
<pubDate>Mon, 19 Oct 2026 15:00:00 GMT</pubDate><source url="https://reuters.com">Reuters</source></item>
</channel></rss>"""

GENERAL_RSS = b"""<?xml version="1.0"?><rss><channel><title>Top News</title>
<item><title>Fed signals rate cut as inflation cools</title><link>https://example.com/fed</link>
<pubDate>Tue, 27 Oct 2026 18:00:00 GMT</pubDate><description>Powell said &lt;b&gt;inflation&lt;/b&gt; eased.</description></item>
<item><title>Waymo expands robotaxi service</title><link>https://example.com/waymo</link>
<pubDate>Tue, 27 Oct 2026 19:00:00 GMT</pubDate></item>
</channel></rss>"""


class Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_collect_routes_and_filters(monkeypatch):
    def fake_get(url, **kw):
        if "Lockheed" in url:
            assert "when:2d" in url
            return Resp(GOOGLE_RSS)
        if url == config.GENERAL_FEEDS[0]:
            return Resp(GENERAL_RSS)
        return Resp(b"<rss><channel></channel></rss>")

    class FixedNow(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 27, 22, tzinfo=timezone.utc)

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    monkeypatch.setattr(fetch, "datetime", FixedNow)
    out = fetch.collect(datetime(2026, 10, 26, 20, tzinfo=timezone.utc), datetime(2026, 10, 28, 4, tzinfo=timezone.utc))
    assert [it["title"] for it in out["defense"]] == ["Lockheed Martin wins $2 billion missile contract"]
    assert out["defense"][0]["source"] == "Reuters"
    assert [it["title"] for it in out["macro"]] == ["Fed signals rate cut as inflation cools"]
    assert out["macro"][0]["summary"] == "Powell said inflation eased."
    assert [it["title"] for it in out["autonomy"]] == ["Waymo expands robotaxi service"]


def _item(title, source, hour=12):
    return {"title": title, "source": source, "summary": "", "url": "https://x",
            "published": datetime(2026, 10, 27, hour, tzinfo=timezone.utc)}


def test_rank_prefers_quality_and_drops_near_duplicates():
    items = [
        _item("Tiny blog reposts Fed news", "shattered.io", hour=20),
        _item("Fed holds rates steady, signals patience", "Reuters", hour=10),
        _item("Fed holds rates steady and signals patience", "Some Blog", hour=11),
        _item("Treasury yields slip after Fed decision", "CNBC", hour=9),
    ]
    ranked = [it["title"] for it in fetch.rank(items, ["fed"])]
    assert ranked == [
        "Fed holds rates steady, signals patience",
        "Treasury yields slip after Fed decision",
        "Tiny blog reposts Fed news",
    ]


def test_rank_demotes_foreign_only_headlines():
    items = [
        _item("Australian inflation runs hot, RBA hike bets rise", "Reuters"),
        _item("Fed seen cutting rates as US inflation cools", "Some Blog"),
    ]
    assert fetch.rank(items, ["inflation"])[0]["title"].startswith("Fed seen")
