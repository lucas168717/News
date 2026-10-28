from newsbot import translate


class Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_translate_sections(monkeypatch):
    def fake_get(url, params, **kw):
        if params["q"] == "boom":
            raise translate.requests.ConnectionError("down")
        return Resp([[["美联储", "Fed", None], ["维持利率", " holds rates", None]], None, "en"])

    monkeypatch.setattr(translate.requests, "get", fake_get)
    sections = [
        {"ai": False, "items": [{"title": "Fed holds rates", "summary": ""}, {"title": "boom", "summary": ""}]},
        {"ai": True, "items": [{"title": "skip me", "summary": "", "title_zh": "已有"}]},
    ]
    assert translate.translate_sections(sections)
    assert sections[0]["items"][0]["title_zh"] == "美联储维持利率"
    assert "title_zh" not in sections[0]["items"][1]
    assert sections[1]["items"][0]["title_zh"] == "已有"
