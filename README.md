# 美股每日简报

这个网页在每个美股交易日收盘后自动更新，汇总最新交易日的美股新闻，分为六个板块：

🌐 宏观 · 💻 科技 · 🛡️ 国防军工 · 🛒 消费 · 🏦 金融 · 🤖 自动驾驶与人形机器人

另外还有市场快照（主要指数、美债收益率、美元、原油、黄金、比特币，以及各板块 ETF）和全市场要点。

## 工作原理

```
GitHub Actions（每周一至周五 22:15 UTC，即北京时间次日 06:15）
  ├─ 计算最新交易日（NYSE 日历，含节假日），新闻窗口 = 前一交易日 16:00 ET → 当日 24:00 ET
  ├─ 抓取 RSS：Google News 分板块检索、CNBC、MarketWatch、Yahoo Finance、Defense News、
  │           Breaking Defense、The Robot Report 等；按关键词归类、去重
  ├─ 抓取收盘行情（Yahoo Finance）
  ├─ Claude（可选）：每个板块筛选 6–12 条重要新闻，生成中文标题、摘要、相关代码、利好/利空判断，以及板块要点和全市场要点
  └─ 把结果保存到 site-data 分支（保留历史），并部署到 GitHub Pages
```

每天打开同一个网址即可查看，不需要下载任何文件。页面不对搜索引擎开放收录（`noindex` + robots.txt），但知道网址的人都能打开。

## 部署步骤

1. **添加 Claude API Key（推荐）**：Settings → Secrets and variables → Actions → New repository secret，名称 `ANTHROPIC_API_KEY`。用于生成中文摘要和要点；不配置时只显示英文标题列表。
2. **开启 GitHub Pages**：Settings → Pages → Source 选 **GitHub Actions**。
   - 免费账户的私有仓库不能使用 Pages，需要先把仓库设为 public（Settings → General → Danger Zone → Change visibility）。仓库里只有代码，API Key 保存在 Secrets 中，不会公开。
3. **首次运行**：Actions → *Daily US market news* → Run workflow。完成后访问
   `https://lucas168717.github.io/News/`，收藏这个网址即可。

之后每个交易日自动更新；周末和 NYSE 休市日不会生成新的一天。页面顶部的下拉框可以查看历史交易日。

## 可调整的地方

| 位置 | 内容 |
|---|---|
| `newsbot/config.py` | 板块、RSS 源 / 检索词、归类关键词、行情代码 |
| 仓库变量 `NEWSBOT_MODEL` | 默认 `claude-opus-5-5`，可以换成其他 Claude 模型 |
| `.github/workflows/daily-news.yml` | 运行时间（cron，UTC） |
| `newsbot/trading_calendar.py` | `SPECIAL_CLOSURES`：临时休市日（如国丧日） |

**费用参考**：每天调用 7 次 Claude（6 个板块 + 1 次总结）。按 Opus 5.5 的价格，粗略估计每天几十美分；实际费用取决于当天的新闻量。

## 本地运行

```bash
pip install -r requirements.txt
ANTHROPIC_API_KEY=... python -m newsbot.build --site-dir site
python -m http.server -d site 8000   # 打开 http://localhost:8000
```

`--date YYYY-MM-DD` 用于重新生成指定交易日（RSS 只保留最近几天的新闻，太早的日期抓不到内容），`--force` 用于覆盖已经生成的当天数据。

测试：`pip install pytest && python -m pytest`

> 免责声明：内容由程序自动抓取，摘要由 AI 生成，可能有误，仅供个人参考，不构成投资建议。
